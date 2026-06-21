"""
包管理模型（AutoUnit包和驱动包）
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Enum, DateTime, BigInteger, JSON
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
    status = Column(
        Enum("published", "unpublished", "testing"),
        nullable=False,
        default="unpublished",
        index=True
    )
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


class DriverPackage(Base):
    """驱动包表"""
    __tablename__ = "driver_packages"
    
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    type = Column(Enum("java", "python", "cpp"), nullable=False, index=True)
    version = Column(String(64), nullable=False)
    size = Column(BigInteger, nullable=False)
    file_path = Column(String(512), nullable=False)
    status = Column(
        Enum("published", "unpublished", "testing"),
        nullable=False,
        default="unpublished",
        index=True
    )
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

