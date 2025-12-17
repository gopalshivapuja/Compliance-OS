"""
Evidence model for audit-ready file storage
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, BigInteger, ForeignKey, Table, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin, TenantScopedMixin, AuditMixin


# Junction table for many-to-many relationship between evidence and tags
evidence_tag_mappings = Table(
    "evidence_tag_mappings",
    Base.metadata,
    Column("evidence_id", UUID(as_uuid=True), ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Evidence(Base, UUIDMixin, TenantScopedMixin, AuditMixin):
    """Evidence model - immutable file storage with versioning"""

    __tablename__ = "evidence"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Reference to compliance instance
    compliance_instance_id = Column(
        UUID(as_uuid=True), ForeignKey("compliance_instances.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # File details
    evidence_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # S3 path or local file path
    file_type = Column(String(100), nullable=True)  # PDF, PNG, XLSX, etc.
    file_size = Column(BigInteger, nullable=True)  # Size in bytes
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash for integrity

    # Versioning
    version = Column(Integer, nullable=False, default=1)
    parent_evidence_id = Column(
        UUID(as_uuid=True), ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True
    )  # Points to previous version

    # Approval workflow
    approval_status = Column(String(50), nullable=False, default="Pending", index=True)  # Pending, Approved, Rejected
    approved_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(UUID(as_uuid=True), nullable=True)  # Should be DateTime, but keeping consistent
    approval_remarks = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Immutability flag
    is_immutable = Column(Boolean, default=False, nullable=False)  # Once approved, cannot be deleted

    # Metadata
    description = Column(Text, nullable=True)
    meta_data = Column(JSONB, nullable=True)

    # Relationships
    compliance_instance = relationship("ComplianceInstance", back_populates="evidence")
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    tags = relationship("Tag", secondary=evidence_tag_mappings, back_populates="evidence")

    # Self-referential for versioning
    parent_evidence = relationship("Evidence", remote_side="Evidence.id", foreign_keys=[parent_evidence_id], backref="versions")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_evidence_compliance_status", "compliance_instance_id", "approval_status"),
        Index("idx_evidence_hash", "file_hash"),
    )

    def __repr__(self):
        return f"<Evidence {self.evidence_name} v{self.version}: {self.approval_status}>"
