"""
用户相关模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Enum, DateTime, BigInteger, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(String(64), primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    nickname = Column(String(128))
    email = Column(String(128), unique=True, index=True)
    avatar = Column(String(512))
    role = Column(BigInteger, ForeignKey("roles.id"), nullable=False, comment="角色，参看roles表")
    status = Column(Enum("active", "inactive"), nullable=False, default="active")
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    update_time = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    role_relation = relationship("Role", back_populates="users")


class Role(Base):
    """角色表"""
    __tablename__ = "roles"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True, comment="角色代码")
    name = Column(String(100), nullable=False, comment="角色名称（中文）")
    name_en = Column(String(100), nullable=False, comment="角色名称（英文）")
    description = Column(String(255), comment="角色描述")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关系
    users = relationship("User", back_populates="role_relation")


class RoleRequest(Base):
    """用户角色申请。"""
    __tablename__ = "role_requests"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    current_role = Column(String(50), nullable=False)
    requested_role = Column(String(50), nullable=False)
    reason = Column(Text)
    status = Column(String(20), nullable=False, default="pending", index=True)
    reviewer_id = Column(String(64))
    review_comment = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    reviewed_at = Column(DateTime)
