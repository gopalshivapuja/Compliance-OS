"""
Tag model for categorizing evidence and other resources
"""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin, TenantScopedMixin, AuditMixin


class Tag(Base, UUIDMixin, TenantScopedMixin, AuditMixin):
    """Tag model for organizing evidence"""

    __tablename__ = "tags"

    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag_name = Column(String(100), nullable=False, index=True)
    tag_color = Column(String(7), nullable=True)  # Hex color code, e.g., #FF5733

    # Relationships
    evidence = relationship("Evidence", secondary="evidence_tag_mappings", back_populates="tags")

    def __repr__(self):
        return f"<Tag {self.tag_name}>"
