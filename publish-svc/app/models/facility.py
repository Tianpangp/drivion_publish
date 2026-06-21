"""
设施管理模型（厂区/线体/工位）
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Enum, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Factory(Base):
    """厂区表"""
    __tablename__ = "factories"
    
    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False, index=True)
    code = Column(String(64), unique=True, index=True)
    description = Column(Text)
    location = Column(String(255))
    status = Column(Enum("active", "inactive"), nullable=False, default="active", index=True)
    is_deleted = Column(Integer, nullable=False, default=0, index=True)
    create_user_id = Column(String(64), nullable=False, index=True)
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    update_time = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    lines = relationship("Line", back_populates="factory")


class Line(Base):
    """线体表"""
    __tablename__ = "lines"
    
    id = Column(String(64), primary_key=True)
    factory_id = Column(String(64), ForeignKey("factories.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False, index=True)
    code = Column(String(64), unique=True, index=True)
    description = Column(Text)
    status = Column(Enum("active", "inactive"), nullable=False, default="active", index=True)
    is_deleted = Column(Integer, nullable=False, default=0, index=True)
    create_user_id = Column(String(64), nullable=False, index=True)
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    update_time = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    factory = relationship("Factory", back_populates="lines")
    stations = relationship("Station", back_populates="line")


class Station(Base):
    """工位表"""
    __tablename__ = "stations"
    
    id = Column(String(64), primary_key=True)
    line_id = Column(String(64), ForeignKey("lines.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False, index=True)
    code = Column(String(64), unique=True, index=True)
    description = Column(Text)
    ip = Column(String(64))
    mac = Column(String(64))
    status = Column(Enum("active", "inactive"), nullable=False, default="active", index=True)
    is_deleted = Column(Integer, nullable=False, default=0, index=True)
    create_user_id = Column(String(64), nullable=False, index=True)
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    update_time = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    line = relationship("Line", back_populates="stations")

