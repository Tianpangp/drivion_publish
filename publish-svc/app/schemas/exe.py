"""
Exe 拉取发布包相关 schemas
"""
from typing import Any, Optional, List
from pydantic import BaseModel, Field


class ExeStationInfo(BaseModel):
    """工位基础信息"""
    id: str
    name: str
    code: Optional[str] = None
    path: Optional[str] = None
    ip: Optional[str] = None
    mac: Optional[str] = None


class ExeArtifactInfo(BaseModel):
    """Exe 可拉取制品信息"""
    id: str
    name: str
    version: Optional[str] = None
    fileName: Optional[str] = None
    size: Optional[int] = None
    md5: Optional[str] = None
    sha256: Optional[str] = None
    status: Optional[str] = None
    downloadApiPath: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExeDeploymentManifestInfo(ExeArtifactInfo):
    """部署清单信息"""
    content: Optional[str] = None


class ExeBundleResponse(BaseModel):
    """按工位聚合的 Exe 拉取包"""
    station: ExeStationInfo
    manifest: Optional[ExeDeploymentManifestInfo] = None
    autoUnits: List[ExeArtifactInfo] = Field(default_factory=list)
    drivers: List[ExeArtifactInfo] = Field(default_factory=list)
    interfaces: List[ExeArtifactInfo] = Field(default_factory=list)
    generatedAt: str
    warnings: List[str] = Field(default_factory=list)


class ExeEquipmentInfo(BaseModel):
    id: str
    name: str
    code: Optional[str] = None
    status: str
    equipmentType: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    station: dict[str, Any]
    line: dict[str, Any]
    site: dict[str, Any]


class ExeAutoUnitInfo(ExeArtifactInfo):
    packageId: str
    module: str
    published: bool
    releaseWarning: Optional[str] = None


class ExeEquipmentDeployment(BaseModel):
    equipment: ExeEquipmentInfo
    autoUnit: Optional[ExeAutoUnitInfo] = None
    boundAt: Optional[str] = None
    revision: str
    generatedAt: str
