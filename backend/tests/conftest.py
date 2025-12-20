"""
Pytest configuration and fixtures

This file contains common test fixtures used across all tests.
"""

import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.database import get_db
from app.models.base import Base
from app.models.user import User
from app.models.tenant import Tenant
from app.models.role import Role
from app.models.audit_log import AuditLog
from app.core.security import get_password_hash


# PostgreSQL test database URL
# Use separate test database on your existing PostgreSQL server
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql://gopal@localhost:5432/compliance_os_test"
)

# Create test engine with PostgreSQL
engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,  # Don't pool connections in tests
    echo=False,  # Set to True for SQL debugging
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test function.
    Uses PostgreSQL test database with proper transaction rollback.
    """
    # Create all tables before test
    Base.metadata.create_all(bind=engine)

    # Create session
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()  # Rollback changes after each test
        connection.close()
        # Clean up all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a test client with dependency injection.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_tenant(db_session):
    """
    Create a test tenant.
    """
    tenant = Tenant(
        tenant_name="Test Company",
        tenant_code="TEST001",
        contact_email="test@example.com",
        status="active",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def test_user(db_session, test_tenant):
    """
    Create a test user.
    """
    user = User(
        tenant_id=test_tenant.id,
        email="testuser@example.com",
        first_name="Test",
        last_name="User",
        password_hash=get_password_hash("Test123!@#"),
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_role(db_session):
    """
    Create a test role.
    """
    role = Role(
        role_name="Tax Lead",
        description="Tax compliance execution",
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture
def auth_headers(test_user):
    """
    Create authentication headers for API requests.
    """
    from app.core.security import create_access_token

    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}
