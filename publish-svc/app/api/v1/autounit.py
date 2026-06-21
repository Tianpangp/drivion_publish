"""
AutoUnit 包管理 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, delete
from app.core.database import get_db
from app.core.deps import get_current_user, require_permissions
from app.core.permissions import Permission
from app.core.utils import generate_id, format_datetime, parse_tar_package
from app.core.storage import get_storage, MinIOStorage
from app.models.user import User
from app.models.package import AutoUnitPackage
from app.models.facility import Station
from app.models.binding import AutoUnitStationApplication
from app.schemas.common import Response, PaginatedResponse
from app.schemas.autounit import (
    AutoUnitPackageResponse, AutoUnitPackageDetailResponse,
    AutoUnitPackageUpdateStatus, AutoUnitPackageApply,
    AutoUnitPackageApplyResponse, StationInfo
)

router = APIRouter()


async def _get_bound_stations(package_id: str, db: AsyncSession) -> list:
    """获取包绑定的工位列表"""
    result = await db.execute(
        select(Station, AutoUnitStationApplication)
        .join(AutoUnitStationApplication, Station.id == AutoUnitStationApplication.station_id)
        .where(AutoUnitStationApplication.package_id == package_id)
    )
    
    stations = []
    for station, _ in result:
        stations.append({
            "id": station.id,
            "name": station.name,
            "code": station.code
        })
    return stations


@router.get("/packages", response_model=Response[PaginatedResponse[AutoUnitPackageResponse]], summary="获取AutoUnit包列表")
async def get_autounit_packages(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取AutoUnit包列表（支持筛选和搜索）"""
    query = select(AutoUnitPackage)
    
    if search:
        query = query.where(
            or_(
                AutoUnitPackage.name.like(f"%{search}%"),
                AutoUnitPackage.file_name.like(f"%{search}%")
            )
        )
    
    if status:
        query = query.where(AutoUnitPackage.status == status)
    
    # 查询总数
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()
    
    # 分页查询
    query = query.offset((page - 1) * pageSize).limit(pageSize)
    result = await db.execute(query)
    packages = result.scalars().all()
    
    # 构建响应
    package_list = []
    for pkg in packages:
        # 获取上传用户名
        user_result = await db.execute(
            select(User.username).where(User.id == pkg.upload_user_id)
        )
        upload_user = user_result.scalar() or "unknown"
        
        # 获取绑定的工位
        bound_stations = await _get_bound_stations(pkg.id, db)
        
        package_list.append(AutoUnitPackageResponse(
            id=pkg.id,
            name=pkg.name,
            fileName=pkg.file_name,
            version=pkg.version,
            size=pkg.size,
            uploadTime=format_datetime(pkg.upload_time),
            uploadUser=upload_user,
            status=pkg.status,
            description=pkg.description,
            boundStations=bound_stations,
            dependencies=pkg.dependencies,
            pythonVersion=pkg.python_version,
            md5=pkg.md5,
            sha256=pkg.sha256
        ))
    
    return Response(
        code=200,
        message="获取成功",
        data=PaginatedResponse(
            list=package_list,
            total=total,
            page=page,
            pageSize=pageSize
        )
    )


@router.post("/packages/upload", response_model=Response[AutoUnitPackageResponse], summary="上传AutoUnit包")
async def upload_autounit_package(
    file: UploadFile = File(...),
    name: str = Form(...),
    version: str = Form(...),
    description: Optional[str] = Form(None),
    pythonVersion: Optional[str] = Form(None),
    storage: MinIOStorage = Depends(get_storage),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.AUTOUNIT_UPLOAD.value))
):
    """上传新的AutoUnit Python包"""
    # 检查版本是否已存在
    existing = await db.execute(
        select(AutoUnitPackage).where(
            and_(AutoUnitPackage.name == name, AutoUnitPackage.version == version)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"包 {name} 版本 {version} 已存在"
        )
    
    # 读取文件
    file_data = await file.read()
    
    # 解析包信息
    package_info = parse_tar_package(file_data)
    
    # 上传到MinIO
    object_name = f"autounit/{name}/{version}/{file.filename}"
    file_path, md5, sha256 = storage.upload_file(
        file_data,
        object_name,
        content_type=file.content_type or "application/gzip"
    )
    
    # 创建包记录
    package = AutoUnitPackage(
        id=generate_id("pkg"),
        name=name,
        version=version,
        file_name=file.filename,
        file_path=file_path,
        size=len(file_data),
        md5=md5,
        sha256=sha256,
        status="unpublished",
        description=description or package_info.get("readme"),
        python_version=pythonVersion or package_info.get("python_version"),
        dependencies=package_info.get("dependencies"),
        readme=package_info.get("readme"),
        upload_user_id=current_user.id
    )
    
    db.add(package)
    await db.commit()
    await db.refresh(package)
    
    return Response(
        code=200,
        message="上传成功",
        data=AutoUnitPackageResponse(
            id=package.id,
            name=package.name,
            fileName=package.file_name,
            version=package.version,
            size=package.size,
            uploadTime=format_datetime(package.upload_time),
            uploadUser=current_user.username,
            status=package.status,
            description=package.description,
            boundStations=[],
            dependencies=package.dependencies,
            pythonVersion=package.python_version,
            md5=package.md5,
            sha256=package.sha256
        )
    )


@router.put("/packages/{package_id}/status", response_model=Response[dict], summary="更新AutoUnit包状态")
async def update_package_status(
    package_id: str,
    status_data: AutoUnitPackageUpdateStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.AUTOUNIT_PUBLISH.value))
):
    """更新AutoUnit包的状态（发布/测试/未发布）"""
    # 查询包
    result = await db.execute(
        select(AutoUnitPackage).where(AutoUnitPackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="包不存在"
        )
    
    # 更新状态
    package.status = status_data.status
    if status_data.status == "published":
        package.publish_user_id = current_user.id
        package.publish_time = func.now()
    
    await db.commit()
    await db.refresh(package)
    
    return Response(
        code=200,
        message="状态更新成功",
        data={
            "id": package.id,
            "status": package.status,
            "updateTime": format_datetime(package.update_time)
        }
    )


@router.delete("/packages/{package_id}/recall", response_model=Response, summary="撤回AutoUnit包")
async def recall_package(
    package_id: str,
    storage: MinIOStorage = Depends(get_storage),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.AUTOUNIT_PUBLISH.value))
):
    """撤回并删除AutoUnit包"""
    # 查询包
    result = await db.execute(
        select(AutoUnitPackage).where(AutoUnitPackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="包不存在"
        )
    
    # 删除MinIO中的文件
    object_name = package.file_path.replace(f"{storage.bucket}/", "")
    storage.delete_file(object_name)
    
    # 删除应用关系
    await db.execute(
        delete(AutoUnitStationApplication).where(
            AutoUnitStationApplication.package_id == package_id
        )
    )
    
    # 删除包记录
    await db.delete(package)
    await db.commit()
    
    return Response(code=200, message="撤回成功", data=None)


@router.get("/packages/{package_id}/download", summary="下载AutoUnit包")
async def download_package(
    package_id: str,
    storage: MinIOStorage = Depends(get_storage),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载指定的AutoUnit包文件"""
    # 查询包
    result = await db.execute(
        select(AutoUnitPackage).where(AutoUnitPackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="包不存在"
        )
    
    # 从MinIO下载文件
    object_name = package.file_path.replace(f"{storage.bucket}/", "")
    file_data = storage.download_file(object_name)
    
    # 返回文件流
    return FastAPIResponse(
        content=file_data,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{package.file_name}"',
            "Content-Length": str(package.size)
        }
    )


@router.get("/packages/{package_id}", response_model=Response[AutoUnitPackageDetailResponse], summary="获取AutoUnit包详情")
async def get_package_detail(
    package_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定AutoUnit包的详细信息"""
    # 查询包
    result = await db.execute(
        select(AutoUnitPackage).where(AutoUnitPackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="包不存在"
        )
    
    # 获取上传用户
    upload_user_result = await db.execute(
        select(User.username).where(User.id == package.upload_user_id)
    )
    upload_user = upload_user_result.scalar() or "unknown"
    
    # 获取发布用户
    publish_user = None
    if package.publish_user_id:
        publish_user_result = await db.execute(
            select(User.username).where(User.id == package.publish_user_id)
        )
        publish_user = publish_user_result.scalar()
    
    # 获取绑定的工位
    bound_stations = await _get_bound_stations(package.id, db)
    
    return Response(
        code=200,
        message="获取成功",
        data=AutoUnitPackageDetailResponse(
            id=package.id,
            name=package.name,
            fileName=package.file_name,
            version=package.version,
            size=package.size,
            uploadTime=format_datetime(package.upload_time),
            uploadUser=upload_user,
            status=package.status,
            publishTime=format_datetime(package.publish_time),
            publishUser=publish_user,
            description=package.description,
            boundStations=bound_stations,
            dependencies=package.dependencies,
            pythonVersion=package.python_version,
            md5=package.md5,
            sha256=package.sha256,
            readme=package.readme,
            changelog=package.changelog
        )
    )


@router.post("/packages/{package_id}/apply", response_model=Response[AutoUnitPackageApplyResponse], summary="应用AutoUnit包到工位")
async def apply_package_to_stations(
    package_id: str,
    apply_data: AutoUnitPackageApply,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.AUTOUNIT_UPLOAD.value))
):
    """将AutoUnit包应用到一个或多个工位"""
    # 查询包
    package_result = await db.execute(
        select(AutoUnitPackage).where(AutoUnitPackage.id == package_id)
    )
    package = package_result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="包不存在"
        )
    
    applied_stations = []
    
    for station_id in apply_data.stationIds:
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
        
        # 检查是否已应用
        existing = await db.execute(
            select(AutoUnitStationApplication).where(
                and_(
                    AutoUnitStationApplication.package_id == package_id,
                    AutoUnitStationApplication.station_id == station_id
                )
            )
        )
        
        if not existing.scalar_one_or_none():
            # 创建应用关系
            application = AutoUnitStationApplication(
                id=generate_id("app"),
                package_id=package_id,
                station_id=station_id,
                apply_user_id=current_user.id
            )
            db.add(application)
        
        applied_stations.append(StationInfo(
            id=station.id,
            name=station.name,
            code=station.code
        ))
    
    await db.commit()
    
    return Response(
        code=200,
        message="应用成功",
        data=AutoUnitPackageApplyResponse(
            packageId=package.id,
            packageName=package.name,
            appliedStations=applied_stations,
            applyTime=format_datetime(None)
        )
    )


@router.delete("/packages/{package_id}/apply", response_model=Response, summary="取消AutoUnit包在工位的应用")
async def unapply_package_from_stations(
    package_id: str,
    apply_data: AutoUnitPackageApply,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.AUTOUNIT_UPLOAD.value))
):
    """取消AutoUnit包在指定工位的应用"""
    # 检查包是否存在
    package_result = await db.execute(
        select(AutoUnitPackage).where(AutoUnitPackage.id == package_id)
    )
    if not package_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="包不存在"
        )
    
    # 删除应用关系
    for station_id in apply_data.stationIds:
        await db.execute(
            delete(AutoUnitStationApplication).where(
                and_(
                    AutoUnitStationApplication.package_id == package_id,
                    AutoUnitStationApplication.station_id == station_id
                )
            )
        )
    
    await db.commit()
    
    return Response(code=200, message="取消应用成功", data=None)

