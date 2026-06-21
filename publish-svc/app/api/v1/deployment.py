"""
部署清单管理 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, delete
from app.core.database import get_db
from app.core.deps import get_current_user, require_permissions
from app.core.permissions import Permission
from app.core.utils import generate_id, format_datetime, compute_file_hash
from app.core.storage import get_storage, MinIOStorage
from app.models.user import User
from app.models.deployment import DeploymentManifest
from app.models.binding import ManifestStationBinding
from app.models.facility import Station, Line, Factory
from app.schemas.common import Response, PaginatedResponse
from app.schemas.deployment import (
    DeploymentManifestResponse, DeploymentManifestDetailResponse,
    DeploymentManifestUpdate, DeploymentManifestBind,
    DeploymentManifestBindResponse, StationInfo
)

router = APIRouter()


async def _get_bound_stations(manifest_id: str, db: AsyncSession) -> list:
    """获取部署清单绑定的工位列表"""
    result = await db.execute(
        select(Station, Line, Factory, ManifestStationBinding)
        .join(ManifestStationBinding, Station.id == ManifestStationBinding.station_id)
        .join(Line, Station.line_id == Line.id)
        .join(Factory, Line.factory_id == Factory.id)
        .where(
            and_(
                ManifestStationBinding.manifest_id == manifest_id,
                Station.is_deleted == 0,
                Line.is_deleted == 0,
                Factory.is_deleted == 0
            )
        )
    )
    
    stations = []
    for station, line, factory, _ in result:
        stations.append({
            "id": station.id,
            "name": station.name,
            "code": station.code,
            "path": f"{factory.name} / {line.name} / {station.name}"
        })
    return stations


@router.get("/manifests", response_model=Response[PaginatedResponse[DeploymentManifestResponse]], summary="获取部署清单列表")
async def get_deployment_manifests(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取部署清单列表（支持搜索）"""
    query = select(DeploymentManifest)
    
    if search:
        query = query.where(
            or_(
                DeploymentManifest.name.like(f"%{search}%"),
                DeploymentManifest.description.like(f"%{search}%")
            )
        )
    
    # 查询总数
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()
    
    # 分页查询
    query = query.offset((page - 1) * pageSize).limit(pageSize)
    result = await db.execute(query)
    manifests = result.scalars().all()
    
    # 构建响应
    manifest_list = []
    for manifest in manifests:
        # 获取上传用户名
        user_result = await db.execute(
            select(User.username).where(User.id == manifest.upload_user_id)
        )
        upload_user = user_result.scalar() or "unknown"
        
        # 获取绑定的工位
        bound_stations = await _get_bound_stations(manifest.id, db)
        
        manifest_list.append(DeploymentManifestResponse(
            id=manifest.id,
            name=manifest.name,
            description=manifest.description,
            fileName=manifest.file_name,
            version=manifest.version,
            size=manifest.size,
            uploadTime=format_datetime(manifest.upload_time),
            uploadUser=upload_user,
            boundStations=bound_stations,
            md5=manifest.md5
        ))
    
    return Response(
        code=200,
        message="获取成功",
        data=PaginatedResponse(
            list=manifest_list,
            total=total,
            page=page,
            pageSize=pageSize
        )
    )


@router.post("/manifests/upload", response_model=Response[DeploymentManifestResponse], summary="上传部署清单")
async def upload_deployment_manifest(
    file: UploadFile = File(...),
    name: str = Form(...),
    version: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    storage: MinIOStorage = Depends(get_storage),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.DEPLOYMENT_UPLOAD.value))
):
    """上传新的部署清单文件"""
    # 验证文件格式
    if not file.filename.endswith('.toml'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件格式错误：必须为 TOML 格式"
        )
    
    # 读取文件
    file_data = await file.read()
    
    # 读取文件内容
    try:
        content = file_data.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件编码错误：必须为 UTF-8 格式"
        )
    
    # 计算文件哈希
    md5, _ = compute_file_hash(file_data)
    
    # 上传到MinIO
    object_name = f"manifests/{name}/{file.filename}"
    file_path, _, _ = storage.upload_file(
        file_data,
        object_name,
        content_type="application/toml"
    )
    
    # 创建清单记录
    manifest = DeploymentManifest(
        id=generate_id("mf"),
        name=name,
        description=description,
        file_name=file.filename,
        version=version,
        size=len(file_data),
        file_path=file_path,
        content=content,
        md5=md5,
        upload_user_id=current_user.id
    )
    
    db.add(manifest)
    await db.commit()
    await db.refresh(manifest)
    
    return Response(
        code=200,
        message="上传成功",
        data=DeploymentManifestResponse(
            id=manifest.id,
            name=manifest.name,
            description=manifest.description,
            fileName=manifest.file_name,
            version=manifest.version,
            size=manifest.size,
            uploadTime=format_datetime(manifest.upload_time),
            uploadUser=current_user.username,
            boundStations=[],
            md5=manifest.md5
        )
    )


@router.get("/manifests/{manifest_id}", response_model=Response[DeploymentManifestDetailResponse], summary="获取部署清单详情")
async def get_deployment_manifest_detail(
    manifest_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定部署清单的详细信息"""
    # 查询清单
    result = await db.execute(
        select(DeploymentManifest).where(DeploymentManifest.id == manifest_id)
    )
    manifest = result.scalar_one_or_none()
    
    if not manifest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部署清单不存在"
        )
    
    # 获取上传用户
    upload_user_result = await db.execute(
        select(User.username).where(User.id == manifest.upload_user_id)
    )
    upload_user = upload_user_result.scalar() or "unknown"
    
    # 获取绑定的工位
    bound_stations = await _get_bound_stations(manifest.id, db)
    
    return Response(
        code=200,
        message="获取成功",
        data=DeploymentManifestDetailResponse(
            id=manifest.id,
            name=manifest.name,
            description=manifest.description,
            fileName=manifest.file_name,
            version=manifest.version,
            size=manifest.size,
            uploadTime=format_datetime(manifest.upload_time),
            uploadUser=upload_user,
            boundStations=bound_stations,
            md5=manifest.md5,
            content=manifest.content,
            downloadCount=0  # TODO: 统计下载次数
        )
    )


@router.put("/manifests/{manifest_id}", response_model=Response[dict], summary="更新部署清单信息")
async def update_deployment_manifest(
    manifest_id: str,
    update_data: DeploymentManifestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.DEPLOYMENT_UPLOAD.value))
):
    """更新部署清单的基本信息（名称、描述等）"""
    # 查询清单
    result = await db.execute(
        select(DeploymentManifest).where(DeploymentManifest.id == manifest_id)
    )
    manifest = result.scalar_one_or_none()
    
    if not manifest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部署清单不存在"
        )
    
    # 更新字段
    if update_data.name is not None:
        manifest.name = update_data.name
    if update_data.description is not None:
        manifest.description = update_data.description
    if update_data.version is not None:
        manifest.version = update_data.version
    
    await db.commit()
    await db.refresh(manifest)
    
    return Response(
        code=200,
        message="更新成功",
        data={
            "id": manifest.id,
            "name": manifest.name,
            "description": manifest.description,
            "version": manifest.version,
            "updateTime": format_datetime(manifest.update_time)
        }
    )


@router.delete("/manifests/{manifest_id}", response_model=Response, summary="删除部署清单")
async def delete_deployment_manifest(
    manifest_id: str,
    storage: MinIOStorage = Depends(get_storage),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.DEPLOYMENT_UPLOAD.value))
):
    """删除指定的部署清单"""
    # 查询清单
    result = await db.execute(
        select(DeploymentManifest).where(DeploymentManifest.id == manifest_id)
    )
    manifest = result.scalar_one_or_none()
    
    if not manifest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部署清单不存在"
        )
    
    # 检查是否已绑定工位
    binding_result = await db.execute(
        select(ManifestStationBinding).where(
            ManifestStationBinding.manifest_id == manifest_id
        )
    )
    bindings = binding_result.scalars().all()
    
    if bindings:
        # 获取绑定的工位名称
        station_names = []
        for binding in bindings:
            station_result = await db.execute(
                select(Station.name).where(Station.id == binding.station_id)
            )
            station_name = station_result.scalar()
            if station_name:
                station_names.append(station_name)
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该部署清单已绑定工位，请先解绑后再删除",
            headers={"X-Bound-Stations": ",".join(station_names)}
        )
    
    # 删除MinIO中的文件
    object_name = manifest.file_path.replace(f"{storage.bucket}/", "")
    storage.delete_file(object_name)
    
    # 删除清单记录
    await db.delete(manifest)
    await db.commit()
    
    return Response(code=200, message="删除成功", data=None)


@router.get("/manifests/{manifest_id}/download", summary="下载部署清单")
async def download_deployment_manifest(
    manifest_id: str,
    storage: MinIOStorage = Depends(get_storage),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载指定的部署清单文件"""
    # 查询清单
    result = await db.execute(
        select(DeploymentManifest).where(DeploymentManifest.id == manifest_id)
    )
    manifest = result.scalar_one_or_none()
    
    if not manifest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部署清单不存在"
        )
    
    # 从MinIO下载文件
    object_name = manifest.file_path.replace(f"{storage.bucket}/", "")
    file_data = storage.download_file(object_name)
    
    # 返回文件流
    return FastAPIResponse(
        content=file_data,
        media_type="application/toml",
        headers={
            "Content-Disposition": f'attachment; filename="{manifest.file_name}"',
            "Content-Length": str(manifest.size)
        }
    )


@router.post("/manifests/{manifest_id}/bind", response_model=Response[DeploymentManifestBindResponse], summary="绑定部署清单到工位")
async def bind_manifest_to_stations(
    manifest_id: str,
    bind_data: DeploymentManifestBind,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.DEPLOYMENT_BIND.value))
):
    """将部署清单绑定到一个或多个工位"""
    # 查询清单
    manifest_result = await db.execute(
        select(DeploymentManifest).where(DeploymentManifest.id == manifest_id)
    )
    manifest = manifest_result.scalar_one_or_none()
    
    if not manifest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部署清单不存在"
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
        
        # 检查是否已绑定
        existing = await db.execute(
            select(ManifestStationBinding).where(
                and_(
                    ManifestStationBinding.manifest_id == manifest_id,
                    ManifestStationBinding.station_id == station_id
                )
            )
        )
        
        if not existing.scalar_one_or_none():
            # 创建绑定关系
            binding = ManifestStationBinding(
                id=generate_id("mfb"),
                manifest_id=manifest_id,
                station_id=station_id,
                bind_user_id=current_user.id
            )
            db.add(binding)
        
        bound_stations.append(StationInfo(
            id=station.id,
            name=station.name,
            code=station.code
        ))
    
    await db.commit()
    
    return Response(
        code=200,
        message="绑定成功",
        data=DeploymentManifestBindResponse(
            manifestId=manifest.id,
            manifestName=manifest.name,
            boundStations=bound_stations,
            bindTime=format_datetime(None)
        )
    )


@router.delete("/manifests/{manifest_id}/bind", response_model=Response, summary="解绑部署清单与工位")
async def unbind_manifest_from_stations(
    manifest_id: str,
    bind_data: DeploymentManifestBind,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.DEPLOYMENT_BIND.value))
):
    """解绑部署清单与工位的绑定关系"""
    # 检查清单是否存在
    manifest_result = await db.execute(
        select(DeploymentManifest).where(DeploymentManifest.id == manifest_id)
    )
    if not manifest_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部署清单不存在"
        )
    
    # 删除绑定关系
    for station_id in bind_data.stationIds:
        await db.execute(
            delete(ManifestStationBinding).where(
                and_(
                    ManifestStationBinding.manifest_id == manifest_id,
                    ManifestStationBinding.station_id == station_id
                )
            )
        )
    
    await db.commit()
    
    return Response(code=200, message="解绑成功", data=None)

