"""
部署清单模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, BigInteger
from app.core.database import Base


class DeploymentManifest(Base):
    """部署清单表"""
    __tablename__ = "deployment_manifests"
    
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    file_name = Column(String(255), nullable=False)
    version = Column(String(64))
    size = Column(BigInteger, nullable=False)
    file_path = Column(String(512), nullable=False)
    content = Column(Text)  # TOML文件内容
    md5 = Column(String(64), nullable=False)
    upload_user_id = Column(String(64), nullable=False, index=True)
    upload_time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    update_time = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

