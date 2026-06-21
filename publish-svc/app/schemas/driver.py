"""
驱动包管理相关 schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field


# ============ 驱动包 ============

class DriverPackageUpload(BaseModel):
    """上传驱动包请求"""
    name: str = Field(..., description="驱动名称")
    type: str = Field(..., description="驱动类型：java/python/cpp")
    version: str = Field(..., description="版本号")
    description: Optional[str] = Field(None, description="驱动描述")
    protocol: Optional[str] = Field(None, description="支持的协议")
    manufacturer: Optional[str] = Field(None, description="设备厂商")
    deviceModel: Optional[str] = Field(None, description="设备型号")


class StationInfo(BaseModel):
    """工位信息"""
    id: str
    name: str
    code: Optional[str] = None


class DriverPackageResponse(BaseModel):
    """驱动包响应"""
    id: str
    name: str
    fileName: str
    type: str
    version: str
    size: int
    uploadTime: str
    uploadUser: str
    status: str
    description: Optional[str] = None
    boundStations: List[StationInfo] = []
    protocol: Optional[str] = None
    manufacturer: Optional[str] = None
    deviceModel: Optional[str] = None
    md5: str
    
    class Config:
        from_attributes = True


class DriverPackageDetailResponse(DriverPackageResponse):
    """驱动包详情响应"""
    publishTime: Optional[str] = None
    unpublishTime: Optional[str] = None
    supportedPlatforms: Optional[List[str]] = None
    apiDocUrl: Optional[str] = None
    readme: Optional[str] = None
    sha256: Optional[str] = None

