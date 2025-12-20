"""Business logic services"""

from app.services.audit_service import log_action, get_audit_logs, get_resource_audit_trail
from app.services.entity_access_service import (
    check_entity_access,
    get_user_accessible_entities,
    grant_entity_access,
    revoke_entity_access,
    check_role_permission,
    get_user_roles,
    get_entity_users,
)

__all__ = [
    # Audit service
    "log_action",
    "get_audit_logs",
    "get_resource_audit_trail",
    # Entity access service
    "check_entity_access",
    "get_user_accessible_entities",
    "grant_entity_access",
    "revoke_entity_access",
    "check_role_permission",
    "get_user_roles",
    "get_entity_users",
]
