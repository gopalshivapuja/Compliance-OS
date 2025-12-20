"""
User model for authentication and authorization
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
from app.models.base import Base, UUIDMixin, TenantScopedMixin, AuditMixin
from app.models.role import user_roles

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base, UUIDMixin, TenantScopedMixin, AuditMixin):
    """User model with authentication and RBAC"""

    __tablename__ = "users"

    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=True)
    status = Column(
        String(20), nullable=False, default="active", index=True
    )  # active, inactive, suspended
    last_login_at = Column(DateTime, nullable=True)
    is_system_admin = Column(Boolean, default=False, nullable=False, index=True)  # Super user flag

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    accessible_entities = relationship(
        "Entity", secondary="entity_access", back_populates="users_with_access"
    )

    # Tasks assigned to this user
    assigned_tasks = relationship(
        "WorkflowTask",
        foreign_keys="[WorkflowTask.assigned_to_user_id]",
        back_populates="assigned_user",
    )

    # Audit trail - actions created/updated by this user
    created_audit_logs = relationship(
        "AuditLog", foreign_keys="[AuditLog.user_id]", back_populates="user"
    )

    def set_password(self, password: str):
        """Hash and set password"""
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(password, self.password_hash)

    @property
    def full_name(self) -> str:
        """Return full name"""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<User {self.email}: {self.full_name}>"
