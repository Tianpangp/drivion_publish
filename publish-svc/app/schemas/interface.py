"""
界面管理相关 schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class InterfaceUpdateInfo(BaseModel):
    """更新界面基本信息"""
    name: Optional[str] = Field(None, description="界面名称")
    description: Optional[str] = Field(None, description="界面描述")
    stationIds: Optional[List[str]] = Field(None, description="绑定的工位ID列表")


class StationInfo(BaseModel):
    """工位信息"""
    id: str
    name: str
    code: Optional[str] = None
    path: Optional[str] = None


class InterfaceResponse(BaseModel):
    """界面响应"""
    id: str
    name: str
    description: Optional[str] = None
    jsonFilePath: Optional[str] = Field(None, description="JSON文件路径")
    fileSize: Optional[int] = Field(None, description="文件大小（字节）")
    fileMd5: Optional[str] = Field(None, description="文件MD5值")
    thumbnail: Optional[str] = None
    boundStations: List[StationInfo] = []
    createTime: str
    updateTime: str
    createUser: str
    
    class Config:
        from_attributes = True


class InterfaceDetailResponse(InterfaceResponse):
    """界面详情响应"""
    lastEditUser: Optional[str] = None

