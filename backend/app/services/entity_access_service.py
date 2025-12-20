"""
Entity Access Control Service
Handles user permissions to entities and role-based access control (RBAC).
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from uuid import UUID

from app.models.entity import entity_access, Entity
from app.models.user import User
from app.models.role import Role


def check_entity_access(
    db: Session,
    user_id: UUID,
    entity_id: UUID,
    tenant_id: Optional[UUID] = None,
) -> bool:
    """
    Check if a user has access to a specific entity.

    Args:
        db: Database session
        user_id: User ID to check
        entity_id: Entity ID to check access for
        tenant_id: Optional tenant ID for additional validation

    Returns:
        bool: True if user has access, False otherwise

    Example:
        >>> has_access = check_entity_access(db, user_id="user-123", entity_id="entity-456")
        >>> if not has_access:
        ...     raise HTTPException(status_code=403, detail="Access denied to this entity")
    """
    # Query the entity_access junction table
    query = select(entity_access).where(
        entity_access.c.user_id == user_id,
        entity_access.c.entity_id == entity_id,
    )

    # Add tenant_id check if provided (multi-tenant isolation)
    if tenant_id:
        query = query.where(entity_access.c.tenant_id == tenant_id)

    result = db.execute(query).first()
    return result is not None


def get_user_accessible_entities(
    db: Session,
    user_id: UUID,
    tenant_id: UUID,
) -> List[UUID]:
    """
    Get list of entity IDs that a user has access to.

    Args:
        db: Database session
        user_id: User ID
        tenant_id: Tenant ID for multi-tenant isolation

    Returns:
        List[UUID]: List of entity IDs the user can access

    Example:
        >>> accessible_entities = get_user_accessible_entities(db, user_id, tenant_id)
        >>> query = query.filter(ComplianceInstance.entity_id.in_(accessible_entities))
    """
    # Query the entity_access junction table
    result = db.execute(
        select(entity_access.c.entity_id).where(
            entity_access.c.user_id == user_id,
            entity_access.c.tenant_id == tenant_id,
        )
    ).all()

    # Extract entity_ids from result tuples
    return [row[0] for row in result]


def check_role_permission(
    user_roles: List[str],
    required_roles: List[str],
) -> bool:
    """
    Check if user has any of the required roles.

    Args:
        user_roles: List of role names the user has
        required_roles: List of role names required for the action

    Returns:
        bool: True if user has at least one of the required roles

    Example:
        >>> user_roles = ["Tax Lead", "Payroll Manager"]
        >>> required_roles = ["CFO", "System Admin"]
        >>> can_approve = check_role_permission(user_roles, required_roles)
    """
    # Check if there's any overlap between user roles and required roles
    return bool(set(user_roles) & set(required_roles))


def get_user_roles(
    db: Session,
    user_id: UUID,
) -> List[str]:
    """
    Get list of role names for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List[str]: List of role names

    Example:
        >>> roles = get_user_roles(db, user_id)
        >>> if "CFO" in roles:
        ...     # Allow approval
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []

    return [role.role_name for role in user.roles]


def grant_entity_access(
    db: Session,
    user_id: UUID,
    entity_id: UUID,
    tenant_id: UUID,
) -> bool:
    """
    Grant a user access to an entity.

    Args:
        db: Database session
        user_id: User ID to grant access
        entity_id: Entity ID to grant access to
        tenant_id: Tenant ID for multi-tenant isolation

    Returns:
        bool: True if access was granted, False if already existed

    Example:
        >>> granted = grant_entity_access(db, user_id, entity_id, tenant_id)
        >>> if granted:
        ...     print("Access granted successfully")
    """
    # Check if access already exists
    if check_entity_access(db, user_id, entity_id, tenant_id):
        return False  # Already has access

    # Insert new access record
    db.execute(
        entity_access.insert().values(
            user_id=user_id,
            entity_id=entity_id,
            tenant_id=tenant_id,
        )
    )
    db.commit()
    return True


def revoke_entity_access(
    db: Session,
    user_id: UUID,
    entity_id: UUID,
) -> bool:
    """
    Revoke a user's access to an entity.

    Args:
        db: Database session
        user_id: User ID to revoke access
        entity_id: Entity ID to revoke access from

    Returns:
        bool: True if access was revoked, False if didn't exist

    Example:
        >>> revoked = revoke_entity_access(db, user_id, entity_id)
        >>> if revoked:
        ...     print("Access revoked successfully")
    """
    # Check if access exists
    if not check_entity_access(db, user_id, entity_id):
        return False  # No access to revoke

    # Delete access record
    db.execute(
        entity_access.delete().where(
            entity_access.c.user_id == user_id,
            entity_access.c.entity_id == entity_id,
        )
    )
    db.commit()
    return True


def get_entity_users(
    db: Session,
    entity_id: UUID,
    tenant_id: UUID,
) -> List[User]:
    """
    Get all users who have access to an entity.

    Args:
        db: Database session
        entity_id: Entity ID
        tenant_id: Tenant ID for multi-tenant isolation

    Returns:
        List[User]: List of users with access

    Example:
        >>> users = get_entity_users(db, entity_id, tenant_id)
        >>> for user in users:
        ...     print(f"{user.full_name} has access")
    """
    # Query users through the entity_access junction table
    result = db.execute(
        select(entity_access.c.user_id).where(
            entity_access.c.entity_id == entity_id,
            entity_access.c.tenant_id == tenant_id,
        )
    ).all()

    user_ids = [row[0] for row in result]

    # Fetch user objects
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    return users
