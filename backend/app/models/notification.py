"""
Notification model for in-app notifications
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base, UUIDMixin, TenantScopedMixin


class Notification(Base, UUIDMixin, TenantScopedMixin):
    """Notification model for in-app notifications"""

    __tablename__ = "notifications"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Who should see this notification
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Notification details
    notification_type = Column(String(50), nullable=False, index=True)
    # task_assigned, approval_request, overdue_alert, escalation, etc.

    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(500), nullable=True)  # Link to related resource

    # Status
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User")

    # Indexes for queries
    __table_args__ = (Index("idx_notifications_user_read", "user_id", "is_read", "created_at"),)

    def __repr__(self):
        return f"<Notification {self.notification_type} for User {self.user_id}: {self.title}>"
