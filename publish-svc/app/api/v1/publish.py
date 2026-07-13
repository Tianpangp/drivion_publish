"""发布域 API：现场结构、制品、设备绑定与审批。"""
from __future__ import annotations

import hashlib
import io
import json
import tarfile
import tomllib
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response as FileResponse
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import Permission, has_permission
from app.core.storage import storage
from app.core.utils import format_datetime, generate_id
from app.models.facility import Equipment, Factory, Line, Station
from app.models.log import OperationLog
from app.models.package import AutoUnitPackage, DriverPackage
from app.models.publish import EquipmentAutoUnitBinding, EquipmentBindingHistory, PublishApproval
from app.models.user import User
from app.schemas.common import Response

router = APIRouter()
MAX_UPLOAD_SIZE = 100 * 1024 * 1024


def _require(user: User, permission: Permission) -> None:
    if not has_permission(getattr(user, "role_code", ""), permission.value):
        raise HTTPException(403, f"无操作权限: {permission.value}")


def _require_any(user: User, *permissions: Permission) -> None:
    if not any(has_permission(getattr(user, "role_code", ""), item.value) for item in permissions):
        raise HTTPException(403, "无操作权限")


def _now() -> datetime:
    return datetime.now()


def _username(user: User) -> str:
    return user.nickname or user.username


def _dt(value: datetime | None) -> str | None:
    return format_datetime(value)


def _log(db: AsyncSession, user: User, operation: str, module: str, description: str, target_id: str = "", target_type: str = "") -> None:
    db.add(OperationLog(
        id=generate_id("log"), operation=operation, module=module,
        operator_id=user.id, operator=_username(user), role=getattr(user, "role_code", ""),
        result="success", time=_now(), description=description, ip="", user_agent="",
        target_id=target_id, target_type=target_type,
    ))


def _archive_text(content: bytes, filename: str, target: str) -> str | None:
    stream = io.BytesIO(content)
    if zipfile.is_zipfile(stream):
        with zipfile.ZipFile(stream) as archive:
            matches = [name for name in archive.namelist() if Path(name).name == target]
            if len(matches) != 1:
                return None
            return archive.read(matches[0]).decode("utf-8")
    try:
        with tarfile.open(fileobj=io.BytesIO(content), mode="r:*") as archive:
            matches = [item for item in archive.getmembers() if item.isfile() and Path(item.name).name == target]
            if len(matches) != 1:
                return None
            extracted = archive.extractfile(matches[0])
            return extracted.read().decode("utf-8") if extracted else None
    except (tarfile.TarError, UnicodeDecodeError):
        return None


def _parse_autounit(content: bytes, filename: str) -> dict[str, Any]:
    text = _archive_text(content, filename, "drivion.project.json")
    if not text:
        raise HTTPException(400, "包内必须且只能包含一个 drivion.project.json")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "drivion.project.json 格式错误") from exc
    required = ("name", "package_id", "version", "module")
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise HTTPException(400, f"drivion.project.json 缺少字段: {', '.join(missing)}")
    return data


def _parse_driver(content: bytes, filename: str) -> dict[str, Any]:
    text = _archive_text(content, filename, "pyproject.toml")
    if not text:
        raise HTTPException(400, "包内必须且只能包含一个 pyproject.toml")
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise HTTPException(400, "pyproject.toml 格式错误") from exc
    project = data.get("project") or {}
    entries = (project.get("entry-points") or {}).get("drivion.hal_drivers") or {}
    if not project.get("name") or not project.get("version"):
        raise HTTPException(400, "pyproject.toml 缺少 project.name 或 project.version")
    if not isinstance(entries, dict) or not entries:
        raise HTTPException(400, "pyproject.toml 缺少 drivion.hal_drivers entry point")
    return {"name": project["name"], "version": project["version"], "entrypoints": list(entries)}


async def _read_upload(file: UploadFile) -> bytes:
    content = await file.read(MAX_UPLOAD_SIZE + 1)
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(413, "上传包不能超过 100MB")
    if not content:
        raise HTTPException(400, "上传文件为空")
    return content


def _hashes(content: bytes) -> tuple[str, str]:
    return hashlib.md5(content).hexdigest(), hashlib.sha256(content).hexdigest()


def _storage_key(kind: str, record_id: str, filename: str) -> str:
    suffixes = "".join(Path(filename).suffixes) or ".bin"
    return f"{kind}/{record_id}/package{suffixes}"


async def _bound_equipment(db: AsyncSession, package_id: str) -> list[dict[str, str]]:
    result = await db.execute(
        select(Equipment).join(EquipmentAutoUnitBinding, EquipmentAutoUnitBinding.equipment_id == Equipment.id)
        .where(EquipmentAutoUnitBinding.package_id == package_id, Equipment.is_deleted == 0)
    )
    return [{"id": item.id, "name": item.name, "code": item.code or ""} for item in result.scalars()]


async def _autounit_json(db: AsyncSession, item: AutoUnitPackage) -> dict[str, Any]:
    return {
        "id": item.id, "name": item.name, "packageId": item.package_id, "fileName": item.file_name,
        "version": item.version, "module": item.module, "size": item.size, "uploadTime": _dt(item.upload_time),
        "uploadUser": item.upload_user_id, "status": item.status, "description": item.description,
        "boundStations": await _bound_equipment(db, item.id), "dependencies": item.dependencies or [],
        "pythonVersion": item.python_version or "", "downloadCount": item.download_count,
        "md5": item.md5, "sha256": item.sha256 or "", "readme": item.readme, "changelog": item.changelog,
        "publishTime": _dt(item.publish_time), "publishUser": item.publish_user_id,
        "deleted": item.deleted, "locked": item.locked, "storageProvider": item.storage_provider,
    }


def _driver_json(item: DriverPackage) -> dict[str, Any]:
    return {
        "id": item.id, "name": item.name, "fileName": item.file_name, "type": item.type,
        "version": item.version, "size": item.size, "uploadTime": _dt(item.upload_time),
        "uploadUser": item.upload_user_id, "status": item.status, "description": item.description,
        "boundStations": [], "protocol": item.protocol, "manufacturer": item.manufacturer,
        "deviceModel": item.device_model, "downloadCount": item.download_count, "md5": item.md5,
        "sha256": item.sha256 or "", "supportedPlatforms": item.supported_platforms or [],
        "apiDocUrl": item.api_doc_url, "readme": item.readme, "publishTime": _dt(item.publish_time),
        "deleted": item.deleted, "locked": item.locked, "storageProvider": item.storage_provider,
    }


def _node(item: Any, type_: str, children: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    data = {
        "id": item.id, "name": item.name, "type": type_, "code": item.code,
        "description": item.description, "status": item.status, "createTime": _dt(item.create_time),
        "updateTime": _dt(item.update_time), "children": children or [],
    }
    for source, target in (("location", "location"), ("ip", "ip"), ("mac", "mac"),
                           ("vendor", "vendor"), ("model", "model"), ("equipment_type", "equipmentType")):
        if hasattr(item, source):
            data[target] = getattr(item, source)
    return data


@router.get("/tree", response_model=Response[list[dict[str, Any]]])
async def tree(search: str | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    _require(user, Permission.FACILITY_FACTORY_VIEW)
    factories = (await db.execute(select(Factory).where(Factory.is_deleted == 0).order_by(Factory.create_time))).scalars().all()
    lines = (await db.execute(select(Line).where(Line.is_deleted == 0).order_by(Line.create_time))).scalars().all()
    stations = (await db.execute(select(Station).where(Station.is_deleted == 0).order_by(Station.create_time))).scalars().all()
    equipment = (await db.execute(select(Equipment).where(Equipment.is_deleted == 0).order_by(Equipment.create_time))).scalars().all()
    equipment_by_station: dict[str, list[Any]] = {}
    station_by_line: dict[str, list[Any]] = {}
    line_by_factory: dict[str, list[Any]] = {}
    for item in equipment: equipment_by_station.setdefault(item.station_id, []).append(item)
    for item in stations: station_by_line.setdefault(item.line_id, []).append(item)
    for item in lines: line_by_factory.setdefault(item.factory_id, []).append(item)
    result = [_node(factory, "factory", [
        _node(line, "line", [_node(station, "station", [_node(eq, "equipment") for eq in equipment_by_station.get(station.id, [])]) for station in station_by_line.get(line.id, [])])
        for line in line_by_factory.get(factory.id, [])
    ]) for factory in factories]
    if search:
        keyword = search.lower()
        def keep(node: dict[str, Any]) -> dict[str, Any] | None:
            children = [child for child in (keep(value) for value in node["children"]) if child]
            if keyword in node["name"].lower() or keyword in (node.get("code") or "").lower() or children:
                return {**node, "children": children}
            return None
        result = [item for item in (keep(value) for value in result) if item]
    return Response(data=result, message="获取成功")


@router.post("/{kind}", response_model=Response[dict[str, Any]])
async def create_node(kind: Literal["factory", "line", "station", "equipment"], payload: dict[str, Any] = Body(...), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    create_permissions = {"factory": Permission.FACILITY_FACTORY_CREATE, "line": Permission.FACILITY_LINE_CREATE,
        "station": Permission.FACILITY_STATION_CREATE, "equipment": Permission.FACILITY_EQUIPMENT_MANAGE}
    _require(user, create_permissions[kind])
    models = {"factory": Factory, "line": Line, "station": Station, "equipment": Equipment}
    parent_fields = {"line": "factory_id", "station": "line_id", "equipment": "station_id"}
    parent_payload = {"line": "factoryId", "station": "lineId", "equipment": "stationId"}
    kwargs = {"id": generate_id(kind), "name": payload["name"], "code": payload.get("code") or None,
              "description": payload.get("description"), "status": payload.get("status", "active"),
              "create_user_id": user.id, "create_time": _now(), "update_time": _now()}
    if kind in parent_fields:
        parent_id = payload[parent_payload[kind]]
        parent_model = {"line": Factory, "station": Line, "equipment": Station}[kind]
        parent = await db.get(parent_model, parent_id)
        if not parent or parent.is_deleted:
            raise HTTPException(404, "上级节点不存在")
        kwargs[parent_fields[kind]] = parent_id
    extras = {"factory": ("location",), "station": ("ip", "mac"), "equipment": ("vendor", "model", "equipment_type")}
    for field in extras.get(kind, ()):
        kwargs[field] = payload.get("equipmentType" if field == "equipment_type" else field)
    item = models[kind](**kwargs)
    db.add(item)
    await db.flush()
    _log(db, user, "create", "现场结构", f"创建{ {'factory':'厂区','line':'线体','station':'工位','equipment':'设备'}[kind] } {item.name}", item.id, kind)
    return Response(data=_node(item, kind))


async def _find_node(db: AsyncSession, node_id: str):
    for kind, model in (("factory", Factory), ("line", Line), ("station", Station), ("equipment", Equipment)):
        item = await db.get(model, node_id)
        if item and not item.is_deleted:
            return kind, item
    raise HTTPException(404, "节点不存在")


@router.put("/nodes/{node_id}", response_model=Response[dict[str, Any]])
async def update_node(node_id: str, payload: dict[str, Any] = Body(...), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    kind, item = await _find_node(db, node_id)
    edit_permissions = {"factory": Permission.FACILITY_FACTORY_EDIT, "line": Permission.FACILITY_LINE_EDIT,
        "station": Permission.FACILITY_STATION_EDIT, "equipment": Permission.FACILITY_EQUIPMENT_MANAGE}
    _require(user, edit_permissions[kind])
    field_map = {"equipmentType": "equipment_type"}
    for field in ("name", "code", "description", "status", "location", "ip", "mac", "vendor", "model", "equipmentType"):
        target = field_map.get(field, field)
        if field in payload and hasattr(item, target): setattr(item, target, payload[field])
    item.update_time = _now()
    _log(db, user, "update", "现场结构", f"更新节点 {item.name}", item.id, kind)
    return Response(data=_node(item, kind))


@router.delete("/nodes/{node_id}", response_model=Response[None])
async def delete_node(node_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    kind, item = await _find_node(db, node_id)
    delete_permissions = {"factory": Permission.FACILITY_FACTORY_DELETE, "line": Permission.FACILITY_LINE_DELETE,
        "station": Permission.FACILITY_STATION_DELETE, "equipment": Permission.FACILITY_EQUIPMENT_MANAGE}
    _require(user, delete_permissions[kind])
    item.is_deleted = 1
    _log(db, user, "delete", "现场结构", f"删除节点 {item.name}", item.id, kind)
    return Response(data=None)


@router.get("/autounit/packages", response_model=Response[dict[str, Any]])
async def autounit_list(page: int = Query(1, ge=1), pageSize: int = Query(20, ge=1, le=100), search: str | None = None, status: str | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    _require(user, Permission.AUTOUNIT_VIEW)
    query = select(AutoUnitPackage)
    if search: query = query.where(or_(AutoUnitPackage.name.like(f"%{search}%"), AutoUnitPackage.package_id.like(f"%{search}%"), AutoUnitPackage.file_name.like(f"%{search}%")))
    if status: query = query.where(AutoUnitPackage.status == status)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    items = (await db.execute(query.order_by(AutoUnitPackage.upload_time.desc()).offset((page - 1) * pageSize).limit(pageSize))).scalars().all()
    return Response(data={"list": [await _autounit_json(db, item) for item in items], "total": total, "page": page, "pageSize": pageSize})


async def _save_autounit(file: UploadFile, db: AsyncSession, user: User, existing: AutoUnitPackage | None = None):
    content = await _read_upload(file)
    meta = _parse_autounit(content, file.filename or "")
    if existing:
        if existing.status != "pending_testing": raise HTTPException(400, "只有待测试版本可以更新")
        if (meta["package_id"], meta["version"]) != (existing.package_id, existing.version): raise HTTPException(400, "更新包的 package_id 和 version 必须与原版本一致")
        item = existing
        await db.execute(delete(PublishApproval).where(PublishApproval.target_id == item.id, PublishApproval.status == "pending"))
    else:
        duplicate = await db.scalar(select(AutoUnitPackage).where(AutoUnitPackage.package_id == meta["package_id"], AutoUnitPackage.version == meta["version"]))
        if duplicate: raise HTTPException(409, f"AutoUnit {meta['package_id']}@{meta['version']} 已存在")
        item = AutoUnitPackage(id=generate_id("au"), package_id=meta["package_id"], version=meta["version"], name=meta["name"], module=meta["module"], file_name=file.filename or "package.zip", size=0, file_path="", status="pending_testing", md5="", upload_user_id=user.id)
        db.add(item)
    key = _storage_key("autounit", item.id, file.filename or item.file_name)
    storage.put(key, content)
    md5, sha256 = _hashes(content)
    item.name, item.module, item.file_name, item.size, item.file_path = meta["name"], meta["module"], file.filename or item.file_name, len(content), key
    item.storage_provider, item.md5, item.sha256 = storage.provider, md5, sha256
    item.dependencies, item.python_version = meta.get("dependencies", []), meta.get("python_version", "")
    item.description, item.readme, item.changelog = meta.get("description"), meta.get("readme"), meta.get("changelog")
    item.upload_user_id, item.upload_time, item.locked = user.id, _now(), False
    await db.flush()
    _log(db, user, "update" if existing else "upload", "AutoUnit包", f"{'更新' if existing else '上传'} AutoUnit {item.package_id}@{item.version}", item.id, "autounit")
    return item


@router.post("/autounit/packages/upload", response_model=Response[dict[str, Any]])
async def upload_autounit(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    _require(user, Permission.AUTOUNIT_MANAGE_DRAFT)
    item = await _save_autounit(file, db, user)
    return Response(data=await _autounit_json(db, item), message="上传成功")


@router.put("/autounit/packages/{package_id}/upload", response_model=Response[dict[str, Any]])
async def replace_autounit(package_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    _require(user, Permission.AUTOUNIT_MANAGE_DRAFT)
    item = await db.get(AutoUnitPackage, package_id)
    if not item: raise HTTPException(404, "AutoUnit 版本不存在")
    item = await _save_autounit(file, db, user, item)
    return Response(data=await _autounit_json(db, item), message="更新成功，原测试审批已取消")


@router.get("/drivers/packages", response_model=Response[dict[str, Any]])
async def driver_list(page: int = Query(1, ge=1), pageSize: int = Query(20, ge=1, le=100), search: str | None = None, status: str | None = None, type: str | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    _require(user, Permission.DRIVER_VIEW)
    query = select(DriverPackage)
    if search: query = query.where(or_(DriverPackage.name.like(f"%{search}%"), DriverPackage.file_name.like(f"%{search}%")))
    if status: query = query.where(DriverPackage.status == status)
    if type: query = query.where(DriverPackage.type == type)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    items = (await db.execute(query.order_by(DriverPackage.upload_time.desc()).offset((page - 1) * pageSize).limit(pageSize))).scalars().all()
    return Response(data={"list": [_driver_json(item) for item in items], "total": total, "page": page, "pageSize": pageSize})


async def _save_driver(file: UploadFile, db: AsyncSession, user: User, existing: DriverPackage | None = None):
    content = await _read_upload(file)
    meta = _parse_driver(content, file.filename or "")
    if existing:
        if existing.status != "pending_testing": raise HTTPException(400, "只有待测试版本可以更新")
        if (meta["name"], meta["version"]) != (existing.name, existing.version): raise HTTPException(400, "更新包的 name 和 version 必须与原版本一致")
        item = existing
        await db.execute(delete(PublishApproval).where(PublishApproval.target_id == item.id, PublishApproval.status == "pending"))
    else:
        duplicate = await db.scalar(select(DriverPackage).where(DriverPackage.name == meta["name"], DriverPackage.version == meta["version"]))
        if duplicate: raise HTTPException(409, f"HAL {meta['name']}@{meta['version']} 已存在")
        item = DriverPackage(id=generate_id("hal"), name=meta["name"], version=meta["version"], type="python", file_name=file.filename or "package.zip", size=0, file_path="", status="pending_testing", md5="", upload_user_id=user.id)
        db.add(item)
    key = _storage_key("hal", item.id, file.filename or item.file_name)
    storage.put(key, content)
    md5, sha256 = _hashes(content)
    item.file_name, item.size, item.file_path = file.filename or item.file_name, len(content), key
    item.storage_provider, item.md5, item.sha256 = storage.provider, md5, sha256
    item.protocol, item.readme = "python-entrypoint", f"entrypoints: {', '.join(meta['entrypoints'])}"
    item.upload_user_id, item.upload_time, item.locked = user.id, _now(), False
    await db.flush()
    _log(db, user, "update" if existing else "upload", "驱动包管理", f"{'更新' if existing else '上传'} HAL {item.name}@{item.version}", item.id, "driver")
    return item


@router.post("/drivers/packages/upload", response_model=Response[dict[str, Any]])
async def upload_driver(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    _require(user, Permission.DRIVER_MANAGE_DRAFT)
    item = await _save_driver(file, db, user)
    return Response(data=_driver_json(item), message="上传成功")


@router.put("/drivers/packages/{package_id}/upload", response_model=Response[dict[str, Any]])
async def replace_driver(package_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    _require(user, Permission.DRIVER_MANAGE_DRAFT)
    item = await db.get(DriverPackage, package_id)
    if not item: raise HTTPException(404, "HAL 版本不存在")
    item = await _save_driver(file, db, user, item)
    return Response(data=_driver_json(item), message="更新成功，原测试审批已取消")


async def _package(db: AsyncSession, kind: str, package_id: str):
    model = AutoUnitPackage if kind == "autounit" else DriverPackage
    item = await db.get(model, package_id)
    if not item: raise HTTPException(404, "包版本不存在")
    return item


def _package_label(kind: str, item: Any) -> str:
    return f"{item.package_id if kind == 'autounit' else item.name}@{item.version}"


async def _pending_approval(db: AsyncSession, target_id: str) -> PublishApproval | None:
    return await db.scalar(select(PublishApproval).where(PublishApproval.target_id == target_id, PublishApproval.status == "pending"))


async def _submit(db: AsyncSession, user: User, kind: str, item: Any, action: str, approve_status: str, reject_status: str):
    if await _pending_approval(db, item.id): raise HTTPException(409, "该版本已有待审批申请")
    approval = PublishApproval(id=generate_id("approval"), target_id=item.id, target_kind=kind,
        artifact_type="AutoUnit" if kind == "autounit" else "HAL", action=action,
        approve_status=approve_status, reject_status=reject_status, applicant_id=user.id,
        applicant=_username(user), submitted_at=_now(), status="pending")
    db.add(approval)
    _log(db, user, "submit", "审批管理", f"{action}审批 {_package_label(kind, item)}", item.id, kind)


@router.post("/{kind}/packages/{package_id}/submit-testing", response_model=Response[dict[str, Any]])
async def submit_testing(kind: Literal["autounit", "drivers"], package_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    domain = "autounit" if kind == "autounit" else "driver"
    _require(user, Permission.AUTOUNIT_SUBMIT_TEST if domain == "autounit" else Permission.DRIVER_SUBMIT_TEST)
    item = await _package(db, domain, package_id)
    if item.status != "pending_testing": raise HTTPException(400, "只有待测试版本可以提交测试")
    await _submit(db, user, domain, item, "提交测试", "testing", "pending_testing")
    return Response(data=await _autounit_json(db, item) if domain == "autounit" else _driver_json(item), message="已提交测试审批")


@router.post("/{kind}/packages/{package_id}/submit-publish", response_model=Response[dict[str, Any]])
async def submit_publish(kind: Literal["autounit", "drivers"], package_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    domain = "autounit" if kind == "autounit" else "driver"
    _require(user, Permission.AUTOUNIT_SUBMIT_PUBLISH if domain == "autounit" else Permission.DRIVER_SUBMIT_PUBLISH)
    item = await _package(db, domain, package_id)
    if item.status not in {"testing", "removed"}: raise HTTPException(400, "只有已测试或已下架版本可以提交发布")
    previous = item.status
    item.status = "pending_publish"
    await _submit(db, user, domain, item, "重新上架" if previous == "removed" else "提交发布", "published", previous)
    return Response(data=await _autounit_json(db, item) if domain == "autounit" else _driver_json(item), message="已提交发布审批")


@router.post("/{kind}/packages/{package_id}/submit-remove", response_model=Response[dict[str, Any]])
async def submit_remove(kind: Literal["autounit", "drivers"], package_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    domain = "autounit" if kind == "autounit" else "driver"
    _require(user, Permission.AUTOUNIT_SUBMIT_REMOVE if domain == "autounit" else Permission.DRIVER_SUBMIT_REMOVE)
    item = await _package(db, domain, package_id)
    if item.status != "published": raise HTTPException(400, "只有已发布版本可以申请下架")
    if domain == "autounit" and await db.scalar(select(func.count()).select_from(EquipmentAutoUnitBinding).where(EquipmentAutoUnitBinding.package_id == item.id)):
        raise HTTPException(409, "该 AutoUnit 仍被设备绑定，不能下架")
    item.status = "pending_remove"
    await _submit(db, user, domain, item, "申请下架", "removed", "published")
    return Response(data=await _autounit_json(db, item) if domain == "autounit" else _driver_json(item), message="已提交下架审批")


@router.post("/{kind}/packages/{package_id}/reject", response_model=Response[None])
async def active_reject(kind: Literal["autounit", "drivers"], package_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    domain = "autounit" if kind == "autounit" else "driver"
    _require(user, Permission.AUTOUNIT_MANAGE_DRAFT if domain == "autounit" else Permission.DRIVER_MANAGE_DRAFT)
    item = await _package(db, domain, package_id)
    if item.status in {"published", "removed", "pending_remove"}: raise HTTPException(400, "已发布版本只能申请下架")
    item.status, item.locked = "pending_testing", False
    await db.execute(delete(PublishApproval).where(PublishApproval.target_id == item.id, PublishApproval.status == "pending"))
    _log(db, user, "reject", "AutoUnit包" if domain == "autounit" else "驱动包管理", f"退回待测试 {_package_label(domain, item)}", item.id, domain)
    return Response(data=None, message="已退回待测试")


@router.delete("/{kind}/packages/{package_id}", response_model=Response[None])
async def delete_package(kind: Literal["autounit", "drivers"], package_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    domain = "autounit" if kind == "autounit" else "driver"
    _require(user, Permission.AUTOUNIT_MANAGE_DRAFT if domain == "autounit" else Permission.DRIVER_MANAGE_DRAFT)
    item = await _package(db, domain, package_id)
    if item.status != "pending_testing": raise HTTPException(400, "只有待测试版本可以直接删除")
    if domain == "autounit" and await db.scalar(select(func.count()).select_from(EquipmentAutoUnitBinding).where(EquipmentAutoUnitBinding.package_id == item.id)):
        raise HTTPException(409, "该 AutoUnit 已被设备绑定，不能删除")
    label, path = _package_label(domain, item), item.file_path
    await db.execute(delete(PublishApproval).where(PublishApproval.target_id == item.id))
    await db.delete(item)
    storage.delete(path)
    _log(db, user, "delete", "AutoUnit包" if domain == "autounit" else "驱动包管理", f"删除待测试版本 {label}", package_id, domain)
    return Response(data=None, message="已删除")


@router.get("/{kind}/packages/{package_id}/download")
async def download_package(kind: Literal["autounit", "drivers"], package_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    domain = "autounit" if kind == "autounit" else "driver"
    _require(user, Permission.AUTOUNIT_DOWNLOAD if domain == "autounit" else Permission.DRIVER_DOWNLOAD)
    item = await _package(db, domain, package_id)
    if item.deleted: raise HTTPException(410, "该版本已下架")
    try: content = storage.get(item.file_path)
    except FileNotFoundError as exc: raise HTTPException(404, "制品文件不存在") from exc
    item.download_count += 1
    return FileResponse(content=content, media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="{item.file_name}"'})


@router.get("/{kind}/packages/{package_id}", response_model=Response[dict[str, Any]])
async def package_detail(kind: Literal["autounit", "drivers"], package_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    domain = "autounit" if kind == "autounit" else "driver"
    _require(user, Permission.AUTOUNIT_VIEW if domain == "autounit" else Permission.DRIVER_VIEW)
    item = await _package(db, domain, package_id)
    return Response(data=await _autounit_json(db, item) if domain == "autounit" else _driver_json(item))


@router.get("/equipment", response_model=Response[list[dict[str, Any]]])
async def equipment_list(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    _require(user, Permission.FACILITY_EQUIPMENT_VIEW)
    rows = (await db.execute(
        select(Equipment, Station, Line, Factory)
        .select_from(Equipment)
        .join(Station, Equipment.station_id == Station.id)
        .join(Line, Station.line_id == Line.id)
        .join(Factory, Line.factory_id == Factory.id)
        .where(Equipment.is_deleted == 0)
    )).all()
    result = []
    for equipment, station, line, factory in rows:
        binding = await db.scalar(select(EquipmentAutoUnitBinding).where(EquipmentAutoUnitBinding.equipment_id == equipment.id))
        package = await db.get(AutoUnitPackage, binding.package_id) if binding else None
        history = (await db.execute(select(EquipmentBindingHistory).where(EquipmentBindingHistory.equipment_id == equipment.id).order_by(EquipmentBindingHistory.operation_time.desc()).limit(20))).scalars().all()
        result.append({"id": equipment.id, "name": equipment.name, "code": equipment.code or "", "path": f"{factory.name} / {line.name} / {station.name}",
            "type": equipment.equipment_type or "", "vendor": equipment.vendor or "", "model": equipment.model or "", "enabled": equipment.status == "active",
            "binding": ({"id": package.id, "name": package.name, "packageId": package.package_id, "version": package.version, "module": package.module, "status": package.status, "boundAt": _dt(binding.bind_time)} if package else None),
            "history": [{"operation": h.operation, "name": h.package_name or "", "version": h.package_version or "", "time": _dt(h.operation_time)} for h in history]})
    return Response(data=result)


@router.post("/equipment/{equipment_id}/autounit-binding", response_model=Response[dict[str, Any]])
async def bind_equipment(equipment_id: str, payload: dict[str, str] = Body(...), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    _require(user, Permission.BINDING_AUTOUNIT_MANAGE)
    equipment = await db.get(Equipment, equipment_id)
    package = await db.get(AutoUnitPackage, payload.get("packageVersionId"))
    if not equipment or equipment.is_deleted: raise HTTPException(404, "设备不存在")
    if not package or package.deleted: raise HTTPException(404, "AutoUnit 版本不存在或已下架")
    binding = await db.scalar(select(EquipmentAutoUnitBinding).where(EquipmentAutoUnitBinding.equipment_id == equipment_id))
    if binding: binding.package_id, binding.bind_user_id, binding.bind_time = package.id, user.id, _now()
    else:
        binding = EquipmentAutoUnitBinding(id=generate_id("binding"), equipment_id=equipment_id, package_id=package.id, bind_user_id=user.id, bind_time=_now())
        db.add(binding)
    db.add(EquipmentBindingHistory(id=generate_id("history"), equipment_id=equipment_id, package_id=package.id, package_name=package.name, package_version=package.version, operation="bind", operator_id=user.id, operation_time=_now()))
    _log(db, user, "bind", "设备绑定", f"设备 {equipment.name} 绑定 {_package_label('autounit', package)}", equipment.id, "equipment")
    return Response(data={"id": package.id, "name": package.name, "packageId": package.package_id, "version": package.version, "module": package.module, "status": package.status, "boundAt": _dt(binding.bind_time)})


@router.delete("/equipment/{equipment_id}/autounit-binding", response_model=Response[None])
async def unbind_equipment(equipment_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    _require(user, Permission.BINDING_AUTOUNIT_MANAGE)
    binding = await db.scalar(select(EquipmentAutoUnitBinding).where(EquipmentAutoUnitBinding.equipment_id == equipment_id))
    if not binding: raise HTTPException(404, "设备未绑定 AutoUnit")
    package = await db.get(AutoUnitPackage, binding.package_id)
    await db.delete(binding)
    db.add(EquipmentBindingHistory(id=generate_id("history"), equipment_id=equipment_id, package_id=package.id if package else None, package_name=package.name if package else None, package_version=package.version if package else None, operation="unbind", operator_id=user.id, operation_time=_now()))
    _log(db, user, "unbind", "设备绑定", f"设备 {equipment_id} 解绑 AutoUnit", equipment_id, "equipment")
    return Response(data=None)


def _approval_json(item: PublishApproval, package: Any) -> dict[str, Any]:
    return {"id": item.id, "type": item.artifact_type, "name": package.name, "packageId": package.package_id if item.target_kind == "autounit" else package.name,
        "version": package.version, "action": item.action, "applicant": item.applicant, "submittedAt": _dt(item.submitted_at), "status": "待审批"}


@router.get("/approvals", response_model=Response[list[dict[str, Any]]])
async def approvals(type: str | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    _require_any(user, Permission.APPROVAL_TEST_VIEW, Permission.APPROVAL_RELEASE_VIEW)
    query = select(PublishApproval).where(PublishApproval.status == "pending").order_by(PublishApproval.submitted_at.desc())
    role_code = getattr(user, "role_code", "")
    can_test = has_permission(role_code, Permission.APPROVAL_TEST_VIEW.value)
    can_release = has_permission(role_code, Permission.APPROVAL_RELEASE_VIEW.value)
    if can_test and not can_release:
        query = query.where(PublishApproval.action == "提交测试")
    elif can_release and not can_test:
        query = query.where(PublishApproval.action != "提交测试")
    if type and type != "全部": query = query.where(PublishApproval.artifact_type == type)
    items = (await db.execute(query)).scalars().all()
    result = []
    for item in items:
        package = await _package(db, item.target_kind, item.target_id)
        result.append(_approval_json(item, package))
    return Response(data=result)


@router.post("/approvals/{approval_id}/{decision}", response_model=Response[None])
async def review_approval(approval_id: str, decision: Literal["approve", "reject"], db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    approval = await db.get(PublishApproval, approval_id)
    if not approval or approval.status != "pending": raise HTTPException(404, "待审批记录不存在")
    _require(user, Permission.APPROVAL_TEST_REVIEW if approval.action == "提交测试" else Permission.APPROVAL_RELEASE_REVIEW)
    item = await _package(db, approval.target_kind, approval.target_id)
    item.status = approval.approve_status if decision == "approve" else approval.reject_status
    if decision == "approve" and approval.action == "提交测试": item.locked = True
    if item.status == "pending_testing": item.locked = False
    if item.status == "published": item.deleted, item.publish_user_id, item.publish_time = 0, user.id, _now()
    if item.status == "removed": item.deleted = 1
    approval.status, approval.reviewer_id, approval.reviewed_at = "approved" if decision == "approve" else "rejected", user.id, _now()
    _log(db, user, "approve" if decision == "approve" else "reject", "审批管理", f"{'通过' if decision == 'approve' else '驳回'}{approval.action} {_package_label(approval.target_kind, item)}", item.id, approval.target_kind)
    return Response(data=None, message="审批通过" if decision == "approve" else "已驳回并回退")
