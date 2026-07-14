"""SSO BFF 服务端会话模型。"""
from datetime import datetime

from sqlalchemy import Column, DateTime, JSON, String, Text

from app.core.database import Base


class SsoAuthTransaction(Base):
    __tablename__ = "sso_auth_transactions"

    id = Column(String(64), primary_key=True)
    state = Column(String(128), nullable=False, unique=True, index=True)
    nonce = Column(String(128), nullable=False)
    code_verifier = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)


class SsoSession(Base):
    __tablename__ = "sso_sessions"

    id = Column(String(64), primary_key=True)
    subject = Column(String(128), nullable=False, index=True)
    username = Column(String(128), nullable=False)
    nickname = Column(String(128))
    email = Column(String(256))
    roles = Column(JSON, nullable=False, default=list)
    permissions = Column(JSON, nullable=False, default=list)
    permission_grants = Column(JSON, nullable=False, default=list)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    access_expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
