"""
Compliance Master model - templates/definitions of compliance obligations
"""
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin, AuditMixin


class ComplianceMaster(Base, UUIDMixin, AuditMixin):
    """Compliance Master - template for compliance obligations"""

    __tablename__ = "compliance_masters"

    # Can be NULL for system-wide templates, or set for tenant-specific customizations
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)

    compliance_code = Column(String(100), nullable=False, index=True)
    compliance_name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Categorization
    category = Column(String(50), nullable=False, index=True)  # GST, Direct Tax, Payroll, MCA, FEMA, FP&A
    sub_category = Column(String(100), nullable=True)

    # Frequency and timing
    frequency = Column(String(50), nullable=False, index=True)  # Monthly, Quarterly, Annual, Event-based
    due_date_rule = Column(JSONB, nullable=False)  # Flexible rule engine for due date calculation
    # Example: {"type": "monthly", "day": 11, "offset_days": 0}

    # Ownership and approval
    owner_role_code = Column(String(50), nullable=True)  # Default owner role
    approver_role_code = Column(String(50), nullable=True)  # Default approver role

    # Dependencies
    dependencies = Column(JSONB, nullable=True)  # Array of compliance codes this depends on
    # Example: ["GSTR-1", "GSTR-3B"]

    # Workflow configuration
    workflow_config = Column(JSONB, nullable=True)  # Custom workflow steps if not using standard
    # Example: [{"step": "Prepare", "role": "Tax Lead"}, {"step": "Review", "role": "Manager"}, ...]

    # Status and flags
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_template = Column(Boolean, default=False, nullable=False)  # System-wide template vs tenant-specific

    # Metadata
    authority = Column(String(255), nullable=True)  # Regulatory authority (CBIC, Income Tax Dept, etc.)
    penalty_details = Column(Text, nullable=True)
    reference_links = Column(JSONB, nullable=True)  # Array of URLs
    meta_data = Column(JSONB, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="compliance_masters")
    compliance_instances = relationship("ComplianceInstance", back_populates="compliance_master", cascade="all, delete-orphan")

    # Composite index for uniqueness within tenant
    __table_args__ = (
        Index("idx_compliance_masters_tenant_code", "tenant_id", "compliance_code", unique=True),
    )

    def __repr__(self):
        return f"<ComplianceMaster {self.compliance_code}: {self.compliance_name}>"
