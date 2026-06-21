"""
工位绑定管理 API
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from app.core.database import get_db
from app.core.deps import get_current_user, require_permissions
from app.core.permissions import Permission
from app.core.utils import generate_id, format_datetime
from app.models.user import User
from app.models.interface import Interface
from app.models.facility import Station, Line, Factory
from app.models.binding import InterfaceStationBinding, AutoUnitStationApplication, ManifestStationBinding
from app.models.package import AutoUnitPackage
from app.models.deployment import DeploymentManifest
from app.schemas.common import Response
from app.schemas.binding import InterfaceBindRequest, InterfaceBindResponse, StationBindingsResponse

router = APIRouter()


async def _get_station_path(station_id: str, db: AsyncSession) -> str:
    """获取工位完整路径"""
    result = await db.execute(
        select(Station, Line, Factory)
        .join(Line, Station.line_id == Line.id)
        .join(Factory, Line.factory_id == Factory.id)
        .where(Station.id == station_id)
    )
    row = result.first()
    if row:
        station, line, factory = row
        return f"{factory.name} / {line.name} / {station.name}"
    return ""


@router.post("/interface", response_model=Response[InterfaceBindResponse], summary="绑定界面到工位")
async def bind_interface_to_stations(
    bind_data: InterfaceBindRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.BINDING_INTERFACE.value))
):
    """将界面绑定到一个或多个工位"""
    # 检查界面是否存在
    interface_result = await db.execute(
        select(Interface).where(Interface.id == bind_data.interfaceId)
    )
    interface = interface_result.scalar_one_or_none()
    
    if not interface:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="界面不存在"
        )
    
    bound_stations = []
    
    for station_id in bind_data.stationIds:
        # 检查工位是否存在
        station_result = await db.execute(
            select(Station).where(and_(Station.id == station_id, Station.is_deleted == 0))
        )
        station = station_result.scalar_one_or_none()
        
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工位 {station_id} 不存在"
            )
        
        # 检查是否已经绑定
        existing = await db.execute(
            select(InterfaceStationBinding).where(
                and_(
                    InterfaceStationBinding.interface_id == bind_data.interfaceId,
                    InterfaceStationBinding.station_id == station_id
                )
            )
        )
        
        if not existing.scalar_one_or_none():
            # 创建绑定关系
            binding = InterfaceStationBinding(
                id=generate_id("bind"),
                interface_id=bind_data.interfaceId,
                station_id=station_id,
                bind_user_id=current_user.id
            )
            db.add(binding)
        
        bound_stations.append({
            "id": station.id,
            "name": station.name,
            "code": station.code
        })
    
    await db.commit()
    
    return Response(
        code=200,
        message="绑定成功",
        data=InterfaceBindResponse(
            interfaceId=interface.id,
            interfaceName=interface.name,
            boundStations=bound_stations,
            bindTime=format_datetime(None)  # 当前时间
        )
    )


@router.delete("/interface", response_model=Response, summary="解绑界面与工位")
async def unbind_interface_from_stations(
    bind_data: InterfaceBindRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.BINDING_INTERFACE.value))
):
    """解绑界面与工位的绑定关系"""
    # 检查界面是否存在
    interface_result = await db.execute(
        select(Interface).where(Interface.id == bind_data.interfaceId)
    )
    if not interface_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="界面不存在"
        )
    
    # 删除绑定关系
    for station_id in bind_data.stationIds:
        await db.execute(
            delete(InterfaceStationBinding).where(
                and_(
                    InterfaceStationBinding.interface_id == bind_data.interfaceId,
                    InterfaceStationBinding.station_id == station_id
                )
            )
        )
    
    await db.commit()
    
    return Response(code=200, message="解绑成功", data=None)


@router.get("/stations/{station_id}", response_model=Response[StationBindingsResponse], summary="获取工位的所有绑定信息")
async def get_station_bindings(
    station_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定工位绑定的界面、部署清单和应用的 AutoUnit 包"""
    # 检查工位是否存在
    station_result = await db.execute(
        select(Station).where(and_(Station.id == station_id, Station.is_deleted == 0))
    )
    station = station_result.scalar_one_or_none()
    
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工位不存在"
        )
    
    # 获取工位路径
    station_path = await _get_station_path(station_id, db)
    
    # 获取绑定的界面
    interface_result = await db.execute(
        select(Interface, InterfaceStationBinding)
        .join(InterfaceStationBinding, Interface.id == InterfaceStationBinding.interface_id)
        .where(InterfaceStationBinding.station_id == station_id)
    )
    
    interfaces = []
    for interface, binding in interface_result:
        interfaces.append({
            "id": interface.id,
            "name": interface.name,
            "bindTime": format_datetime(binding.bind_time)
        })
    
    # 获取绑定的部署清单
    manifest_result = await db.execute(
        select(DeploymentManifest, ManifestStationBinding)
        .join(ManifestStationBinding, DeploymentManifest.id == ManifestStationBinding.manifest_id)
        .where(ManifestStationBinding.station_id == station_id)
    )
    
    manifests = []
    for manifest, binding in manifest_result:
        manifests.append({
            "id": manifest.id,
            "name": manifest.name,
            "version": manifest.version,
            "bindTime": format_datetime(binding.bind_time)
        })
    
    # 获取应用的 AutoUnit 包
    autounit_result = await db.execute(
        select(AutoUnitPackage, AutoUnitStationApplication)
        .join(AutoUnitStationApplication, AutoUnitPackage.id == AutoUnitStationApplication.package_id)
        .where(AutoUnitStationApplication.station_id == station_id)
    )
    
    autounit_packages = []
    for package, application in autounit_result:
        autounit_packages.append({
            "id": package.id,
            "name": package.name,
            "version": package.version,
            "applyTime": format_datetime(application.apply_time)
        })
    
    return Response(
        code=200,
        message="获取成功",
        data=StationBindingsResponse(
            stationId=station.id,
            stationName=station.name,
            stationCode=station.code or "",
            stationPath=station_path,
            interfaces=interfaces,
            deploymentManifests=manifests,
            autounitPackages=autounit_packages
        )
    )

