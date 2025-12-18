"""
Integration tests for authentication endpoints.
Tests login, refresh, logout, and /me endpoints with real database.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.user import User
from app.models.tenant import Tenant
from app.models.role import Role, user_roles
from app.core.security import get_password_hash


@pytest.fixture
def test_tenant_with_user(db_session):
    """Create a test tenant with a user and role."""
    # Create tenant
    tenant = Tenant(
        tenant_name="Test Company",
        tenant_code="TEST001",
        contact_email="test@example.com",
        status="active",
    )
    db_session.add(tenant)
    db_session.flush()

    # Create role
    role = Role(
        role_code="CFO",
        role_name="Chief Financial Officer",
        description="Financial oversight and compliance approval",
        is_system_role=True,
    )
    db_session.add(role)
    db_session.flush()

    # Create user
    user = User(
        tenant_id=tenant.id,
        email="testuser@example.com",
        first_name="Test",
        last_name="User",
        password_hash=get_password_hash("TestPassword123!"),
        status="active",
        is_system_admin=False,
    )
    db_session.add(user)
    db_session.flush()

    # Assign role to user (manually insert with tenant_id)
    db_session.execute(
        user_roles.insert().values(
            user_id=user.id,
            role_id=role.id,
            tenant_id=tenant.id,
        )
    )
    db_session.commit()
    db_session.refresh(user)

    return {"tenant": tenant, "user": user, "role": role}


def test_login_success(client: TestClient, test_tenant_with_user):
    """Test successful login with valid credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data

    # Verify user data
    user_data = data["user"]
    assert user_data["email"] == "testuser@example.com"
    assert user_data["first_name"] == "Test"
    assert user_data["last_name"] == "User"
    assert user_data["full_name"] == "Test User"
    assert "CFO" in user_data["roles"]
    assert user_data["is_system_admin"] is False

    # Verify tokens are non-empty
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0


def test_login_invalid_email(client: TestClient, test_tenant_with_user):
    """Test login with non-existent email."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_invalid_password(client: TestClient, test_tenant_with_user):
    """Test login with incorrect password."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_inactive_user(client: TestClient, test_tenant_with_user, db_session):
    """Test login with inactive user account."""
    # Set user status to inactive
    user = test_tenant_with_user["user"]
    user.status = "inactive"
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()


def test_refresh_token_success(client: TestClient, test_tenant_with_user):
    """Test successful token refresh with valid refresh token."""
    # First login to get tokens
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123!",
        },
    )
    login_data = login_response.json()
    refresh_token = login_data["refresh_token"]

    # Use refresh token to get new access token
    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 200
    refresh_data = refresh_response.json()

    # Verify new tokens are returned
    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data
    assert refresh_data["token_type"] == "bearer"

    # Verify new tokens are different (token rotation)
    assert refresh_data["access_token"] != login_data["access_token"]
    assert refresh_data["refresh_token"] != refresh_token

    # Verify user data is still correct
    assert refresh_data["user"]["email"] == "testuser@example.com"


def test_refresh_token_invalid(client: TestClient, test_tenant_with_user):
    """Test token refresh with invalid refresh token."""
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-token-123"},
    )

    assert response.status_code == 401
    assert "Invalid or expired" in response.json()["detail"]


def test_refresh_token_old_token_invalidated(
    client: TestClient, test_tenant_with_user
):
    """Test that old refresh token is invalidated after refresh."""
    # Login to get tokens
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123!",
        },
    )
    old_refresh_token = login_response.json()["refresh_token"]

    # Refresh token
    client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )

    # Try to use old refresh token again (should fail)
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )

    assert response.status_code == 401


def test_logout_success(client: TestClient, test_tenant_with_user):
    """Test successful logout."""
    # Login to get tokens
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123!",
        },
    )
    tokens = login_response.json()

    # Logout
    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Logout successful"

    # Try to use refresh token after logout (should fail)
    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert refresh_response.status_code == 401


def test_get_me_success(client: TestClient, test_tenant_with_user):
    """Test getting current user information."""
    # Login to get access token
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123!",
        },
    )
    access_token = login_response.json()["access_token"]

    # Get current user info
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["email"] == "testuser@example.com"
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"
    assert data["full_name"] == "Test User"
    assert "CFO" in data["roles"]
    assert "user_id" in data
    assert "tenant_id" in data


def test_get_me_unauthorized(client: TestClient, test_tenant_with_user):
    """Test /me endpoint without authentication."""
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 403  # Forbidden (no token provided)


def test_get_me_invalid_token(client: TestClient, test_tenant_with_user):
    """Test /me endpoint with invalid token."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token-123"},
    )

    assert response.status_code in [401, 403]  # Unauthorized or Forbidden


def test_login_creates_audit_log(client: TestClient, test_tenant_with_user, db_session):
    """Test that login action is logged to audit trail."""
    from app.models.audit_log import AuditLog

    # Login
    client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123!",
        },
    )

    # Check audit log was created
    audit_log = db_session.query(AuditLog).filter(
        AuditLog.action_type == "LOGIN",
        AuditLog.resource_type == "user",
    ).first()

    assert audit_log is not None
    assert audit_log.user_id == str(test_tenant_with_user["user"].id)
    assert audit_log.tenant_id == str(test_tenant_with_user["tenant"].id)
    assert "logged in" in audit_log.change_summary.lower()


def test_logout_creates_audit_log(client: TestClient, test_tenant_with_user, db_session):
    """Test that logout action is logged to audit trail."""
    from app.models.audit_log import AuditLog

    # Login to get tokens
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123!",
        },
    )
    tokens = login_response.json()

    # Logout
    client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    # Check audit log was created
    audit_log = db_session.query(AuditLog).filter(
        AuditLog.action_type == "LOGOUT",
        AuditLog.resource_type == "user",
    ).first()

    assert audit_log is not None
    assert audit_log.user_id == str(test_tenant_with_user["user"].id)
    assert "logged out" in audit_log.change_summary.lower()
