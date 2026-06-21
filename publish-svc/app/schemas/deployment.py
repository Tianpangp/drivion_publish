"""
部署清单管理相关 schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class StationInfo(BaseModel):
    """工位信息"""
    id: str
    name: str
    code: Optional[str] = None
    path: Optional[str] = None


class DeploymentManifestResponse(BaseModel):
    """部署清单响应"""
    id: str
    name: str
    description: Optional[str] = None
    fileName: str
    version: Optional[str] = None
    size: int
    uploadTime: str
    uploadUser: str
    boundStations: List[StationInfo] = []
    md5: str
    
    class Config:
        from_attributes = True


class DeploymentManifestDetailResponse(DeploymentManifestResponse):
    """部署清单详情响应"""
    content: Optional[str] = None
    downloadCount: int = 0


class DeploymentManifestUpdate(BaseModel):
    """更新部署清单信息"""
    name: Optional[str] = Field(None, description="清单名称")
    description: Optional[str] = Field(None, description="清单描述")
    version: Optional[str] = Field(None, description="版本号")


class DeploymentManifestBind(BaseModel):
    """绑定部署清单到工位"""
    stationIds: List[str] = Field(..., description="工位ID列表")


class DeploymentManifestBindResponse(BaseModel):
    """绑定响应"""
    manifestId: str
    manifestName: str
    boundStations: List[StationInfo]
    bindTime: str

