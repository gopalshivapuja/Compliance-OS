"""
Audit Service
Handles immutable audit logging for all system actions.

Core principle: "If it cannot stand up to an auditor, it does not ship."
"""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Dict, Any, Union
from uuid import UUID

from app.models.audit_log import AuditLog


async def log_action(
    db: Session,
    tenant_id: Union[str, UUID],
    user_id: Union[str, UUID],
    action_type: str,
    resource_type: str,
    resource_id: Union[str, UUID],
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    change_summary: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """
    Log an action to the immutable audit trail.

    Args:
        db: Database session
        tenant_id: Tenant ID for multi-tenant isolation
        user_id: User who performed the action
        action_type: Type of action (CREATE, UPDATE, DELETE, LOGIN, LOGOUT, APPROVE, REJECT)
        resource_type: Type of resource affected (user, compliance_instance, evidence, etc.)
        resource_id: ID of the affected resource
        old_values: Before state (for UPDATE actions)
        new_values: After state (for CREATE/UPDATE actions)
        change_summary: Human-readable summary of the change
        ip_address: IP address of the request
        user_agent: User agent of the request

    Returns:
        AuditLog: The created audit log entry

    Raises:
        SQLAlchemyError: If database operation fails

    Example:
        >>> await log_action(
        ...     db=db,
        ...     tenant_id="tenant-123",
        ...     user_id="user-456",
        ...     action_type="UPDATE",
        ...     resource_type="compliance_instance",
        ...     resource_id="instance-789",
        ...     old_values={"status": "Not Started"},
        ...     new_values={"status": "In Progress"},
        ...     change_summary="Updated status from Not Started to In Progress",
        ...     ip_address="192.168.1.1",
        ...     user_agent="Mozilla/5.0..."
        ... )
    """
    try:
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            change_summary=change_summary or f"{action_type} on {resource_type}",
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
        )

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        return audit_log

    except SQLAlchemyError as e:
        db.rollback()
        raise e


def get_audit_logs(
    db: Session,
    tenant_id: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    user_id: Optional[str] = None,
    action_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[AuditLog], int]:
    """
    Query audit logs with filters.

    Args:
        db: Database session
        tenant_id: Tenant ID for multi-tenant isolation
        resource_type: Filter by resource type (optional)
        resource_id: Filter by resource ID (optional)
        user_id: Filter by user who performed action (optional)
        action_type: Filter by action type (optional)
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        tuple: (list of audit logs, total count)
    """
    query = db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id)

    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    if resource_id:
        query = query.filter(AuditLog.resource_id == resource_id)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    if action_type:
        query = query.filter(AuditLog.action_type == action_type)

    # Order by most recent first
    query = query.order_by(AuditLog.created_at.desc())

    total = query.count()

    # Apply pagination
    logs = query.offset(skip).limit(limit).all()

    return logs, total


def get_resource_audit_trail(
    db: Session,
    tenant_id: str,
    resource_type: str,
    resource_id: str,
) -> list[AuditLog]:
    """
    Get complete audit trail for a specific resource.

    Args:
        db: Database session
        tenant_id: Tenant ID for multi-tenant isolation
        resource_type: Type of resource
        resource_id: ID of the resource

    Returns:
        list[AuditLog]: Complete audit history ordered chronologically
    """
    return (
        db.query(AuditLog)
        .filter(
            AuditLog.tenant_id == tenant_id,
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id,
        )
        .order_by(AuditLog.created_at.asc())
        .all()
    )
