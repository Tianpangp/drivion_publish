"""
日志模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, JSON
from app.core.database import Base


class OperationLog(Base):
    """操作日志表"""
    __tablename__ = "operation_logs"
    
    id = Column(String(64), primary_key=True)
    operation = Column(String(32), nullable=False, index=True)
    module = Column(String(64), nullable=False, index=True)
    operator_id = Column(String(64), nullable=False, index=True)
    operator = Column(String(128), nullable=False)
    role = Column(String(64))
    result = Column(String(16), nullable=False, index=True)
    time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    description = Column(Text)
    ip = Column(String(64))
    user_agent = Column(String(512))
    changes = Column(JSON)  # 变更详情
    error = Column(Text)
    request_url = Column(String(512))
    request_method = Column(String(16))
    response_time = Column(Integer)  # 响应时间（毫秒）
    target_id = Column(String(64), index=True)
    target_type = Column(String(64), index=True)
