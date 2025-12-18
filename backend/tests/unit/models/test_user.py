"""
Unit tests for User model
"""

import pytest
from app.models.user import User
from app.core.security import get_password_hash


def test_user_creation(db_session, test_tenant):
    """Test creating a user."""
    user = User(
        tenant_id=test_tenant.id,
        email="newuser@example.com",
        first_name="New",
        last_name="User",
        password_hash=get_password_hash("Password123!"),
        status="active",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == "newuser@example.com"
    assert user.full_name == "New User"
    assert user.status == "active"
    assert user.tenant_id == test_tenant.id


def test_user_password_hashing(db_session, test_tenant):
    """Test that user passwords are hashed correctly."""
    plain_password = "Test123!@#"

    user = User(
        tenant_id=test_tenant.id,
        email="test@example.com",
        first_name="Test",
        last_name="User",
        status="active",
    )

    # Set password (should be hashed)
    user.set_password(plain_password)

    db_session.add(user)
    db_session.commit()

    # Password should not be stored in plain text
    assert user.password_hash != plain_password

    # Verify password should work
    assert user.verify_password(plain_password)

    # Wrong password should fail
    assert not user.verify_password("wrongpassword")


def test_user_string_representation(test_user):
    """Test user __repr__ method."""
    assert "testuser@example.com" in str(test_user)


def test_user_tenant_relationship(db_session, test_tenant):
    """Test that user has proper relationship with tenant."""
    user = User(
        tenant_id=test_tenant.id,
        email="relationtest@example.com",
        first_name="Relation",
        last_name="Test",
        password_hash=get_password_hash("Test123!"),
        status="active",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Verify relationship
    assert user.tenant is not None
    assert user.tenant.id == test_tenant.id
    assert user.tenant.tenant_name == "Test Company"
