"""Exe Runtime pull APIs, DevKit artifact submission, and legacy station bundle."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response as FileResponse
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, get_db
from app.core.integration_auth import (
    IntegrationPrincipal,
    get_integration_principal,
    require_fresh_integration_permission,
    require_integration_permission,
)
from app.core.storage import storage
from app.core.utils import format_datetime
from app.models.binding import (
    AutoUnitStationApplication,
    InterfaceStationBinding,
    ManifestStationBinding,
)
from app.models.deployment import DeploymentManifest
from app.models.facility import Equipment, Factory, Line, Station
from app.models.interface import Interface
from app.models.package import AutoUnitPackage, DriverPackage
from app.models.publish import EquipmentAutoUnitBinding
from app.schemas.common import Response
from app.schemas.exe import (
    ExeArtifactInfo,
    ExeAutoUnitInfo,
    ExeBundleResponse,
    ExeDeploymentManifestInfo,
    ExeEquipmentDeployment,
    ExeEquipmentInfo,
    ExeStationInfo,
)

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None


router = APIRouter()


async def _equipment_context(
    equipment_id: str, db: AsyncSession
) -> tuple[Equipment, Station, Line, Factory]:
    row = (await db.execute(
        select(Equipment, Station, Line, Factory)
        .join(Station, Equipment.station_id == Station.id)
        .join(Line, Station.line_id == Line.id)
        .join(Factory, Line.factory_id == Factory.id)
        .where(
            Equipment.id == equipment_id,
            Equipment.is_deleted == 0,
            Station.is_deleted == 0,
            Line.is_deleted == 0,
            Factory.is_deleted == 0,
        )
    )).first()
    if not row:
        raise HTTPException(404, "设备不存在或现场结构已删除")
    return row


def _equipment_resources(
    equipment: Equipment, station: Station, line: Line, site: Factory
) -> list[tuple[str, str]]:
    return [
        ("equipment", equipment.id),
        ("station", station.id),
        ("line", line.id),
        ("site", site.id),
    ]


def _equipment_info(
    equipment: Equipment, station: Station, line: Line, site: Factory
) -> ExeEquipmentInfo:
    return ExeEquipmentInfo(
        id=equipment.id,
        name=equipment.name,
        code=equipment.code,
        status=equipment.status,
        equipmentType=equipment.equipment_type,
        vendor=equipment.vendor,
        model=equipment.model,
        station={"id": station.id, "name": station.name, "code": station.code},
        line={"id": line.id, "name": line.name, "code": line.code},
        site={"id": site.id, "name": site.name, "code": site.code},
    )


def _external_artifact(item: AutoUnitPackage | DriverPackage, download_path: str) -> ExeArtifactInfo:
    metadata: dict[str, Any] = {
        "description": item.description,
        "publishTime": format_datetime(item.publish_time),
        "storageProvider": item.storage_provider,
    }
    if isinstance(item, AutoUnitPackage):
        metadata.update({
            "packageId": item.package_id,
            "module": item.module,
            "pythonVersion": item.python_version,
            "dependencies": item.dependencies or [],
        })
    else:
        metadata.update({
            "type": item.type,
            "protocol": item.protocol,
            "manufacturer": item.manufacturer,
            "deviceModel": item.device_model,
            "supportedPlatforms": item.supported_platforms or [],
        })
    return ExeArtifactInfo(
        id=item.id,
        name=item.name,
        version=item.version,
        fileName=item.file_name,
        size=item.size,
        md5=item.md5,
        sha256=item.sha256,
        status=item.status,
        downloadApiPath=download_path,
        metadata=metadata,
    )


def _bound_autounit_info(item: AutoUnitPackage, equipment_id: str) -> ExeAutoUnitInfo:
    warning = None if item.status == "published" else f"当前绑定版本状态为 {item.status}，并非已发布版本"
    return ExeAutoUnitInfo(
        id=item.id,
        name=item.name,
        packageId=item.package_id,
        module=item.module,
        version=item.version,
        fileName=item.file_name,
        size=item.size,
        md5=item.md5,
        sha256=item.sha256,
        status=item.status,
        published=item.status == "published",
        releaseWarning=warning,
        downloadApiPath=f"/publish/api/v1/exe/equipment/{equipment_id}/autounit/download",
        metadata={
            "description": item.description,
            "pythonVersion": item.python_version,
            "dependencies": item.dependencies or [],
            "publishTime": format_datetime(item.publish_time),
        },
    )


async def _bound_autounit(
    equipment_id: str, db: AsyncSession
) -> tuple[EquipmentAutoUnitBinding | None, AutoUnitPackage | None]:
    binding = await db.scalar(
        select(EquipmentAutoUnitBinding).where(
            EquipmentAutoUnitBinding.equipment_id == equipment_id
        )
    )
    if not binding:
        return None, None
    package = await db.get(AutoUnitPackage, binding.package_id)
    if not package or package.deleted:
        raise HTTPException(409, "设备绑定指向已删除或已下架的 AutoUnit 版本")
    return binding, package


def _revision(binding: EquipmentAutoUnitBinding | None, package: AutoUnitPackage | None) -> str:
    raw = "unbound" if not binding or not package else ":".join([
        binding.id,
        binding.bind_time.isoformat(),
        package.id,
        package.sha256 or package.md5,
        package.status,
    ])
    return hashlib.sha256(raw.encode()).hexdigest()


def _artifact_file(item: AutoUnitPackage | DriverPackage, content: bytes) -> FileResponse:
    filename = quote(item.file_name, safe="")
    return FileResponse(
        content=content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
            "ETag": f'"{item.sha256 or item.md5}"',
            "X-Artifact-SHA256": item.sha256 or "",
            "X-Artifact-MD5": item.md5,
        },
    )


@router.get(
    "/equipment/{equipment_id}/deployment",
    response_model=Response[ExeEquipmentDeployment],
    summary="获取设备当前 AutoUnit 绑定",
)
async def get_equipment_deployment(
    equipment_id: str,
    db: AsyncSession = Depends(get_db),
    principal: IntegrationPrincipal = Depends(get_integration_principal),
):
    equipment, station, line, site = await _equipment_context(equipment_id, db)
    require_integration_permission(
        principal,
        "platform.equipment.read",
        _equipment_resources(equipment, station, line, site),
    )
    binding, package = await _bound_autounit(equipment_id, db)
    return Response(
        data=ExeEquipmentDeployment(
            equipment=_equipment_info(equipment, station, line, site),
            autoUnit=_bound_autounit_info(package, equipment_id) if package else None,
            boundAt=format_datetime(binding.bind_time) if binding else None,
            revision=_revision(binding, package),
            generatedAt=datetime.now(timezone.utc).isoformat(),
        ),
        message="获取成功",
    )


@router.get(
    "/equipment/{equipment_id}/autounit/download",
    summary="下载设备当前绑定的 AutoUnit",
)
async def download_equipment_autounit(
    equipment_id: str,
    db: AsyncSession = Depends(get_db),
    principal: IntegrationPrincipal = Depends(get_integration_principal),
):
    equipment, station, line, site = await _equipment_context(equipment_id, db)
    resources = _equipment_resources(equipment, station, line, site)
    require_integration_permission(principal, "platform.equipment.read", resources)
    require_integration_permission(principal, "artifact.package.download", resources)
    _, package = await _bound_autounit(equipment_id, db)
    if not package:
        raise HTTPException(404, "设备未绑定 AutoUnit")
    try:
        content = storage.get(package.file_path)
    except FileNotFoundError as exc:
        raise HTTPException(404, "AutoUnit 制品文件不存在") from exc
    package.download_count += 1
    return _artifact_file(package, content)


async def _hal_version(name: str, version: str, db: AsyncSession) -> DriverPackage:
    package = await db.scalar(
        select(DriverPackage).where(
            DriverPackage.name == name,
            DriverPackage.version == version,
            DriverPackage.deleted == 0,
        )
    )
    if not package:
        raise HTTPException(404, f"HAL {name}@{version} 不存在或已下架")
    return package


@router.get(
    "/equipment/{equipment_id}/hal",
    response_model=Response[ExeArtifactInfo],
    summary="按名称和版本解析 HAL",
)
async def resolve_hal(
    equipment_id: str,
    name: str = Query(..., min_length=1),
    version: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    principal: IntegrationPrincipal = Depends(get_integration_principal),
):
    equipment, station, line, site = await _equipment_context(equipment_id, db)
    resources = _equipment_resources(equipment, station, line, site)
    require_integration_permission(principal, "platform.equipment.read", resources)
    require_integration_permission(principal, "artifact.package.read", resources)
    package = await _hal_version(name, version, db)
    path = (
        f"/publish/api/v1/exe/equipment/{equipment_id}/hal/download"
        f"?name={quote(name, safe='')}&version={quote(version, safe='')}"
    )
    return Response(data=_external_artifact(package, path), message="获取成功")


@router.get(
    "/equipment/{equipment_id}/hal/download",
    summary="按名称和版本下载 HAL",
)
async def download_hal(
    equipment_id: str,
    name: str = Query(..., min_length=1),
    version: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    principal: IntegrationPrincipal = Depends(get_integration_principal),
):
    equipment, station, line, site = await _equipment_context(equipment_id, db)
    resources = _equipment_resources(equipment, station, line, site)
    require_integration_permission(principal, "platform.equipment.read", resources)
    require_integration_permission(principal, "artifact.package.download", resources)
    package = await _hal_version(name, version, db)
    try:
        content = storage.get(package.file_path)
    except FileNotFoundError as exc:
        raise HTTPException(404, "HAL 制品文件不存在") from exc
    package.download_count += 1
    return _artifact_file(package, content)


@router.post(
    "/artifacts/autounit",
    response_model=Response[dict[str, Any]],
    summary="DevKit 提交 AutoUnit 制品",
)
async def submit_autounit_artifact(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    principal: IntegrationPrincipal = Depends(get_integration_principal),
):
    await require_fresh_integration_permission(principal, "autounit.definition.publish")
    from app.api.v1.publish import _autounit_json, _save_autounit

    item = await _save_autounit(file, db, principal)  # type: ignore[arg-type]
    return Response(data=await _autounit_json(db, item), message="提交成功，当前状态为待测试")


@router.put(
    "/artifacts/autounit/{artifact_id}",
    response_model=Response[dict[str, Any]],
    summary="DevKit 更新待测试 AutoUnit 制品",
)
async def replace_autounit_artifact(
    artifact_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    principal: IntegrationPrincipal = Depends(get_integration_principal),
):
    await require_fresh_integration_permission(principal, "autounit.definition.publish")
    from app.api.v1.publish import _autounit_json, _save_autounit

    existing = await db.get(AutoUnitPackage, artifact_id)
    if not existing:
        raise HTTPException(404, "AutoUnit 版本不存在")
    item = await _save_autounit(file, db, principal, existing)  # type: ignore[arg-type]
    return Response(data=await _autounit_json(db, item), message="更新成功，原测试审批已取消")


@router.post(
    "/artifacts/hal",
    response_model=Response[dict[str, Any]],
    summary="DevKit 提交 HAL 制品",
)
async def submit_hal_artifact(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    principal: IntegrationPrincipal = Depends(get_integration_principal),
):
    await require_fresh_integration_permission(principal, "hal.driver.publish")
    from app.api.v1.publish import _driver_json, _save_driver

    item = await _save_driver(file, db, principal)  # type: ignore[arg-type]
    return Response(data=_driver_json(item), message="提交成功，当前状态为待测试")


@router.put(
    "/artifacts/hal/{artifact_id}",
    response_model=Response[dict[str, Any]],
    summary="DevKit 更新待测试 HAL 制品",
)
async def replace_hal_artifact(
    artifact_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    principal: IntegrationPrincipal = Depends(get_integration_principal),
):
    await require_fresh_integration_permission(principal, "hal.driver.publish")
    from app.api.v1.publish import _driver_json, _save_driver

    existing = await db.get(DriverPackage, artifact_id)
    if not existing:
        raise HTTPException(404, "HAL 版本不存在")
    item = await _save_driver(file, db, principal, existing)  # type: ignore[arg-type]
    return Response(data=_driver_json(item), message="更新成功，原测试审批已取消")


@router.get(
    "/stations/{station_id}/bundle",
    response_model=Response[ExeBundleResponse],
    summary="按工位获取 Exe 部署包",
    deprecated=True,
)
async def get_station_bundle(
    station_id: str,
    principal: IntegrationPrincipal = Depends(get_integration_principal),
):
    """旧工位模型兼容接口；新 Exe 必须使用 equipment deployment 接口。"""
    async with AsyncSessionLocal() as db:
        row = (await db.execute(
            select(Station, Line, Factory)
            .join(Line, Station.line_id == Line.id)
            .join(Factory, Line.factory_id == Factory.id)
            .where(
                Station.id == station_id,
                Station.is_deleted == 0,
                Line.is_deleted == 0,
                Factory.is_deleted == 0,
            )
        )).first()
        if not row:
            raise HTTPException(404, "工位不存在或已删除")
        station, line, site = row
        require_integration_permission(
            principal,
            "platform.station.read",
            [("station", station.id), ("line", line.id), ("site", site.id)],
        )
        return Response(
            code=200,
            message="获取成功",
            data=await _build_db_bundle(station_id, db),
        )


async def _build_db_bundle(station_id: str, db: AsyncSession) -> ExeBundleResponse:
    station_info = await _get_station_info(station_id, db)
    if not station_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工位不存在或已删除",
        )

    warnings: list[str] = []
    manifest = await _get_latest_manifest(station_id, db)
    auto_units = await _get_applied_autounits(station_id, db)
    interfaces = await _get_bound_interfaces(station_id, db)

    driver_names: list[str] = []
    if manifest and manifest.content:
        driver_names, parse_warnings = _extract_driver_names(manifest.content)
        warnings.extend(parse_warnings)
    else:
        warnings.append("工位未绑定部署清单，无法从清单解析驱动依赖")

    drivers = await _get_manifest_drivers(driver_names, db)
    if not driver_names:
        warnings.append("清单未声明 drivers，暂不返回驱动包")
    elif len(drivers) < len(set(driver_names)):
        found = {driver.name for driver in drivers}
        missing = sorted(set(driver_names) - found)
        warnings.append(f"部分驱动未找到或未发布: {', '.join(missing)}")

    bundle = ExeBundleResponse(
        station=station_info,
        manifest=_manifest_artifact(manifest) if manifest else None,
        autoUnits=[_autounit_artifact(item) for item in auto_units],
        drivers=[_driver_artifact(item) for item in drivers],
        interfaces=[_interface_artifact(item) for item in interfaces],
        generatedAt=datetime.now(timezone.utc).isoformat(),
        warnings=warnings,
    )

    return bundle


async def _get_station_info(station_id: str, db: AsyncSession) -> ExeStationInfo | None:
    result = await db.execute(
        select(Station, Line, Factory)
        .join(Line, Station.line_id == Line.id)
        .join(Factory, Line.factory_id == Factory.id)
        .where(
            and_(
                Station.id == station_id,
                Station.is_deleted == 0,
                Line.is_deleted == 0,
                Factory.is_deleted == 0,
            )
        )
    )
    row = result.first()
    if not row:
        return None

    station, line, factory = row
    return ExeStationInfo(
        id=station.id,
        name=station.name,
        code=station.code,
        path=f"{factory.name} / {line.name} / {station.name}",
        ip=station.ip,
        mac=station.mac,
    )


async def _get_latest_manifest(station_id: str, db: AsyncSession) -> DeploymentManifest | None:
    result = await db.execute(
        select(DeploymentManifest)
        .join(ManifestStationBinding, DeploymentManifest.id == ManifestStationBinding.manifest_id)
        .where(ManifestStationBinding.station_id == station_id)
        .order_by(ManifestStationBinding.bind_time.desc(), DeploymentManifest.upload_time.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _get_applied_autounits(station_id: str, db: AsyncSession) -> list[AutoUnitPackage]:
    result = await db.execute(
        select(AutoUnitPackage)
        .join(AutoUnitStationApplication, AutoUnitPackage.id == AutoUnitStationApplication.package_id)
        .where(
            and_(
                AutoUnitStationApplication.station_id == station_id,
                AutoUnitPackage.status == "published",
            )
        )
        .order_by(AutoUnitStationApplication.apply_time.desc())
    )
    return list(result.scalars().all())


async def _get_bound_interfaces(station_id: str, db: AsyncSession) -> list[Interface]:
    result = await db.execute(
        select(Interface)
        .join(InterfaceStationBinding, Interface.id == InterfaceStationBinding.interface_id)
        .where(
            and_(
                InterfaceStationBinding.station_id == station_id,
                Interface.is_deleted == False,  # noqa: E712
            )
        )
        .order_by(InterfaceStationBinding.bind_time.desc())
    )
    return list(result.scalars().all())


async def _get_manifest_drivers(driver_names: list[str], db: AsyncSession) -> list[DriverPackage]:
    if not driver_names:
        return []

    result = await db.execute(
        select(DriverPackage)
        .where(
            and_(
                DriverPackage.name.in_(sorted(set(driver_names))),
                DriverPackage.status == "published",
            )
        )
        .order_by(DriverPackage.publish_time.desc(), DriverPackage.upload_time.desc())
    )
    return list(result.scalars().all())


def _extract_driver_names(content: str) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    parsed: dict[str, Any] = {}

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        if tomllib is None:
            warnings.append("当前 Python 不支持 TOML 解析，无法读取 drivers")
            return [], warnings
        try:
            parsed = tomllib.loads(content)
        except Exception as exc:
            warnings.append(f"清单解析失败: {exc}")
            return [], warnings

    raw_drivers = parsed.get("drivers", [])
    if not raw_drivers and isinstance(parsed.get("manifest"), dict):
        raw_drivers = parsed["manifest"].get("drivers", [])
    if isinstance(raw_drivers, dict):
        raw_drivers = raw_drivers.get("items", raw_drivers.get("packages", []))

    names: list[str] = []
    for item in raw_drivers:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict) and item.get("name"):
            names.append(str(item["name"]))
    return names, warnings


def _manifest_artifact(manifest: DeploymentManifest) -> ExeDeploymentManifestInfo:
    return ExeDeploymentManifestInfo(
        id=manifest.id,
        name=manifest.name,
        version=manifest.version,
        fileName=manifest.file_name,
        size=manifest.size,
        md5=manifest.md5,
        status="published",
        downloadApiPath=f"/publish/api/v1/deployment/manifests/{manifest.id}/download",
        content=manifest.content,
        metadata={
            "description": manifest.description,
            "uploadTime": format_datetime(manifest.upload_time),
        },
    )


def _autounit_artifact(package: AutoUnitPackage) -> ExeArtifactInfo:
    return ExeArtifactInfo(
        id=package.id,
        name=package.name,
        version=package.version,
        fileName=package.file_name,
        size=package.size,
        md5=package.md5,
        sha256=package.sha256,
        status=package.status,
        downloadApiPath=f"/publish/api/v1/autounit/packages/{package.id}/download",
        metadata={
            "description": package.description,
            "pythonVersion": package.python_version,
            "dependencies": package.dependencies or [],
            "publishTime": format_datetime(package.publish_time),
        },
    )


def _driver_artifact(package: DriverPackage) -> ExeArtifactInfo:
    return ExeArtifactInfo(
        id=package.id,
        name=package.name,
        version=package.version,
        fileName=package.file_name,
        size=package.size,
        md5=package.md5,
        sha256=package.sha256,
        status=package.status,
        downloadApiPath=f"/publish/api/v1/drivers/packages/{package.id}/download",
        metadata={
            "type": package.type,
            "protocol": package.protocol,
            "manufacturer": package.manufacturer,
            "deviceModel": package.device_model,
            "supportedPlatforms": package.supported_platforms or [],
            "publishTime": format_datetime(package.publish_time),
        },
    )


def _interface_artifact(interface: Interface) -> ExeArtifactInfo:
    return ExeArtifactInfo(
        id=interface.id,
        name=interface.name,
        fileName=None,
        size=interface.file_size,
        md5=interface.file_md5,
        status="published",
        downloadApiPath=f"/publish/api/v1/interfaces/{interface.id}/download",
        metadata={
            "description": interface.description,
            "thumbnail": interface.thumbnail,
            "updateTime": format_datetime(interface.update_time),
        },
    )
