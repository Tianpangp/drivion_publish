"""
设施管理相关 schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# ============ 基础模型 ============

class FacilityBase(BaseModel):
    """设施基础模型"""
    name: str = Field(..., description="名称")
    code: Optional[str] = Field(None, description="编号")
    description: Optional[str] = Field(None, description="描述")
    status: str = Field("active", description="状态：active-启用, inactive-停用")


# ============ 厂区 ============

class FactoryCreate(FacilityBase):
    """创建厂区请求"""
    location: Optional[str] = Field(None, description="地址")


class FactoryUpdate(BaseModel):
    """更新厂区请求"""
    name: Optional[str] = Field(None, description="名称")
    code: Optional[str] = Field(None, description="编号")
    description: Optional[str] = Field(None, description="描述")
    status: Optional[str] = Field(None, description="状态")
    location: Optional[str] = Field(None, description="地址")


class FactoryResponse(BaseModel):
    """厂区响应"""
    id: str
    name: str
    type: str = "factory"
    code: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: str
    createTime: str
    updateTime: str
    
    class Config:
        from_attributes = True


# ============ 线体 ============

class LineCreate(FacilityBase):
    """创建线体请求"""
    factoryId: str = Field(..., description="所属厂区ID")


class LineUpdate(BaseModel):
    """更新线体请求"""
    name: Optional[str] = Field(None, description="名称")
    code: Optional[str] = Field(None, description="编号")
    description: Optional[str] = Field(None, description="描述")
    status: Optional[str] = Field(None, description="状态")


class LineResponse(BaseModel):
    """线体响应"""
    id: str
    factoryId: str
    name: str
    type: str = "line"
    code: Optional[str] = None
    description: Optional[str] = None
    status: str
    createTime: str
    updateTime: str
    
    class Config:
        from_attributes = True


# ============ 工位 ============

class StationCreate(FacilityBase):
    """创建工位请求"""
    lineId: str = Field(..., description="所属线体ID")
    ip: Optional[str] = Field(None, description="工位设备IP")
    mac: Optional[str] = Field(None, description="工位设备MAC")


class StationUpdate(BaseModel):
    """更新工位请求"""
    name: Optional[str] = Field(None, description="名称")
    code: Optional[str] = Field(None, description="编号")
    description: Optional[str] = Field(None, description="描述")
    status: Optional[str] = Field(None, description="状态")
    ip: Optional[str] = Field(None, description="工位设备IP")
    mac: Optional[str] = Field(None, description="工位设备MAC")


class StationResponse(BaseModel):
    """工位响应"""
    id: str
    lineId: str
    name: str
    type: str = "station"
    code: Optional[str] = None
    description: Optional[str] = None
    ip: Optional[str] = None
    mac: Optional[str] = None
    status: str
    createTime: str
    updateTime: str
    
    class Config:
        from_attributes = True


# ============ 树形结构 ============

class StationTreeNode(StationResponse):
    """工位树节点"""
    pass


class LineTreeNode(LineResponse):
    """线体树节点"""
    children: List[StationTreeNode] = []


class FactoryTreeNode(FactoryResponse):
    """厂区树节点"""
    children: List[LineTreeNode] = []


# 树形结构响应
FacilityTree = List[FactoryTreeNode]


# ============ 工位搜索 ============

class StationSearchResponse(BaseModel):
    """工位搜索响应"""
    id: str
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    ip: Optional[str] = None
    mac: Optional[str] = None
    status: str
    path: str  # 完整路径：厂区 / 线体 / 工位
    factoryId: str
    factoryName: str
    lineId: str
    lineName: str
    createTime: str
    updateTime: str
    
    class Config:
        from_attributes = True
