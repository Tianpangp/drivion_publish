"""
驱动包管理 API
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
from app.models.package import DriverPackage
from app.schemas.common import Response, PaginatedResponse
from app.schemas.driver import (
    DriverPackageResponse, DriverPackageDetailResponse
)

router = APIRouter()


@router.get("/packages", response_model=Response[PaginatedResponse[DriverPackageResponse]], summary="获取驱动包列表")
async def get_driver_packages(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取驱动包列表（支持筛选和搜索）"""
    query = select(DriverPackage)
    
    if search:
        query = query.where(
            or_(
                DriverPackage.name.like(f"%{search}%"),
                DriverPackage.file_name.like(f"%{search}%")
            )
        )
    
    if type:
        query = query.where(DriverPackage.type == type)
    
    if status:
        query = query.where(DriverPackage.status == status)
    
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
        
        package_list.append(DriverPackageResponse(
            id=pkg.id,
            name=pkg.name,
            fileName=pkg.file_name,
            type=pkg.type,
            version=pkg.version,
            size=pkg.size,
            uploadTime=format_datetime(pkg.upload_time),
            uploadUser=upload_user,
            status=pkg.status,
            description=pkg.description,
            boundStations=[],  # 驱动包不绑定工位
            protocol=pkg.protocol,
            manufacturer=pkg.manufacturer,
            deviceModel=pkg.device_model,
            md5=pkg.md5
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


@router.post("/packages/upload", response_model=Response[DriverPackageResponse], summary="上传驱动包")
async def upload_driver_package(
    file: UploadFile = File(...),
    type: str = Form(...),
    name: str = Form(...),
    version: str = Form(...),
    description: Optional[str] = Form(None),
    protocol: Optional[str] = Form(None),
    manufacturer: Optional[str] = Form(None),
    deviceModel: Optional[str] = Form(None),
    storage: MinIOStorage = Depends(get_storage),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.DRIVER_UPLOAD.value))
):
    """上传新的驱动包"""
    # 验证驱动类型
    if type not in ["java", "python", "cpp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="驱动类型必须是 java、python 或 cpp"
        )
    
    # 检查版本是否已存在
    existing = await db.execute(
        select(DriverPackage).where(
            and_(
                DriverPackage.name == name,
                DriverPackage.version == version,
                DriverPackage.type == type
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"驱动包 {name} (类型: {type}) 版本 {version} 已存在"
        )
    
    # 读取文件
    file_data = await file.read()
    
    # 计算文件哈希
    md5, sha256 = compute_file_hash(file_data)
    
    # 上传到MinIO
    object_name = f"drivers/{type}/{name}/{version}/{file.filename}"
    file_path, _, _ = storage.upload_file(
        file_data,
        object_name,
        content_type=file.content_type or "application/octet-stream"
    )
    
    # 创建包记录
    package = DriverPackage(
        id=generate_id("drv"),
        name=name,
        version=version,
        type=type,
        file_name=file.filename,
        file_path=file_path,
        size=len(file_data),
        md5=md5,
        sha256=sha256,
        status="unpublished",
        description=description,
        protocol=protocol,
        manufacturer=manufacturer,
        device_model=deviceModel,
        upload_user_id=current_user.id
    )
    
    db.add(package)
    await db.commit()
    await db.refresh(package)
    
    return Response(
        code=200,
        message="上传成功",
        data=DriverPackageResponse(
            id=package.id,
            name=package.name,
            fileName=package.file_name,
            type=package.type,
            version=package.version,
            size=package.size,
            uploadTime=format_datetime(package.upload_time),
            uploadUser=current_user.username,
            status=package.status,
            description=package.description,
            boundStations=[],
            protocol=package.protocol,
            manufacturer=package.manufacturer,
            deviceModel=package.device_model,
            md5=package.md5
        )
    )


@router.post("/packages/{package_id}/publish", response_model=Response[dict], summary="发布驱动包")
async def publish_driver_package(
    package_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.DRIVER_PUBLISH.value))
):
    """发布驱动包到生产环境"""
    # 查询包
    result = await db.execute(
        select(DriverPackage).where(DriverPackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="驱动包不存在"
        )
    
    # 更新状态
    package.status = "published"
    package.publish_user_id = current_user.id
    package.publish_time = func.now()
    
    await db.commit()
    await db.refresh(package)
    
    return Response(
        code=200,
        message="发布成功",
        data={
            "id": package.id,
            "status": package.status,
            "publishTime": format_datetime(package.publish_time),
            "publishUser": current_user.username
        }
    )


@router.post("/packages/{package_id}/unpublish", response_model=Response[dict], summary="下架驱动包")
async def unpublish_driver_package(
    package_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.DRIVER_PUBLISH.value))
):
    """下架已发布的驱动包（不删除，只改变状态）"""
    # 查询包
    result = await db.execute(
        select(DriverPackage).where(DriverPackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="驱动包不存在"
        )
    
    # 更新状态
    package.status = "unpublished"
    package.unpublish_user_id = current_user.id
    package.unpublish_time = func.now()
    
    await db.commit()
    await db.refresh(package)
    
    return Response(
        code=200,
        message="下架成功",
        data={
            "id": package.id,
            "status": package.status,
            "unpublishTime": format_datetime(package.unpublish_time),
            "unpublishUser": current_user.username
        }
    )


@router.delete("/packages/{package_id}/recall", response_model=Response, summary="撤回驱动包")
async def recall_driver_package(
    package_id: str,
    storage: MinIOStorage = Depends(get_storage),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.DRIVER_PUBLISH.value))
):
    """撤回并删除驱动包"""
    # 查询包
    result = await db.execute(
        select(DriverPackage).where(DriverPackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="驱动包不存在"
        )
    
    # 删除MinIO中的文件
    object_name = package.file_path.replace(f"{storage.bucket}/", "")
    storage.delete_file(object_name)
    
    # 删除包记录
    await db.delete(package)
    await db.commit()
    
    return Response(code=200, message="撤回成功", data=None)


@router.get("/packages/{package_id}/download", summary="下载驱动包")
async def download_driver_package(
    package_id: str,
    storage: MinIOStorage = Depends(get_storage),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载指定的驱动包文件"""
    # 查询包
    result = await db.execute(
        select(DriverPackage).where(DriverPackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="驱动包不存在"
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


@router.get("/packages/{package_id}", response_model=Response[DriverPackageDetailResponse], summary="获取驱动包详情")
async def get_driver_package_detail(
    package_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定驱动包的详细信息"""
    # 查询包
    result = await db.execute(
        select(DriverPackage).where(DriverPackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="驱动包不存在"
        )
    
    # 获取上传用户
    upload_user_result = await db.execute(
        select(User.username).where(User.id == package.upload_user_id)
    )
    upload_user = upload_user_result.scalar() or "unknown"
    
    return Response(
        code=200,
        message="获取成功",
        data=DriverPackageDetailResponse(
            id=package.id,
            name=package.name,
            fileName=package.file_name,
            type=package.type,
            version=package.version,
            size=package.size,
            uploadTime=format_datetime(package.upload_time),
            uploadUser=upload_user,
            status=package.status,
            publishTime=format_datetime(package.publish_time),
            unpublishTime=format_datetime(package.unpublish_time),
            description=package.description,
            boundStations=[],  # 驱动包不绑定工位
            protocol=package.protocol,
            manufacturer=package.manufacturer,
            deviceModel=package.device_model,
            supportedPlatforms=package.supported_platforms,
            apiDocUrl=package.api_doc_url,
            readme=package.readme,
            md5=package.md5,
            sha256=package.sha256
        )
    )

