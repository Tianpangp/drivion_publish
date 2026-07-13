"""
日志管理 API
"""
import csv
import io
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from app.core.database import get_db
from app.core.deps import get_current_user, require_permissions
from app.core.permissions import Permission
from app.core.utils import format_datetime
from app.models.user import User
from app.models.log import OperationLog
from app.schemas.common import Response, PaginatedResponse
from app.schemas.log import (
    OperationLogResponse, OperationLogDetailResponse,
    LogExportRequest
)

router = APIRouter()


@router.get("", response_model=Response[PaginatedResponse[OperationLogResponse]], summary="获取操作日志列表")
async def get_operation_logs(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    operation: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    startTime: Optional[str] = Query(None),
    endTime: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.LOG_VIEW.value))
):
    """获取系统操作日志列表（支持筛选和搜索）"""
    query = select(OperationLog)
    
    # 搜索关键词
    if search:
        query = query.where(
            or_(
                OperationLog.operator.like(f"%{search}%"),
                OperationLog.description.like(f"%{search}%")
            )
        )
    
    # 操作类型筛选
    if operation:
        query = query.where(OperationLog.operation == operation)
    
    # 操作结果筛选
    if result:
        query = query.where(OperationLog.result == result)
    
    # 时间范围筛选
    if startTime:
        query = query.where(OperationLog.time >= startTime)
    if endTime:
        query = query.where(OperationLog.time <= endTime)
    
    # 模块筛选
    if module:
        query = query.where(OperationLog.module == module)
    
    # 查询总数
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()
    
    # 分页查询（按时间倒序）
    query = query.order_by(OperationLog.time.desc()).offset((page - 1) * pageSize).limit(pageSize)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # 构建响应
    log_list = []
    for log in logs:
        log_list.append(OperationLogResponse(
            id=log.id,
            operation=log.operation,
            module=log.module,
            operator=log.operator,
            operatorId=log.operator_id,
            role=log.role,
            result=log.result,
            time=format_datetime(log.time),
            description=log.description,
            ip=log.ip,
            userAgent=log.user_agent,
            changes=log.changes,
            error=log.error
        ))
    
    return Response(
        code=200,
        message="获取成功",
        data=PaginatedResponse(
            list=log_list,
            total=total or 0,
            page=page,
            pageSize=pageSize
        )
    )


@router.get("/{log_id}", response_model=Response[OperationLogDetailResponse], summary="获取日志详情")
async def get_operation_log_detail(
    log_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.LOG_VIEW.value))
):
    """获取指定日志的详细信息"""
    # 查询日志
    result = await db.execute(
        select(OperationLog).where(OperationLog.id == log_id)
    )
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日志不存在"
        )
    
    return Response(
        code=200,
        message="获取成功",
        data=OperationLogDetailResponse(
            id=log.id,
            operation=log.operation,
            module=log.module,
            operator=log.operator,
            operatorId=log.operator_id,
            role=log.role,
            result=log.result,
            time=format_datetime(log.time),
            description=log.description,
            ip=log.ip,
            userAgent=log.user_agent,
            changes=log.changes,
            error=log.error,
            requestUrl=log.request_url,
            requestMethod=log.request_method,
            responseTime=log.response_time,
            targetId=log.target_id,
            targetType=log.target_type
        )
    )


@router.post("/export", summary="导出日志")
async def export_logs(
    export_request: LogExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.LOG_EXPORT.value))
):
    """导出日志文件为 CSV 格式"""
    query = select(OperationLog)
    
    # 应用筛选条件
    if export_request.filters:
        filters = export_request.filters
        
        if filters.get("operation"):
            query = query.where(OperationLog.operation == filters["operation"])
        
        if filters.get("result"):
            query = query.where(OperationLog.result == filters["result"])
        
        if filters.get("startTime"):
            query = query.where(OperationLog.time >= filters["startTime"])
        
        if filters.get("endTime"):
            query = query.where(OperationLog.time <= filters["endTime"])
        
        if filters.get("module"):
            query = query.where(OperationLog.module == filters["module"])
    
    # 查询所有符合条件的日志
    query = query.order_by(OperationLog.time.desc())
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # 创建CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow([
        "日志ID", "操作类型", "操作模块", "操作人", "角色", 
        "结果", "时间", "描述", "IP地址"
    ])
    
    # 写入数据
    operation_map = {
        "create": "创建",
        "update": "更新",
        "delete": "删除",
        "upload": "上传",
        "bind": "绑定",
        "unbind": "解绑",
        "publish": "发布",
        "unpublish": "下架",
        "apply": "应用",
        "recall": "撤回",
        "submit": "提交审批",
        "approve": "审批通过",
        "reject": "驳回"
    }
    
    result_map = {
        "success": "成功",
        "failed": "失败"
    }
    
    for log in logs:
        writer.writerow([
            log.id,
            operation_map.get(log.operation, log.operation),
            log.module,
            log.operator,
            log.role or "",
            result_map.get(log.result, log.result),
            format_datetime(log.time),
            log.description or "",
            log.ip or ""
        ])
    
    # 生成CSV文件
    csv_content = output.getvalue().encode('utf-8-sig')  # 使用 UTF-8 BOM 以便 Excel 正确显示中文
    output.close()
    
    # 生成文件名
    from datetime import datetime
    filename = f"logs_{datetime.now().strftime('%Y%m%d')}.csv"
    
    # 返回文件流
    return FastAPIResponse(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
