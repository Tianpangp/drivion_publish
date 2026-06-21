"""
绑定关系相关 schemas
"""
from typing import List
from pydantic import BaseModel, Field


class InterfaceBindRequest(BaseModel):
    """绑定界面到工位请求"""
    interfaceId: str = Field(..., description="界面ID")
    stationIds: List[str] = Field(..., description="工位ID列表")


class InterfaceBindResponse(BaseModel):
    """绑定响应"""
    interfaceId: str
    interfaceName: str
    boundStations: List[dict]
    bindTime: str


class StationBindingsResponse(BaseModel):
    """工位绑定信息响应"""
    stationId: str
    stationName: str
    stationCode: str
    stationPath: str
    interfaces: List[dict] = []
    deploymentManifests: List[dict] = []
    autounitPackages: List[dict] = []

