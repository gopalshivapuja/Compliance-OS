"""
Unit tests for audit service.
Tests immutable audit logging functionality.
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import uuid4

from app.services.audit_service import (
    log_action,
    get_audit_logs,
    get_resource_audit_trail,
)
from app.models.audit_log import AuditLog


@pytest.mark.asyncio
async def test_log_action_creates_audit_log(db_session: Session, test_tenant, test_user):
    """Test that log_action creates an audit log entry."""
    tenant_id = str(test_tenant.id)
    user_id = str(test_user.id)
    resource_id = str(uuid4())

    audit_log = await log_action(
        db=db_session,
        tenant_id=tenant_id,
        user_id=user_id,
        action_type="CREATE",
        resource_type="compliance_instance",
        resource_id=resource_id,
        new_values={"status": "Not Started"},
        change_summary="Created new compliance instance",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
    )

    assert audit_log is not None
    assert audit_log.id is not None
    assert str(audit_log.tenant_id) == tenant_id
    assert str(audit_log.user_id) == user_id
    assert audit_log.action_type == "CREATE"
    assert audit_log.resource_type == "compliance_instance"
    assert str(audit_log.resource_id) == resource_id
    assert audit_log.new_values == {"status": "Not Started"}
    assert audit_log.change_summary == "Created new compliance instance"
    assert audit_log.ip_address == "192.168.1.1"
    assert audit_log.user_agent == "Mozilla/5.0"
    assert audit_log.created_at is not None


@pytest.mark.asyncio
async def test_log_action_update_with_old_and_new_values(
    db_session: Session, test_tenant, test_user
):
    """Test logging UPDATE action with before/after snapshots."""
    tenant_id = str(test_tenant.id)
    user_id = str(test_user.id)
    resource_id = str(uuid4())

    old_values = {"status": "Not Started", "owner_id": None}
    new_values = {"status": "In Progress", "owner_id": user_id}

    audit_log = await log_action(
        db=db_session,
        tenant_id=tenant_id,
        user_id=user_id,
        action_type="UPDATE",
        resource_type="compliance_instance",
        resource_id=resource_id,
        old_values=old_values,
        new_values=new_values,
        change_summary="Updated status from Not Started to In Progress",
    )

    assert audit_log.old_values == old_values
    assert audit_log.new_values == new_values
    assert audit_log.action_type == "UPDATE"


@pytest.mark.asyncio
async def test_log_action_login_action(db_session: Session, test_tenant, test_user):
    """Test logging LOGIN action."""
    tenant_id = str(test_tenant.id)
    user_id = str(test_user.id)

    audit_log = await log_action(
        db=db_session,
        tenant_id=tenant_id,
        user_id=user_id,
        action_type="LOGIN",
        resource_type="user",
        resource_id=user_id,
        change_summary="User logged in",
        ip_address="192.168.1.1",
    )

    assert audit_log.action_type == "LOGIN"
    assert audit_log.resource_type == "user"


@pytest.mark.asyncio
async def test_log_action_default_change_summary(db_session: Session, test_tenant, test_user):
    """Test that change_summary defaults to action + resource type."""
    tenant_id = str(test_tenant.id)
    user_id = str(test_user.id)
    resource_id = str(uuid4())

    audit_log = await log_action(
        db=db_session,
        tenant_id=tenant_id,
        user_id=user_id,
        action_type="DELETE",
        resource_type="evidence",
        resource_id=resource_id,
    )

    assert audit_log.change_summary == "DELETE on evidence"


def test_get_audit_logs_filters_by_tenant(db_session: Session, test_tenant, test_user):
    """Test that get_audit_logs filters by tenant_id."""
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.core.security import get_password_hash

    # Create second tenant and user
    tenant2 = Tenant(
        tenant_name="Test Company 2",
        tenant_code="TEST002",
        contact_email="test2@example.com",
        status="active",
    )
    db_session.add(tenant2)
    db_session.commit()
    db_session.refresh(tenant2)

    user2 = User(
        tenant_id=tenant2.id,
        email="user2@example.com",
        first_name="User",
        last_name="Two",
        password_hash=get_password_hash("Password123!"),
        status="active",
    )
    db_session.add(user2)
    db_session.commit()
    db_session.refresh(user2)

    tenant1_id = str(test_tenant.id)
    tenant2_id = str(tenant2.id)

    # Create audit logs for two different tenants
    log1 = AuditLog(
        tenant_id=tenant1_id,
        user_id=str(test_user.id),
        action_type="CREATE",
        resource_type="test",
        resource_id=str(uuid4()),
        created_at=datetime.utcnow(),
    )
    log2 = AuditLog(
        tenant_id=tenant2_id,
        user_id=str(user2.id),
        action_type="CREATE",
        resource_type="test",
        resource_id=str(uuid4()),
        created_at=datetime.utcnow(),
    )

    db_session.add_all([log1, log2])
    db_session.commit()

    # Query for tenant1 logs
    logs, total = get_audit_logs(db=db_session, tenant_id=tenant1_id)

    assert total == 1
    assert str(logs[0].tenant_id) == tenant1_id


def test_get_audit_logs_filters_by_resource_type(db_session: Session, test_tenant, test_user):
    """Test filtering audit logs by resource type."""
    tenant_id = str(test_tenant.id)
    user_id = str(test_user.id)

    # Create logs for different resource types
    log1 = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action_type="CREATE",
        resource_type="compliance_instance",
        resource_id=str(uuid4()),
        created_at=datetime.utcnow(),
    )
    log2 = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action_type="CREATE",
        resource_type="evidence",
        resource_id=str(uuid4()),
        created_at=datetime.utcnow(),
    )

    db_session.add_all([log1, log2])
    db_session.commit()

    # Query for compliance_instance logs only
    logs, total = get_audit_logs(
        db=db_session, tenant_id=tenant_id, resource_type="compliance_instance"
    )

    assert total == 1
    assert logs[0].resource_type == "compliance_instance"


def test_get_audit_logs_pagination(db_session: Session, test_tenant, test_user):
    """Test pagination of audit logs."""
    tenant_id = str(test_tenant.id)
    user_id = str(test_user.id)

    # Create 5 audit logs
    for i in range(5):
        log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action_type="CREATE",
            resource_type="test",
            resource_id=str(uuid4()),
            created_at=datetime.utcnow(),
        )
        db_session.add(log)

    db_session.commit()

    # Get first 2 logs
    logs, total = get_audit_logs(db=db_session, tenant_id=tenant_id, skip=0, limit=2)

    assert total == 5
    assert len(logs) == 2

    # Get next 2 logs
    logs, total = get_audit_logs(db=db_session, tenant_id=tenant_id, skip=2, limit=2)

    assert total == 5
    assert len(logs) == 2


def test_get_resource_audit_trail(db_session: Session, test_tenant, test_user):
    """Test getting complete audit trail for a specific resource."""
    tenant_id = str(test_tenant.id)
    user_id = str(test_user.id)
    resource_id = str(uuid4())

    # Create multiple audit logs for the same resource
    log1 = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action_type="CREATE",
        resource_type="compliance_instance",
        resource_id=resource_id,
        created_at=datetime.utcnow(),
    )
    log2 = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action_type="UPDATE",
        resource_type="compliance_instance",
        resource_id=resource_id,
        created_at=datetime.utcnow(),
    )
    # Create log for different resource
    log3 = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action_type="CREATE",
        resource_type="compliance_instance",
        resource_id=str(uuid4()),  # Different resource
        created_at=datetime.utcnow(),
    )

    db_session.add_all([log1, log2, log3])
    db_session.commit()

    # Get audit trail for specific resource
    trail = get_resource_audit_trail(
        db=db_session,
        tenant_id=tenant_id,
        resource_type="compliance_instance",
        resource_id=resource_id,
    )

    assert len(trail) == 2
    assert all(str(log.resource_id) == resource_id for log in trail)
    # Verify chronological order (oldest first)
    assert trail[0].action_type == "CREATE"
    assert trail[1].action_type == "UPDATE"
