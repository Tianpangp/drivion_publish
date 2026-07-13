"""发布审批与设备绑定模型。"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.core.database import Base


class EquipmentAutoUnitBinding(Base):
    __tablename__ = "equipment_autounit_bindings"

    id = Column(String(64), primary_key=True)
    equipment_id = Column(String(64), ForeignKey("equipment.id"), nullable=False, unique=True, index=True)
    package_id = Column(String(64), ForeignKey("autounit_packages.id"), nullable=False, index=True)
    bind_user_id = Column(String(64), nullable=False)
    bind_time = Column(DateTime, nullable=False, default=datetime.utcnow)


class EquipmentBindingHistory(Base):
    __tablename__ = "equipment_binding_history"

    id = Column(String(64), primary_key=True)
    equipment_id = Column(String(64), ForeignKey("equipment.id"), nullable=False, index=True)
    package_id = Column(String(64), index=True)
    package_name = Column(String(255))
    package_version = Column(String(64))
    operation = Column(String(32), nullable=False)
    operator_id = Column(String(64), nullable=False)
    operation_time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class PublishApproval(Base):
    __tablename__ = "publish_approvals"

    id = Column(String(64), primary_key=True)
    target_id = Column(String(64), nullable=False, index=True)
    target_kind = Column(String(32), nullable=False, index=True)
    artifact_type = Column(String(32), nullable=False, index=True)
    action = Column(String(32), nullable=False)
    approve_status = Column(String(32), nullable=False)
    reject_status = Column(String(32), nullable=False)
    applicant_id = Column(String(64), nullable=False)
    applicant = Column(String(128), nullable=False)
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    status = Column(String(32), nullable=False, default="pending", index=True)
    reviewer_id = Column(String(64))
    reviewed_at = Column(DateTime)
    comment = Column(Text)
