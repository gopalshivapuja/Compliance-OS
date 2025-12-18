"""
Audit Log model for immutable audit trail
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base, UUIDMixin


class AuditLog(Base, UUIDMixin):
    """Audit Log - append-only immutable audit trail"""

    __tablename__ = "audit_logs"

    # Tenant scope (denormalized)
    tenant_id = Column(UUID(as_uuid=False), nullable=False, index=True)

    # Who performed the action
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # What was the action
    action_type = Column(
        String(50), nullable=False, index=True
    )  # CREATE, UPDATE, DELETE, APPROVE, REJECT, LOGIN, etc.

    # Which resource was affected
    resource_type = Column(
        String(100), nullable=False, index=True
    )  # compliance_instance, evidence, user, etc.
    resource_id = Column(UUID(as_uuid=False), nullable=True, index=True)

    # Before/after snapshots for UPDATE actions
    old_values = Column(JSONB, nullable=True)  # Snapshot before change
    new_values = Column(JSONB, nullable=True)  # Snapshot after change

    # Human-readable summary
    change_summary = Column(Text, nullable=True)

    # Context
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)

    # Timestamp (no updated_at - append-only)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="created_audit_logs")

    # Indexes for queries
    __table_args__ = (
        Index("idx_audit_logs_tenant_created", "tenant_id", "created_at"),
        Index("idx_audit_logs_resource", "resource_type", "resource_id", "created_at"),
        Index("idx_audit_logs_user_created", "user_id", "created_at"),
    )

    def __repr__(self):
        return f"<AuditLog {self.action_type} on {self.resource_type}:{self.resource_id}>"
