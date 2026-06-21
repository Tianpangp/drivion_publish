"""
日志管理相关 schemas
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class OperationLogResponse(BaseModel):
    """操作日志响应"""
    id: str
    operation: str
    module: str
    operator: str
    operatorId: str
    role: Optional[str] = None
    result: str
    time: str
    description: Optional[str] = None
    ip: Optional[str] = None
    userAgent: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    class Config:
        from_attributes = True


class OperationLogDetailResponse(OperationLogResponse):
    """操作日志详情响应"""
    requestUrl: Optional[str] = None
    requestMethod: Optional[str] = None
    responseTime: Optional[int] = None
    targetId: Optional[str] = None
    targetType: Optional[str] = None


class LogExportRequest(BaseModel):
    """日志导出请求"""
    filters: Optional[Dict[str, Any]] = Field(None, description="筛选条件")

