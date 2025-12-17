"""
Compliance Instance model - time-bound occurrences of compliance obligations
"""
from sqlalchemy import Column, String, Text, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin, TenantScopedMixin, AuditMixin


class ComplianceInstance(Base, UUIDMixin, TenantScopedMixin, AuditMixin):
    """Compliance Instance - actual occurrence of a compliance for a specific entity and period"""

    __tablename__ = "compliance_instances"

    # Denormalized tenant_id for performance (avoids join with entities)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # References
    compliance_master_id = Column(
        UUID(as_uuid=True), ForeignKey("compliance_masters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)

    # Time period
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=False, index=True)

    # Status tracking
    status = Column(String(50), nullable=False, default="Not Started", index=True)
    # Not Started, In Progress, Review, Pending Approval, Filed, Completed, Blocked, Overdue
    rag_status = Column(String(10), nullable=False, default="Green", index=True)  # Green, Amber, Red

    # Ownership
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    approver_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Dependency tracking (blocking instance)
    blocking_compliance_instance_id = Column(
        UUID(as_uuid=True), ForeignKey("compliance_instances.id", ondelete="SET NULL"), nullable=True
    )

    # Completion tracking
    filed_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    completion_remarks = Column(Text, nullable=True)

    # Additional fields
    remarks = Column(Text, nullable=True)
    meta_data = Column(JSONB, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="compliance_instances")
    compliance_master = relationship("ComplianceMaster", back_populates="compliance_instances")
    entity = relationship("Entity", back_populates="compliance_instances")
    owner = relationship("User", foreign_keys=[owner_user_id])
    approver = relationship("User", foreign_keys=[approver_user_id])

    # Self-referential for blocking dependencies
    blocking_instance = relationship("ComplianceInstance", remote_side="ComplianceInstance.id", foreign_keys=[blocking_compliance_instance_id])

    # Child relationships
    workflow_tasks = relationship("WorkflowTask", back_populates="compliance_instance", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="compliance_instance", cascade="all, delete-orphan")

    # Composite indexes for common queries
    __table_args__ = (
        # Unique constraint: one instance per master + entity + period
        Index(
            "idx_compliance_instances_unique",
            "compliance_master_id",
            "entity_id",
            "period_start",
            "period_end",
            unique=True,
        ),
        # Composite index for dashboard queries
        Index("idx_compliance_instances_tenant_status_due", "tenant_id", "status", "rag_status", "due_date"),
        # Index for entity-based queries
        Index("idx_compliance_instances_entity_status", "entity_id", "status", "due_date"),
    )

    def __repr__(self):
        return f"<ComplianceInstance {self.compliance_master.compliance_code if self.compliance_master else 'N/A'} - {self.entity.entity_code if self.entity else 'N/A'}: {self.status}>"
