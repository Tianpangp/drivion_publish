"""
包管理模型（AutoUnit包和驱动包）
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, BigInteger, JSON, Integer, Boolean, UniqueConstraint
from app.core.database import Base


class AutoUnitPackage(Base):
    """AutoUnit包表"""
    __tablename__ = "autounit_packages"
    
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    version = Column(String(64), nullable=False)
    size = Column(BigInteger, nullable=False)
    file_path = Column(String(512), nullable=False)
    package_id = Column(String(255), nullable=False, index=True)
    module = Column(String(512), nullable=False)
    status = Column(String(32), nullable=False, default="pending_testing", index=True)
    deleted = Column(Integer, nullable=False, default=0, index=True)
    locked = Column(Boolean, nullable=False, default=False)
    storage_provider = Column(String(32), nullable=False, default="local")
    download_count = Column(Integer, nullable=False, default=0)
    description = Column(Text)
    python_version = Column(String(32))
    dependencies = Column(JSON)  # Python依赖列表
    readme = Column(Text)
    changelog = Column(Text)
    md5 = Column(String(64), nullable=False)
    sha256 = Column(String(128))
    upload_user_id = Column(String(64), nullable=False, index=True)
    upload_time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    publish_user_id = Column(String(64))
    publish_time = Column(DateTime)
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    update_time = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("package_id", "version", name="uq_autounit_package_version"),)


class DriverPackage(Base):
    """驱动包表"""
    __tablename__ = "driver_packages"
    
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    type = Column(String(32), nullable=False, default="python", index=True)
    version = Column(String(64), nullable=False)
    size = Column(BigInteger, nullable=False)
    file_path = Column(String(512), nullable=False)
    status = Column(String(32), nullable=False, default="pending_testing", index=True)
    deleted = Column(Integer, nullable=False, default=0, index=True)
    locked = Column(Boolean, nullable=False, default=False)
    storage_provider = Column(String(32), nullable=False, default="local")
    download_count = Column(Integer, nullable=False, default=0)
    description = Column(Text)
    protocol = Column(String(128))
    manufacturer = Column(String(128))
    device_model = Column(String(128))
    supported_platforms = Column(JSON)  # 支持的平台列表
    api_doc_url = Column(String(512))
    readme = Column(Text)
    md5 = Column(String(64), nullable=False)
    sha256 = Column(String(128))
    upload_user_id = Column(String(64), nullable=False, index=True)
    upload_time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    publish_user_id = Column(String(64))
    publish_time = Column(DateTime)
    unpublish_user_id = Column(String(64))
    unpublish_time = Column(DateTime)
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    update_time = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("name", "version", name="uq_driver_package_version"),)
