"""
设施管理 API（厂区/线体/工位）
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.core.database import get_db
from app.core.deps import get_current_user, require_permissions
from app.core.permissions import Permission
from app.core.utils import generate_id, format_datetime
from app.models.user import User
from app.models.facility import Factory, Line, Station
from app.schemas.common import Response
from app.schemas.facility import (
    FactoryCreate, FactoryUpdate, FactoryResponse, FactoryTreeNode,
    LineCreate, LineUpdate, LineResponse, LineTreeNode,
    StationCreate, StationUpdate, StationResponse, StationTreeNode,
    FacilityTree, StationSearchResponse
)
from app.schemas.common import PaginatedResponse

router = APIRouter()


# ============ 获取设施树形结构 ============

@router.get("/tree", response_model=Response[FacilityTree], summary="获取设施树形结构")
async def get_facility_tree(
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取完整的厂区-线体-工位树形结构
    支持按名称、编号、描述模糊搜索
    """
    # 查询所有未删除的厂区
    factory_query = select(Factory).where(Factory.is_deleted == 0)
    if search:
        factory_query = factory_query.where(
            or_(
                Factory.name.like(f"%{search}%"),
                Factory.code.like(f"%{search}%")
            )
        )
    factory_result = await db.execute(factory_query)
    factories = factory_result.scalars().all()
    
    tree_data = []
    
    for factory in factories:
        # 查询该厂区下的所有线体
        line_query = select(Line).where(
            and_(Line.factory_id == factory.id, Line.is_deleted == 0)
        )
        if search:
            line_query = line_query.where(
                or_(
                    Line.name.like(f"%{search}%"),
                    Line.code.like(f"%{search}%")
                )
            )
        line_result = await db.execute(line_query)
        lines = line_result.scalars().all()
        
        line_nodes = []
        for line in lines:
            # 查询该线体下的所有工位
            station_query = select(Station).where(
                and_(Station.line_id == line.id, Station.is_deleted == 0)
            )
            if search:
                station_query = station_query.where(
                    or_(
                        Station.name.like(f"%{search}%"),
                        Station.code.like(f"%{search}%")
                    )
                )
            station_result = await db.execute(station_query)
            stations = station_result.scalars().all()
            
            # 构建工位节点
            station_nodes = [
                StationTreeNode(
                    id=station.id,
                    lineId=station.line_id,
                    name=station.name,
                    type="station",
                    code=station.code,
                    description=station.description,
                    ip=station.ip,
                    mac=station.mac,
                    status=station.status,
                    createTime=format_datetime(station.create_time),
                    updateTime=format_datetime(station.update_time)
                )
                for station in stations
            ]
            
            # 构建线体节点
            line_nodes.append(
                LineTreeNode(
                    id=line.id,
                    factoryId=line.factory_id,
                    name=line.name,
                    type="line",
                    code=line.code,
                    description=line.description,
                    status=line.status,
                    createTime=format_datetime(line.create_time),
                    updateTime=format_datetime(line.update_time),
                    children=station_nodes
                )
            )
        
        # 构建厂区节点
        tree_data.append(
            FactoryTreeNode(
                id=factory.id,
                name=factory.name,
                type="factory",
                code=factory.code,
                description=factory.description,
                location=factory.location,
                status=factory.status,
                createTime=format_datetime(factory.create_time),
                updateTime=format_datetime(factory.update_time),
                children=line_nodes
            )
        )
    
    return Response(code=200, message="获取成功", data=tree_data)


# ============ 厂区管理 ============

@router.post("/factory", response_model=Response[FactoryResponse], summary="创建厂区")
async def create_factory(
    factory_data: FactoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.FACILITY_FACTORY_CREATE.value))
):
    """
    创建新的厂区
    """
    # 检查编号是否重复
    if factory_data.code:
        existing_result = await db.execute(
            select(Factory).where(Factory.code == factory_data.code)
        )
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            # 如果是已删除的厂区，则恢复并更新信息
            if existing.is_deleted == 1:
                existing.is_deleted = 0
                existing.name = factory_data.name
                existing.description = factory_data.description
                existing.location = factory_data.location
                existing.status = factory_data.status
                existing.create_user_id = current_user.id
                
                await db.commit()
                await db.refresh(existing)
                
                return Response(
                    code=200,
                    message="恢复并更新成功",
                    data=FactoryResponse(
                        id=existing.id,
                        name=existing.name,
                        type="factory",
                        code=existing.code,
                        description=existing.description,
                        location=existing.location,
                        status=existing.status,
                        createTime=format_datetime(existing.create_time),
                        updateTime=format_datetime(existing.update_time)
                    )
                )
            else:
                # 如果是未删除的厂区,抛出异常
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"厂区编号 {factory_data.code} 已存在"
                )
    
    # 创建厂区
    factory = Factory(
        id=generate_id("factory"),
        name=factory_data.name,
        code=factory_data.code,
        description=factory_data.description,
        location=factory_data.location,
        status=factory_data.status,
        is_deleted=0,
        create_user_id=current_user.id
    )
    
    db.add(factory)
    await db.commit()
    await db.refresh(factory)
    
    return Response(
        code=200,
        message="创建成功",
        data=FactoryResponse(
            id=factory.id,
            name=factory.name,
            type="factory",
            code=factory.code,
            description=factory.description,
            location=factory.location,
            status=factory.status,
            createTime=format_datetime(factory.create_time),
            updateTime=format_datetime(factory.update_time)
        )
    )


@router.put("/factory/{factory_id}", response_model=Response[FactoryResponse], summary="更新厂区")
async def update_factory(
    factory_id: str,
    factory_data: FactoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.FACILITY_FACTORY_EDIT.value))
):
    """
    更新厂区信息
    """
    # 查询厂区
    result = await db.execute(
        select(Factory).where(and_(Factory.id == factory_id, Factory.is_deleted == 0))
    )
    factory = result.scalar_one_or_none()
    
    if not factory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="厂区不存在"
        )
    
    # 检查编号是否重复
    if factory_data.code and factory_data.code != factory.code:
        existing = await db.execute(
            select(Factory).where(Factory.code == factory_data.code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"厂区编号 {factory_data.code} 已存在"
            )
    
    # 更新字段
    update_data = factory_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(factory, field, value)
    
    await db.commit()
    await db.refresh(factory)
    
    return Response(
        code=200,
        message="更新成功",
        data=FactoryResponse(
            id=factory.id,
            name=factory.name,
            type="factory",
            code=factory.code,
            description=factory.description,
            location=factory.location,
            status=factory.status,
            createTime=format_datetime(factory.create_time),
            updateTime=format_datetime(factory.update_time)
        )
    )


@router.delete("/factory/{factory_id}", response_model=Response, summary="删除厂区")
async def delete_factory(
    factory_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.FACILITY_FACTORY_DELETE.value))
):
    """
    删除厂区（软删除，级联删除其下所有线体和工位）
    """
    # 查询厂区
    result = await db.execute(
        select(Factory).where(and_(Factory.id == factory_id, Factory.is_deleted == 0))
    )
    factory = result.scalar_one_or_none()
    
    if not factory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="厂区不存在"
        )
    
    # 软删除厂区
    factory.is_deleted = 1
    
    # 查询并软删除该厂区下的所有线体
    lines_result = await db.execute(
        select(Line).where(and_(Line.factory_id == factory_id, Line.is_deleted == 0))
    )
    lines = lines_result.scalars().all()
    
    for line in lines:
        line.is_deleted = 1
        
        # 查询并软删除该线体下的所有工位
        stations_result = await db.execute(
            select(Station).where(and_(Station.line_id == line.id, Station.is_deleted == 0))
        )
        stations = stations_result.scalars().all()
        
        for station in stations:
            station.is_deleted = 1
    
    await db.commit()
    
    return Response(code=200, message="删除成功", data=None)


# ============ 线体管理 ============

@router.post("/line", response_model=Response[LineResponse], summary="创建线体")
async def create_line(
    line_data: LineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.FACILITY_LINE_CREATE.value))
):
    """
    在指定厂区下创建新的线体
    """
    # 检查厂区是否存在
    factory_result = await db.execute(
        select(Factory).where(and_(Factory.id == line_data.factoryId, Factory.is_deleted == 0))
    )
    if not factory_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="厂区不存在"
        )
    
    # 检查编号是否重复
    if line_data.code:
        existing = await db.execute(
            select(Line).where(Line.code == line_data.code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"线体编号 {line_data.code} 已存在"
            )
    
    # 创建线体
    line = Line(
        id=generate_id("line"),
        factory_id=line_data.factoryId,
        name=line_data.name,
        code=line_data.code,
        description=line_data.description,
        status=line_data.status,
        is_deleted=0,
        create_user_id=current_user.id
    )
    
    db.add(line)
    await db.commit()
    await db.refresh(line)
    
    return Response(
        code=200,
        message="创建成功",
        data=LineResponse(
            id=line.id,
            factoryId=line.factory_id,
            name=line.name,
            type="line",
            code=line.code,
            description=line.description,
            status=line.status,
            createTime=format_datetime(line.create_time),
            updateTime=format_datetime(line.update_time)
        )
    )


@router.put("/line/{line_id}", response_model=Response[LineResponse], summary="更新线体")
async def update_line(
    line_id: str,
    line_data: LineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.FACILITY_LINE_EDIT.value))
):
    """
    更新线体信息
    """
    # 查询线体
    result = await db.execute(
        select(Line).where(and_(Line.id == line_id, Line.is_deleted == 0))
    )
    line = result.scalar_one_or_none()
    
    if not line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="线体不存在"
        )
    
    # 检查编号是否重复
    if line_data.code and line_data.code != line.code:
        existing = await db.execute(
            select(Line).where(Line.code == line_data.code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"线体编号 {line_data.code} 已存在"
            )
    
    # 更新字段
    update_data = line_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(line, field, value)
    
    await db.commit()
    await db.refresh(line)
    
    return Response(
        code=200,
        message="更新成功",
        data=LineResponse(
            id=line.id,
            factoryId=line.factory_id,
            name=line.name,
            type="line",
            code=line.code,
            description=line.description,
            status=line.status,
            createTime=format_datetime(line.create_time),
            updateTime=format_datetime(line.update_time)
        )
    )


@router.delete("/line/{line_id}", response_model=Response, summary="删除线体")
async def delete_line(
    line_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.FACILITY_LINE_DELETE.value))
):
    """
    删除线体（软删除，级联删除其下所有工位）
    """
    # 查询线体
    result = await db.execute(
        select(Line).where(and_(Line.id == line_id, Line.is_deleted == 0))
    )
    line = result.scalar_one_or_none()
    
    if not line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="线体不存在"
        )
    
    # 软删除线体
    line.is_deleted = 1
    
    # 查询并软删除该线体下的所有工位
    stations_result = await db.execute(
        select(Station).where(and_(Station.line_id == line_id, Station.is_deleted == 0))
    )
    stations = stations_result.scalars().all()
    
    for station in stations:
        station.is_deleted = 1
    
    await db.commit()
    
    return Response(code=200, message="删除成功", data=None)


# ============ 工位管理 ============

@router.post("/station", response_model=Response[StationResponse], summary="创建工位")
async def create_station(
    station_data: StationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.FACILITY_STATION_CREATE.value))
):
    """
    在指定线体下创建新的工位
    """
    # 检查线体是否存在
    line_result = await db.execute(
        select(Line).where(and_(Line.id == station_data.lineId, Line.is_deleted == 0))
    )
    if not line_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="线体不存在"
        )
    
    # 检查编号是否重复
    if station_data.code:
        existing = await db.execute(
            select(Station).where(Station.code == station_data.code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"工位编号 {station_data.code} 已存在"
            )
    
    # 创建工位
    station = Station(
        id=generate_id("station"),
        line_id=station_data.lineId,
        name=station_data.name,
        code=station_data.code,
        description=station_data.description,
        ip=station_data.ip,
        mac=station_data.mac,
        status=station_data.status,
        is_deleted=0,
        create_user_id=current_user.id
    )
    
    db.add(station)
    await db.commit()
    await db.refresh(station)
    
    return Response(
        code=200,
        message="创建成功",
        data=StationResponse(
            id=station.id,
            lineId=station.line_id,
            name=station.name,
            type="station",
            code=station.code,
            description=station.description,
            ip=station.ip,
            mac=station.mac,
            status=station.status,
            createTime=format_datetime(station.create_time),
            updateTime=format_datetime(station.update_time)
        )
    )


@router.put("/station/{station_id}", response_model=Response[StationResponse], summary="更新工位")
async def update_station(
    station_id: str,
    station_data: StationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.FACILITY_STATION_EDIT.value))
):
    """
    更新工位信息
    """
    # 查询工位
    result = await db.execute(
        select(Station).where(and_(Station.id == station_id, Station.is_deleted == 0))
    )
    station = result.scalar_one_or_none()
    
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工位不存在"
        )
    
    # 检查编号是否重复
    if station_data.code and station_data.code != station.code:
        existing = await db.execute(
            select(Station).where(Station.code == station_data.code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"工位编号 {station_data.code} 已存在"
            )
    
    # 更新字段
    update_data = station_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(station, field, value)
    
    await db.commit()
    await db.refresh(station)
    
    return Response(
        code=200,
        message="更新成功",
        data=StationResponse(
            id=station.id,
            lineId=station.line_id,
            name=station.name,
            type="station",
            code=station.code,
            description=station.description,
            ip=station.ip,
            mac=station.mac,
            status=station.status,
            createTime=format_datetime(station.create_time),
            updateTime=format_datetime(station.update_time)
        )
    )


@router.delete("/station/{station_id}", response_model=Response, summary="删除工位")
async def delete_station(
    station_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.FACILITY_STATION_DELETE.value))
):
    """
    删除工位（软删除）
    
    注意：如果工位已绑定界面/驱动/AutoUnit，需要先解绑
    """
    # 查询工位
    result = await db.execute(
        select(Station).where(and_(Station.id == station_id, Station.is_deleted == 0))
    )
    station = result.scalar_one_or_none()
    
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工位不存在"
        )
    
    # TODO: 检查工位是否有绑定关系，如有则返回错误
    # 这里先简单实现软删除
    
    # 软删除工位
    station.is_deleted = 1
    
    await db.commit()
    
    return Response(code=200, message="删除成功", data=None)


# ============ 工位模糊搜索 ============

@router.get("/stations/search", response_model=Response[PaginatedResponse[StationSearchResponse]], summary="工位模糊搜索")
async def search_stations(
    keyword: Optional[str] = Query(None, description="搜索关键词（工位名称、编号）"),
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    工位模糊搜索
    支持按工位名称、编号模糊搜索
    返回工位列表及其所属厂区、线体信息
    """
    from sqlalchemy import func
    
    # 构建查询
    query = select(Station, Line, Factory).join(
        Line, Station.line_id == Line.id
    ).join(
        Factory, Line.factory_id == Factory.id
    ).where(
        and_(
            Station.is_deleted == 0,
            Line.is_deleted == 0,
            Factory.is_deleted == 0
        )
    )
    
    # 添加关键词搜索
    if keyword:
        query = query.where(
            or_(
                Station.name.like(f"%{keyword}%"),
                Station.code.like(f"%{keyword}%")
            )
        )
    
    # 查询总数
    count_query = select(func.count()).select_from(
        select(Station).join(Line, Station.line_id == Line.id).join(
            Factory, Line.factory_id == Factory.id
        ).where(
            and_(
                Station.is_deleted == 0,
                Line.is_deleted == 0,
                Factory.is_deleted == 0
            )
        ).subquery()
    )
    
    if keyword:
        count_query = select(func.count()).select_from(
            select(Station).join(Line, Station.line_id == Line.id).join(
                Factory, Line.factory_id == Factory.id
            ).where(
                and_(
                    Station.is_deleted == 0,
                    Line.is_deleted == 0,
                    Factory.is_deleted == 0,
                    or_(
                        Station.name.like(f"%{keyword}%"),
                        Station.code.like(f"%{keyword}%")
                    )
                )
            ).subquery()
        )
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    # 分页查询
    query = query.order_by(Station.create_time.desc()).offset((page - 1) * pageSize).limit(pageSize)
    result = await db.execute(query)
    rows = result.all()
    
    # 构建响应
    station_list = []
    for station, line, factory in rows:
        path = f"{factory.name} / {line.name} / {station.name}"
        
        station_list.append(StationSearchResponse(
            id=station.id,
            name=station.name,
            code=station.code,
            description=station.description,
            ip=station.ip,
            mac=station.mac,
            status=station.status,
            path=path,
            factoryId=factory.id,
            factoryName=factory.name,
            lineId=line.id,
            lineName=line.name,
            createTime=format_datetime(station.create_time),
            updateTime=format_datetime(station.update_time)
        ))
    
    return Response(
        code=200,
        message="获取成功",
        data=PaginatedResponse(
            list=station_list,
            total=total,
            page=page,
            pageSize=pageSize
        )
    )
