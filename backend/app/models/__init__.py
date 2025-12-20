"""
Models package - imports all models for Alembic discovery
"""

from app.models.base import Base

# Import all models so Alembic can discover them
from app.models.tenant import Tenant
from app.models.role import Role, user_roles
from app.models.user import User
from app.models.entity import Entity, entity_access
from app.models.compliance_master import ComplianceMaster
from app.models.compliance_instance import ComplianceInstance
from app.models.workflow_task import WorkflowTask
from app.models.tag import Tag
from app.models.evidence import Evidence, evidence_tag_mappings
from app.models.audit_log import AuditLog
from app.models.notification import Notification

__all__ = [
    "Base",
    "Tenant",
    "Role",
    "user_roles",
    "User",
    "Entity",
    "entity_access",
    "ComplianceMaster",
    "ComplianceInstance",
    "WorkflowTask",
    "Tag",
    "Evidence",
    "evidence_tag_mappings",
    "AuditLog",
    "Notification",
]
