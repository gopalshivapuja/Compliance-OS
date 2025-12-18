"""
Audit Log endpoints - Read-only, CFO and System Admin access only
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_tenant_id, get_current_user
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import (
    AuditLogResponse,
    AuditLogListResponse,
    ResourceAuditTrailResponse,
)
from app.services.entity_access_service import check_role_permission
from app.services.audit_service import get_audit_logs, get_resource_audit_trail

router = APIRouter()


@router.get("/", response_model=AuditLogListResponse)
async def list_audit_logs(
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    List audit logs for current tenant (read-only).
    **RBAC**: Only CFO and System Admin can access audit logs.
    """
    # Check role permission (RBAC)
    user_roles = current_user.get("roles", [])
    if not check_role_permission(user_roles, ["CFO", "System Admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only CFO and System Admin can view audit logs.",
        )

    # Use audit service to query logs
    logs, total = get_audit_logs(
        db=db,
        tenant_id=tenant_id,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        action_type=action_type,
        skip=skip,
        limit=limit,
    )

    # Convert to response models with denormalized user info
    items = []
    for log in logs:
        # Get user info
        user = db.query(User).filter(User.id == log.user_id).first()

        items.append(
            AuditLogResponse(
                audit_log_id=str(log.id),
                tenant_id=str(log.tenant_id),
                user_id=str(log.user_id),
                user_name=user.full_name if user else None,
                user_email=user.email if user else None,
                action_type=log.action_type,
                resource_type=log.resource_type,
                resource_id=str(log.resource_id),
                old_values=log.old_values,
                new_values=log.new_values,
                change_summary=log.change_summary,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
            )
        )

    return AuditLogListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/resource/{resource_type}/{resource_id}", response_model=ResourceAuditTrailResponse)
async def get_resource_audit_trail_endpoint(
    resource_type: str,
    resource_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    Get complete audit trail for a specific resource.
    **RBAC**: Only CFO and System Admin can access audit trails.
    """
    # Check role permission (RBAC)
    user_roles = current_user.get("roles", [])
    if not check_role_permission(user_roles, ["CFO", "System Admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only CFO and System Admin can view audit logs.",
        )

    # Get audit trail from service
    logs = get_resource_audit_trail(
        db=db,
        tenant_id=tenant_id,
        resource_type=resource_type,
        resource_id=resource_id,
    )

    # Convert to response models
    audit_logs = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first()

        audit_logs.append(
            AuditLogResponse(
                audit_log_id=str(log.id),
                tenant_id=str(log.tenant_id),
                user_id=str(log.user_id),
                user_name=user.full_name if user else None,
                user_email=user.email if user else None,
                action_type=log.action_type,
                resource_type=log.resource_type,
                resource_id=str(log.resource_id),
                old_values=log.old_values,
                new_values=log.new_values,
                change_summary=log.change_summary,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
            )
        )

    return ResourceAuditTrailResponse(
        resource_type=resource_type,
        resource_id=resource_id,
        audit_logs=audit_logs,
        total_changes=len(audit_logs),
    )


@router.get("/{audit_log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    audit_log_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    Get audit log by ID.
    **RBAC**: Only CFO and System Admin can access audit logs.
    """
    # Check role permission (RBAC)
    user_roles = current_user.get("roles", [])
    if not check_role_permission(user_roles, ["CFO", "System Admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only CFO and System Admin can view audit logs.",
        )

    # Get audit log
    log = (
        db.query(AuditLog)
        .filter(
            AuditLog.id == UUID(audit_log_id),
            AuditLog.tenant_id == UUID(tenant_id),
        )
        .first()
    )

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )

    # Get user info
    user = db.query(User).filter(User.id == log.user_id).first()

    return AuditLogResponse(
        audit_log_id=str(log.id),
        tenant_id=str(log.tenant_id),
        user_id=str(log.user_id),
        user_name=user.full_name if user else None,
        user_email=user.email if user else None,
        action_type=log.action_type,
        resource_type=log.resource_type,
        resource_id=str(log.resource_id),
        old_values=log.old_values,
        new_values=log.new_values,
        change_summary=log.change_summary,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        created_at=log.created_at,
    )
