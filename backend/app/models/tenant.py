"""
Tenant model for multi-tenant isolation
"""

from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin, AuditMixin


class Tenant(Base, UUIDMixin, AuditMixin):
    """Tenant model - each organization using Compliance OS"""

    __tablename__ = "tenants"

    tenant_code = Column(String(50), unique=True, nullable=False, index=True)
    tenant_name = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="active", index=True)  # active, suspended, inactive
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    meta_data = Column(JSONB, nullable=True)  # Flexible tenant-specific configs

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    entities = relationship("Entity", back_populates="tenant", cascade="all, delete-orphan")
    compliance_masters = relationship("ComplianceMaster", back_populates="tenant")
    compliance_instances = relationship("ComplianceInstance", back_populates="tenant")

    def __repr__(self):
        return f"<Tenant {self.tenant_code}: {self.tenant_name}>"
