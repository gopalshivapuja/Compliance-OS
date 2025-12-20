"""
Unit tests for Entity Access Control Service.
Tests all functions for entity access management and role-based permissions.
Includes multi-tenant isolation tests.
"""

import pytest
from sqlalchemy.orm import Session

from app.models import Tenant, User, Entity, Role, user_roles, entity_access
from app.core.security import get_password_hash
from app.services.entity_access_service import (
    check_entity_access,
    get_user_accessible_entities,
    check_role_permission,
    get_user_roles,
    grant_entity_access,
    revoke_entity_access,
    get_entity_users,
)


@pytest.fixture
def test_roles(db_session):
    """Create test roles."""
    cfo_role = Role(
        role_code="CFO",
        role_name="Chief Financial Officer",
        description="Financial oversight",
        is_system_role=True,
    )
    tax_lead_role = Role(
        role_code="TAX_LEAD",
        role_name="Tax Lead",
        description="Tax compliance execution",
        is_system_role=True,
    )
    manager_role = Role(
        role_code="MANAGER",
        role_name="Manager",
        description="Team management",
        is_system_role=False,
    )
    db_session.add_all([cfo_role, tax_lead_role, manager_role])
    db_session.commit()
    db_session.refresh(cfo_role)
    db_session.refresh(tax_lead_role)
    db_session.refresh(manager_role)
    return {
        "cfo": cfo_role,
        "tax_lead": tax_lead_role,
        "manager": manager_role,
    }


@pytest.fixture
def test_users_with_roles(db_session, test_tenant, test_roles):
    """Create test users with different role combinations."""
    # User 1: CFO role
    user1 = User(
        tenant_id=test_tenant.id,
        email="cfo@example.com",
        first_name="Chief",
        last_name="Officer",
        password_hash=get_password_hash("Test123!"),
        status="active",
    )
    db_session.add(user1)
    db_session.flush()

    # Assign CFO role
    db_session.execute(
        user_roles.insert().values(
            user_id=user1.id,
            role_id=test_roles["cfo"].id,
            tenant_id=test_tenant.id,
        )
    )

    # User 2: Tax Lead and Manager roles
    user2 = User(
        tenant_id=test_tenant.id,
        email="taxlead@example.com",
        first_name="Tax",
        last_name="Lead",
        password_hash=get_password_hash("Test123!"),
        status="active",
    )
    db_session.add(user2)
    db_session.flush()

    # Assign Tax Lead and Manager roles
    db_session.execute(
        user_roles.insert().values(
            user_id=user2.id,
            role_id=test_roles["tax_lead"].id,
            tenant_id=test_tenant.id,
        )
    )
    db_session.execute(
        user_roles.insert().values(
            user_id=user2.id,
            role_id=test_roles["manager"].id,
            tenant_id=test_tenant.id,
        )
    )

    # User 3: No roles
    user3 = User(
        tenant_id=test_tenant.id,
        email="norole@example.com",
        first_name="No",
        last_name="Role",
        password_hash=get_password_hash("Test123!"),
        status="active",
    )
    db_session.add(user3)
    db_session.flush()

    db_session.commit()
    db_session.refresh(user1)
    db_session.refresh(user2)
    db_session.refresh(user3)

    return {
        "cfo_user": user1,
        "tax_lead_user": user2,
        "no_role_user": user3,
    }


@pytest.fixture
def test_entities_with_access(db_session, test_tenant, test_user):
    """Create test entities and grant access to test_user."""
    entity1 = Entity(
        tenant_id=test_tenant.id,
        entity_code="ENT001",
        entity_name="Entity 1",
        entity_type="Company",
        status="active",
    )
    entity2 = Entity(
        tenant_id=test_tenant.id,
        entity_code="ENT002",
        entity_name="Entity 2",
        entity_type="Branch",
        status="active",
    )
    entity3 = Entity(
        tenant_id=test_tenant.id,
        entity_code="ENT003",
        entity_name="Entity 3",
        entity_type="Company",
        status="active",
    )
    db_session.add_all([entity1, entity2, entity3])
    db_session.flush()

    # Grant access to entity1 and entity2 for test_user
    db_session.execute(
        entity_access.insert().values(
            user_id=test_user.id,
            entity_id=entity1.id,
            tenant_id=test_tenant.id,
        )
    )
    db_session.execute(
        entity_access.insert().values(
            user_id=test_user.id,
            entity_id=entity2.id,
            tenant_id=test_tenant.id,
        )
    )

    db_session.commit()
    db_session.refresh(entity1)
    db_session.refresh(entity2)
    db_session.refresh(entity3)

    return [entity1, entity2, entity3]


def test_check_entity_access_allowed(db_session, test_user, test_entities_with_access):
    """Test checking entity access when user has permission."""
    entity1 = test_entities_with_access[0]

    result = check_entity_access(db_session, test_user.id, entity1.id)

    assert result is True


def test_check_entity_access_denied(db_session, test_user, test_entities_with_access):
    """Test checking entity access when user lacks permission."""
    entity3 = test_entities_with_access[2]  # No access granted to entity3

    result = check_entity_access(db_session, test_user.id, entity3.id)

    assert result is False


def test_check_entity_access_with_tenant_id(
    db_session, test_tenant, test_user, test_entities_with_access
):
    """Test checking entity access with tenant_id validation."""
    entity1 = test_entities_with_access[0]

    # Should succeed with correct tenant_id
    result = check_entity_access(db_session, test_user.id, entity1.id, test_tenant.id)
    assert result is True


def test_check_entity_access_multi_tenant_isolation(
    db_session, test_tenant, test_user, test_entities_with_access
):
    """Test that entity access respects tenant boundaries."""
    entity1 = test_entities_with_access[0]

    # Create another tenant
    other_tenant = Tenant(
        tenant_name="Other Tenant",
        tenant_code="OTHER",
        contact_email="other@example.com",
        status="active",
    )
    db_session.add(other_tenant)
    db_session.commit()

    # Check access with wrong tenant_id should fail
    result = check_entity_access(db_session, test_user.id, entity1.id, other_tenant.id)
    assert result is False


def test_get_user_accessible_entities(
    db_session, test_tenant, test_user, test_entities_with_access
):
    """Test getting list of accessible entity IDs for a user."""
    entity1 = test_entities_with_access[0]
    entity2 = test_entities_with_access[1]

    result = get_user_accessible_entities(db_session, test_user.id, test_tenant.id)

    assert len(result) == 2
    assert entity1.id in result
    assert entity2.id in result


def test_get_user_accessible_entities_empty(db_session, test_tenant, test_entities_with_access):
    """Test getting accessible entities for user with no access."""
    # Create user with no entity access
    new_user = User(
        tenant_id=test_tenant.id,
        email="newuser@example.com",
        first_name="New",
        last_name="User",
        password_hash=get_password_hash("Test123!"),
        status="active",
    )
    db_session.add(new_user)
    db_session.commit()

    result = get_user_accessible_entities(db_session, new_user.id, test_tenant.id)

    assert len(result) == 0


def test_get_user_accessible_entities_multi_tenant(
    db_session, test_tenant, test_user, test_entities_with_access
):
    """Test that accessible entities respects tenant isolation."""
    # Create another tenant with entity
    other_tenant = Tenant(
        tenant_name="Other Tenant",
        tenant_code="OTHER",
        contact_email="other@example.com",
        status="active",
    )
    db_session.add(other_tenant)
    db_session.flush()

    other_entity = Entity(
        tenant_id=other_tenant.id,
        entity_code="OTHER-ENT",
        entity_name="Other Entity",
        entity_type="Company",
        status="active",
    )
    db_session.add(other_entity)
    db_session.flush()

    # Grant access to user for other tenant's entity (simulating cross-tenant scenario)
    db_session.execute(
        entity_access.insert().values(
            user_id=test_user.id,
            entity_id=other_entity.id,
            tenant_id=other_tenant.id,
        )
    )
    db_session.commit()

    # Query with test_tenant should only return test_tenant's entities
    result = get_user_accessible_entities(db_session, test_user.id, test_tenant.id)
    assert other_entity.id not in result

    # Query with other_tenant should only return other_tenant's entity
    result_other = get_user_accessible_entities(db_session, test_user.id, other_tenant.id)
    assert other_entity.id in result_other
    assert len(result_other) == 1


def test_check_role_permission_single_role_match(test_users_with_roles):
    """Test role permission check with single matching role."""
    user_roles_list = ["CFO"]
    required_roles = ["CFO", "System Admin"]

    result = check_role_permission(user_roles_list, required_roles)

    assert result is True


def test_check_role_permission_multiple_roles_match(test_users_with_roles):
    """Test role permission check with multiple roles, one matching."""
    user_roles_list = ["Tax Lead", "Manager"]
    required_roles = ["Manager", "System Admin"]

    result = check_role_permission(user_roles_list, required_roles)

    assert result is True


def test_check_role_permission_no_match(test_users_with_roles):
    """Test role permission check with no matching roles."""
    user_roles_list = ["Tax Lead", "Manager"]
    required_roles = ["CFO", "System Admin"]

    result = check_role_permission(user_roles_list, required_roles)

    assert result is False


def test_check_role_permission_empty_user_roles():
    """Test role permission check with user having no roles."""
    user_roles_list = []
    required_roles = ["CFO", "System Admin"]

    result = check_role_permission(user_roles_list, required_roles)

    assert result is False


def test_check_role_permission_empty_required_roles():
    """Test role permission check with no required roles."""
    user_roles_list = ["CFO"]
    required_roles = []

    result = check_role_permission(user_roles_list, required_roles)

    assert result is False


def test_get_user_roles(db_session, test_users_with_roles):
    """Test getting role names for a user with roles."""
    cfo_user = test_users_with_roles["cfo_user"]

    result = get_user_roles(db_session, cfo_user.id)

    assert len(result) == 1
    assert "Chief Financial Officer" in result


def test_get_user_roles_multiple(db_session, test_users_with_roles):
    """Test getting role names for user with multiple roles."""
    tax_lead_user = test_users_with_roles["tax_lead_user"]

    result = get_user_roles(db_session, tax_lead_user.id)

    assert len(result) == 2
    assert "Tax Lead" in result
    assert "Manager" in result


def test_get_user_roles_no_roles(db_session, test_users_with_roles):
    """Test getting role names for user with no roles."""
    no_role_user = test_users_with_roles["no_role_user"]

    result = get_user_roles(db_session, no_role_user.id)

    assert len(result) == 0


def test_get_user_roles_nonexistent_user(db_session):
    """Test getting role names for non-existent user."""
    from uuid import uuid4

    fake_user_id = uuid4()
    result = get_user_roles(db_session, fake_user_id)

    assert result == []


def test_grant_entity_access_success(db_session, test_tenant, test_user, test_entities_with_access):
    """Test granting entity access to a user."""
    entity3 = test_entities_with_access[2]  # No access initially

    # Verify no access initially
    assert check_entity_access(db_session, test_user.id, entity3.id) is False

    # Grant access
    result = grant_entity_access(db_session, test_user.id, entity3.id, test_tenant.id)

    assert result is True
    # Verify access was granted
    assert check_entity_access(db_session, test_user.id, entity3.id) is True


def test_grant_entity_access_duplicate(
    db_session, test_tenant, test_user, test_entities_with_access
):
    """Test granting entity access when already exists."""
    entity1 = test_entities_with_access[0]  # Already has access

    # Try to grant access again
    result = grant_entity_access(db_session, test_user.id, entity1.id, test_tenant.id)

    assert result is False  # Should return False for duplicate


def test_revoke_entity_access_success(db_session, test_user, test_entities_with_access):
    """Test revoking entity access from a user."""
    entity1 = test_entities_with_access[0]  # Has access initially

    # Verify access exists
    assert check_entity_access(db_session, test_user.id, entity1.id) is True

    # Revoke access
    result = revoke_entity_access(db_session, test_user.id, entity1.id)

    assert result is True
    # Verify access was revoked
    assert check_entity_access(db_session, test_user.id, entity1.id) is False


def test_revoke_entity_access_nonexistent(db_session, test_user, test_entities_with_access):
    """Test revoking entity access that doesn't exist."""
    entity3 = test_entities_with_access[2]  # No access

    # Try to revoke non-existent access
    result = revoke_entity_access(db_session, test_user.id, entity3.id)

    assert result is False  # Should return False for non-existent access


def test_get_entity_users(db_session, test_tenant, test_user, test_entities_with_access):
    """Test getting all users with access to an entity."""
    entity1 = test_entities_with_access[0]

    # Create another user and grant access
    user2 = User(
        tenant_id=test_tenant.id,
        email="user2@example.com",
        first_name="User",
        last_name="Two",
        password_hash=get_password_hash("Test123!"),
        status="active",
    )
    db_session.add(user2)
    db_session.flush()

    db_session.execute(
        entity_access.insert().values(
            user_id=user2.id,
            entity_id=entity1.id,
            tenant_id=test_tenant.id,
        )
    )
    db_session.commit()

    result = get_entity_users(db_session, entity1.id, test_tenant.id)

    assert len(result) == 2
    user_ids = [user.id for user in result]
    assert test_user.id in user_ids
    assert user2.id in user_ids


def test_get_entity_users_empty(db_session, test_tenant, test_entities_with_access):
    """Test getting users for entity with no access grants."""
    entity3 = test_entities_with_access[2]  # No users have access

    result = get_entity_users(db_session, entity3.id, test_tenant.id)

    assert len(result) == 0


def test_get_entity_users_multi_tenant_isolation(
    db_session, test_tenant, test_user, test_entities_with_access
):
    """Test that get_entity_users respects tenant boundaries."""
    entity1 = test_entities_with_access[0]

    # Create another tenant
    other_tenant = Tenant(
        tenant_name="Other Tenant",
        tenant_code="OTHER",
        contact_email="other@example.com",
        status="active",
    )
    db_session.add(other_tenant)
    db_session.commit()

    # Query with wrong tenant_id should return no users
    result = get_entity_users(db_session, entity1.id, other_tenant.id)
    assert len(result) == 0

    # Query with correct tenant_id should return users
    result_correct = get_entity_users(db_session, entity1.id, test_tenant.id)
    assert len(result_correct) == 1
    assert result_correct[0].id == test_user.id
