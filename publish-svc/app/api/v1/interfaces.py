"""
界面管理 API
"""
import hashlib
import json
from typing import Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, delete
from app.core.database import get_db
from app.core.deps import get_current_user, require_permissions
from app.core.permissions import Permission
from app.core.utils import generate_id, format_datetime
from app.core.storage import get_storage
from app.models.user import User
from app.models.interface import Interface
from app.models.facility import Station, Line, Factory
from app.models.binding import InterfaceStationBinding
from app.schemas.common import Response, PaginatedResponse
from app.schemas.interface import (
    InterfaceUpdateInfo,
    InterfaceResponse, InterfaceDetailResponse, StationInfo
)

router = APIRouter()


async def _get_station_path(station_id: str, db: AsyncSession) -> str:
    """获取工位完整路径"""
    result = await db.execute(
        select(Station, Line, Factory)
        .join(Line, Station.line_id == Line.id)
        .join(Factory, Line.factory_id == Factory.id)
        .where(and_(Station.id == station_id, Station.is_deleted == 0))
    )
    row = result.first()
    if row:
        station, line, factory = row
        return f"{factory.name} / {line.name} / {station.name}"
    return ""


async def _get_bound_stations(interface_id: str, db: AsyncSession) -> list:
    """获取界面绑定的工位列表"""
    result = await db.execute(
        select(Station, InterfaceStationBinding)
        .join(InterfaceStationBinding, Station.id == InterfaceStationBinding.station_id)
        .where(and_(
            InterfaceStationBinding.interface_id == interface_id,
            Station.is_deleted == 0
        ))
    )
    
    stations = []
    for station, _ in result:
        path = await _get_station_path(station.id, db)
        stations.append({
            "id": station.id,
            "name": station.name,
            "code": station.code,
            "path": path
        })
    return stations


@router.get("", response_model=Response[PaginatedResponse[InterfaceResponse]], summary="获取界面列表")
async def get_interfaces(
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页条数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取界面列表（支持搜索和分页）"""
    # 构建查询
    query = select(Interface).where(Interface.is_deleted == 0)
    if search:
        query = query.where(
            or_(
                Interface.name.like(f"%{search}%"),
                Interface.description.like(f"%{search}%")
            )
        )
    
    # 查询总数
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()
    
    # 分页查询
    query = query.order_by(Interface.create_time.desc()).offset((page - 1) * pageSize).limit(pageSize)
    result = await db.execute(query)
    interfaces = result.scalars().all()
    
    # 构建响应
    interface_list = []
    for interface in interfaces:
        bound_stations = await _get_bound_stations(interface.id, db)
        
        # 获取创建人用户名
        user_result = await db.execute(
            select(User.username).where(User.id == interface.create_user)
        )
        create_user = user_result.scalar() or "unknown"
        
        interface_list.append(InterfaceResponse(
            id=interface.id,
            name=interface.name,
            description=interface.description,
            jsonFilePath=interface.json_file_path,
            fileSize=interface.file_size,
            fileMd5=interface.file_md5,
            thumbnail=interface.thumbnail,
            boundStations=bound_stations,
            createTime=format_datetime(interface.create_time),
            updateTime=format_datetime(interface.update_time),
            createUser=create_user
        ))
    
    return Response(
        code=200,
        message="获取成功",
        data=PaginatedResponse(
            list=interface_list,
            total=total,
            page=page,
            pageSize=pageSize
        )
    )


@router.post("", response_model=Response[InterfaceDetailResponse], summary="上传界面")
async def upload_interface(
    file: UploadFile = File(..., description="JSON配置文件"),
    name: str = Form(..., description="界面名称"),
    description: Optional[str] = Form(None, description="界面描述"),
    stationIds: Optional[str] = Form(None, description="工位ID列表(JSON字符串)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.INTERFACE_CREATE.value)),
    storage = Depends(get_storage)
):
    """上传界面JSON文件"""
    # 1. 验证文件格式
    if not file.filename or not file.filename.lower().endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持JSON文件"
        )
    
    # 2. 读取文件内容
    content = await file.read()
    
    # 3. 验证JSON格式
    try:
        json.loads(content.decode('utf-8'))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的JSON文件"
        )
    
    # 4. 生成界面ID
    interface_id = generate_id("interface")
    
    # 5. 上传到MinIO
    file_path = f"interfaces/{interface_id}/config.json"
    try:
        await storage.upload_bytes(object_name=file_path, file_data=content, content_type="application/json")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )
    
    # 6. 计算MD5
    file_md5 = hashlib.md5(content).hexdigest()
    
    # 7. 创建界面记录
    interface = Interface(
        id=interface_id,
        name=name,
        description=description,
        json_file_path=file_path,
        file_size=len(content),
        file_md5=file_md5,
        create_user=current_user.id
    )
    
    db.add(interface)
    await db.flush()
    
    # 8. 处理工位绑定
    if stationIds:
        try:
            station_id_list = json.loads(stationIds)
            for station_id in station_id_list:
                # 检查工位是否存在
                station_result = await db.execute(
                    select(Station).where(and_(Station.id == station_id, Station.is_deleted == 0))
                )
                if not station_result.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"工位 {station_id} 不存在"
                    )
                
                binding = InterfaceStationBinding(
                    id=generate_id("bind"),
                    interface_id=interface.id,
                    station_id=station_id,
                    bind_user_id=current_user.id
                )
                db.add(binding)
        except json.JSONDecodeError:
            pass  # 忽略JSON解析错误
    
    await db.commit()
    await db.refresh(interface)
    
    # 获取绑定的工位
    bound_stations = await _get_bound_stations(interface.id, db)
    
    return Response(
        code=200,
        message="上传成功",
        data=InterfaceDetailResponse(
            id=interface.id,
            name=interface.name,
            description=interface.description,
            jsonFilePath=interface.json_file_path,
            fileSize=interface.file_size,
            fileMd5=interface.file_md5,
            thumbnail=interface.thumbnail,
            boundStations=bound_stations,
            createTime=format_datetime(interface.create_time),
            updateTime=format_datetime(interface.update_time),
            createUser=current_user.username,
            lastEditUser=None
        )
    )


@router.put("/{interface_id}/info", response_model=Response[InterfaceResponse], summary="更新界面信息")
async def update_interface_info(
    interface_id: str,
    interface_data: InterfaceUpdateInfo,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.INTERFACE_EDIT.value))
):
    """更新界面的基本信息（名称、描述、工位绑定）"""
    # 查询界面
    result = await db.execute(
        select(Interface).where(and_(Interface.id == interface_id, Interface.is_deleted == 0))
    )
    interface = result.scalar_one_or_none()
    
    if not interface:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="界面不存在"
        )
    
    # 更新基本字段
    if interface_data.name is not None:
        interface.name = interface_data.name
    if interface_data.description is not None:
        interface.description = interface_data.description
    
    interface.last_edit_user = current_user.id
    
    # 更新工位绑定
    if interface_data.stationIds is not None:
        # 先软删除旧绑定
        await db.execute(
            delete(InterfaceStationBinding).where(
                InterfaceStationBinding.interface_id == interface_id
            )
        )
        
        # 添加新绑定
        for station_id in interface_data.stationIds:
            # 检查工位是否存在
            station_result = await db.execute(
                select(Station).where(and_(Station.id == station_id, Station.is_deleted == 0))
            )
            if not station_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"工位 {station_id} 不存在"
                )
            
            binding = InterfaceStationBinding(
                id=generate_id("bind"),
                interface_id=interface_id,
                station_id=station_id,
                bind_user_id=current_user.id
            )
            db.add(binding)
    
    await db.commit()
    await db.refresh(interface)
    
    # 获取绑定的工位
    bound_stations = await _get_bound_stations(interface.id, db)
    
    # 获取创建人用户名
    user_result = await db.execute(
        select(User.username).where(User.id == interface.create_user)
    )
    create_user = user_result.scalar() or "unknown"
    
    return Response(
        code=200,
        message="更新成功",
        data=InterfaceResponse(
            id=interface.id,
            name=interface.name,
            description=interface.description,
            jsonFilePath=interface.json_file_path,
            fileSize=interface.file_size,
            fileMd5=interface.file_md5,
            thumbnail=interface.thumbnail,
            boundStations=bound_stations,
            createTime=format_datetime(interface.create_time),
            updateTime=format_datetime(interface.update_time),
            createUser=create_user
        )
    )


@router.delete("/{interface_id}", response_model=Response, summary="删除界面")
async def delete_interface(
    interface_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.INTERFACE_DELETE.value)),
    storage = Depends(get_storage)
):
    """删除指定界面"""
    # 查询界面
    result = await db.execute(
        select(Interface).where(and_(Interface.id == interface_id, Interface.is_deleted == 0))
    )
    interface = result.scalar_one_or_none()
    
    if not interface:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="界面不存在"
        )
    
    # 删除MinIO中的文件
    if interface.json_file_path:
        try:
            await storage.delete_file_async(interface.json_file_path)
            # 如果有缩略图也删除
            if interface.thumbnail:
                thumbnail_path = f"interfaces/{interface_id}/thumbnail.png"
                await storage.delete_file_async(thumbnail_path)
        except Exception as e:
            # 记录日志但不阻止删除
            print(f"删除MinIO文件失败: {str(e)}")
    
    # 删除绑定关系
    await db.execute(
        delete(InterfaceStationBinding).where(InterfaceStationBinding.interface_id == interface_id)
    )
    
    # 软删除界面
    interface.is_deleted = 1
    
    await db.commit()
    
    return Response(code=200, message="删除成功", data=None)


@router.get("/{interface_id}", response_model=Response[InterfaceDetailResponse], summary="获取界面详情")
async def get_interface_detail(
    interface_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定界面的详细信息"""
    # 查询界面
    result = await db.execute(
        select(Interface).where(and_(Interface.id == interface_id, Interface.is_deleted == 0))
    )
    interface = result.scalar_one_or_none()
    
    if not interface:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="界面不存在"
        )
    
    # 获取绑定的工位
    bound_stations = await _get_bound_stations(interface.id, db)
    
    # 获取创建人和最后编辑人用户名
    user_result = await db.execute(
        select(User.username).where(User.id == interface.create_user)
    )
    create_user = user_result.scalar() or "unknown"
    
    last_edit_user = None
    if interface.last_edit_user:
        user_result = await db.execute(
            select(User.username).where(User.id == interface.last_edit_user)
        )
        last_edit_user = user_result.scalar()
    
    return Response(
        code=200,
        message="获取成功",
        data=InterfaceDetailResponse(
            id=interface.id,
            name=interface.name,
            description=interface.description,
            jsonFilePath=interface.json_file_path,
            fileSize=interface.file_size,
            fileMd5=interface.file_md5,
            thumbnail=interface.thumbnail,
            boundStations=bound_stations,
            createTime=format_datetime(interface.create_time),
            updateTime=format_datetime(interface.update_time),
            createUser=create_user,
            lastEditUser=last_edit_user
        )
    )


@router.get("/{interface_id}/download", summary="下载界面JSON文件")
async def download_interface_json(
    interface_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage = Depends(get_storage)
):
    """下载界面的JSON配置文件"""
    # 查询界面
    result = await db.execute(
        select(Interface).where(and_(Interface.id == interface_id, Interface.is_deleted == 0))
    )
    interface = result.scalar_one_or_none()
    
    if not interface:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="界面不存在"
        )
    
    if not interface.json_file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JSON文件不存在"
        )
    
    # 从MinIO下载文件
    try:
        file_content = await storage.download_file_async(interface.json_file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件下载失败: {str(e)}"
        )
    
    # 返回文件流
    # 使用 RFC 5987 编码中文文件名
    filename = f"{interface.name}.json"
    encoded_filename = quote(filename, safe='')
    
    return StreamingResponse(
        iter([file_content]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Content-Length": str(len(file_content))
        }
    )


@router.get("/{interface_id}/preview", response_model=Response[dict], summary="预览界面")
async def preview_interface(
    interface_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage = Depends(get_storage)
):
    """获取界面预览数据"""
    # 查询界面
    result = await db.execute(
        select(Interface).where(and_(Interface.id == interface_id, Interface.is_deleted == 0))
    )
    interface = result.scalar_one_or_none()
    
    if not interface:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="界面不存在"
        )
    
    # 从MinIO读取JSON内容
    config = None
    if interface.json_file_path:
        try:
            file_content = await storage.download_file_async(interface.json_file_path)
            config = json.loads(file_content.decode('utf-8'))
        except Exception as e:
            print(f"读取JSON文件失败: {str(e)}")
    
    return Response(
        code=200,
        message="获取成功",
        data={
            "id": interface.id,
            "name": interface.name,
            "config": config,
            "previewUrl": None  # 可选，预览地址
        }
    )
