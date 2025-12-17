"""
Entity model for legal entities (companies, branches)
"""
from sqlalchemy import Column, String, Text, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin, TenantScopedMixin, AuditMixin


# Junction table for many-to-many relationship between users and entities (access control)
entity_access = Table(
    "entity_access",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("entity_id", UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True),
    Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),  # Denormalized for performance
)


class Entity(Base, UUIDMixin, TenantScopedMixin, AuditMixin):
    """Entity model - legal entities within a tenant"""

    __tablename__ = "entities"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_code = Column(String(50), nullable=False, index=True)
    entity_name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)  # Company, Branch, LLP, etc.

    # Indian tax identifiers
    pan = Column(String(10), nullable=True, index=True)
    gstin = Column(String(15), nullable=True, index=True)
    cin = Column(String(21), nullable=True)
    tan = Column(String(10), nullable=True)

    # Contact details
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    contact_person = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)

    status = Column(String(20), nullable=False, default="active", index=True)  # active, inactive
    meta_data = Column(JSONB, nullable=True)  # Flexible entity-specific data

    # Relationships
    tenant = relationship("Tenant", back_populates="entities")
    users_with_access = relationship("User", secondary=entity_access, back_populates="accessible_entities")
    compliance_instances = relationship("ComplianceInstance", back_populates="entity", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Entity {self.entity_code}: {self.entity_name}>"
