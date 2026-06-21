"""
通用 schemas
"""
from typing import TypeVar, Generic, Optional, List, Any
from pydantic import BaseModel

T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    """统一响应格式"""
    code: int = 200
    message: str = "操作成功"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    list: List[T]
    total: int
    page: int
    pageSize: int
    totalPages: Optional[int] = None

