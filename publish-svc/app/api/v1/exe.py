"""
Exe 端拉取接口

MVP 目标：按工位聚合当前部署所需的清单、AutoUnit 包、驱动包和界面包，
让工控机不需要理解管理端的多张表关系。
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.utils import format_datetime
from app.models.binding import (
    AutoUnitStationApplication,
    InterfaceStationBinding,
    ManifestStationBinding,
)
from app.models.deployment import DeploymentManifest
from app.models.facility import Factory, Line, Station
from app.models.interface import Interface
from app.models.package import AutoUnitPackage, DriverPackage
from app.schemas.common import Response
from app.schemas.exe import (
    ExeArtifactInfo,
    ExeBundleResponse,
    ExeDeploymentManifestInfo,
    ExeStationInfo,
)

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None


router = APIRouter()


@router.get(
    "/stations/{station_id}/bundle",
    response_model=Response[ExeBundleResponse],
    summary="按工位获取 Exe 部署包",
)
async def get_station_bundle(
    station_id: str,
):
    """返回工控机启动/同步所需的当前部署聚合视图。"""
    async with AsyncSessionLocal() as db:
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
        generatedAt=datetime.utcnow().isoformat(),
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
