"""
AutoUnit 包管理相关 schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field


# ============ AutoUnit 包 ============

class AutoUnitPackageUpload(BaseModel):
    """上传 AutoUnit 包请求"""
    name: str = Field(..., description="包名称")
    version: str = Field(..., description="版本号")
    description: Optional[str] = Field(None, description="包描述")
    pythonVersion: Optional[str] = Field(None, description="Python版本要求")


class AutoUnitPackageUpdateStatus(BaseModel):
    """更新包状态请求"""
    status: str = Field(..., description="状态：published/unpublished/testing")


class StationInfo(BaseModel):
    """工位信息"""
    id: str
    name: str
    code: Optional[str] = None


class AutoUnitPackageResponse(BaseModel):
    """AutoUnit包响应"""
    id: str
    name: str
    fileName: str
    version: str
    size: int
    uploadTime: str
    uploadUser: str
    status: str
    description: Optional[str] = None
    boundStations: List[StationInfo] = []
    dependencies: Optional[List[str]] = None
    pythonVersion: Optional[str] = None
    md5: str
    sha256: Optional[str] = None
    
    class Config:
        from_attributes = True


class AutoUnitPackageDetailResponse(AutoUnitPackageResponse):
    """AutoUnit包详情响应"""
    publishTime: Optional[str] = None
    publishUser: Optional[str] = None
    readme: Optional[str] = None
    changelog: Optional[str] = None


class AutoUnitPackageApply(BaseModel):
    """应用AutoUnit包到工位"""
    stationIds: List[str] = Field(..., description="工位ID列表")


class AutoUnitPackageApplyResponse(BaseModel):
    """应用响应"""
    packageId: str
    packageName: str
    appliedStations: List[StationInfo]
    applyTime: str

