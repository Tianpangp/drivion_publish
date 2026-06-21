"""
绑定关系模型
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from app.core.database import Base


class AutoUnitStationApplication(Base):
    """AutoUnit包与工位应用关系表"""
    __tablename__ = "autounit_station_applications"
    
    id = Column(String(64), primary_key=True)
    package_id = Column(String(64), ForeignKey("autounit_packages.id"), nullable=False, index=True)
    station_id = Column(String(64), ForeignKey("stations.id"), nullable=False, index=True)
    apply_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    apply_user_id = Column(String(64))


class InterfaceStationBinding(Base):
    """界面与工位绑定关系表"""
    __tablename__ = "interface_station_bindings"
    
    id = Column(String(64), primary_key=True)
    interface_id = Column(String(64), ForeignKey("interfaces.id"), nullable=False, index=True)
    station_id = Column(String(64), ForeignKey("stations.id"), nullable=False, index=True)
    bind_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    bind_user_id = Column(String(64))


class ManifestStationBinding(Base):
    """部署清单与工位绑定关系表"""
    __tablename__ = "manifest_station_bindings"
    
    id = Column(String(64), primary_key=True)
    manifest_id = Column(String(64), ForeignKey("deployment_manifests.id"), nullable=False, index=True)
    station_id = Column(String(64), ForeignKey("stations.id"), nullable=False, index=True)
    bind_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    bind_user_id = Column(String(64))

