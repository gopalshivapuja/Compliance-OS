"""
Role model for RBAC (Role-Based Access Control)
"""
from sqlalchemy import Column, String, Text, Table, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin, AuditMixin


# Junction table for many-to-many relationship between users and roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),  # Denormalized for performance
)


class Role(Base, UUIDMixin, AuditMixin):
    """Role model for user permissions"""

    __tablename__ = "roles"

    role_code = Column(String(50), unique=True, nullable=False, index=True)
    role_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_system_role = Column(String(10), nullable=False, default="no")  # yes/no - system roles cannot be deleted

    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")

    def __repr__(self):
        return f"<Role {self.role_code}: {self.role_name}>"
