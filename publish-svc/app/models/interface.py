"""
界面管理模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, BigInteger, Integer, Boolean
from app.core.database import Base


class Interface(Base):
    """界面表"""
    __tablename__ = "interfaces"
    
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    json_file_path = Column(String(512))  # JSON文件在MinIO中的存储路径
    file_size = Column(BigInteger)  # JSON文件大小（字节）
    file_md5 = Column(String(32))  # JSON文件MD5值
    thumbnail = Column(String(512))
    create_user = Column(String(64), nullable=False, index=True)  # 数据库字段名
    last_edit_user = Column(String(64))  # 数据库字段名
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    update_time = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)

