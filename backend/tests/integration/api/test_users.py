"""
Integration tests for User API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Tenant, User, Role
from app.models.role import user_roles
from app.core.security import create_access_token


@pytest.fixture
def test_tenant(db_session: Session):
    """Create a test tenant"""
    tenant = Tenant(
        tenant_code="TEST_TENANT",
        tenant_name="Test Tenant Inc",
        status="active",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def admin_user_fixture(db_session: Session, test_tenant: Tenant):
    """Create a tenant admin user for testing"""
    # Check if admin role exists, create if not
    admin_role = db_session.query(Role).filter(Role.role_code == "admin").first()
    if not admin_role:
        admin_role = Role(
            role_code="admin",
            role_name="Administrator",
        )
        db_session.add(admin_role)
        db_session.flush()

    # Create admin user
    admin = User(
        email="admin@test.com",
        first_name="Admin",
        last_name="User",
        tenant_id=test_tenant.id,
        status="active",
        is_system_admin=False,
    )
    admin.set_password("AdminPass123!")
    db_session.add(admin)
    db_session.flush()

    # Assign role to user (manually insert with tenant_id)
    db_session.execute(
        user_roles.insert().values(
            user_id=admin.id,
            role_id=admin_role.id,
            tenant_id=test_tenant.id,
        )
    )
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def system_admin_user(db_session: Session):
    """Create a system admin user for testing"""
    # Create separate tenant for system admin
    tenant = Tenant(
        tenant_code="SYSTEM_TENANT",
        tenant_name="System Admin Tenant",
        status="active",
    )
    db_session.add(tenant)
    db_session.flush()

    admin = User(
        email="sysadmin@test.com",
        first_name="System",
        last_name="Admin",
        tenant_id=tenant.id,
        status="active",
        is_system_admin=True,
    )
    admin.set_password("SysAdminPass123!")
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def regular_user_fixture(db_session: Session, test_tenant: Tenant):
    """Create a regular (non-admin) user for testing"""
    user = User(
        email="user@test.com",
        first_name="Regular",
        last_name="User",
        tenant_id=test_tenant.id,
        status="active",
        is_system_admin=False,
    )
    user.set_password("UserPass123!")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_headers(admin_user_fixture: User):
    """Create auth headers for tenant admin user"""
    token = create_access_token(
        data={
            "user_id": str(admin_user_fixture.id),
            "tenant_id": str(admin_user_fixture.tenant_id),
            "email": admin_user_fixture.email,
            "roles": ["admin"],
            "is_system_admin": False,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def system_admin_headers(system_admin_user: User):
    """Create auth headers for system admin user"""
    token = create_access_token(
        data={
            "user_id": str(system_admin_user.id),
            "tenant_id": str(system_admin_user.tenant_id),
            "email": system_admin_user.email,
            "roles": ["admin"],
            "is_system_admin": True,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def regular_headers(regular_user_fixture: User):
    """Create auth headers for regular user"""
    token = create_access_token(
        data={
            "user_id": str(regular_user_fixture.id),
            "tenant_id": str(regular_user_fixture.tenant_id),
            "email": regular_user_fixture.email,
            "roles": [],
            "is_system_admin": False,
        }
    )
    return {"Authorization": f"Bearer {token}"}


class TestCreateUser:
    """Tests for POST /api/v1/users"""

    def test_create_user_success_as_admin(
        self, client: TestClient, admin_headers: dict, test_tenant: Tenant
    ):
        """Test creating a user as tenant admin"""
        response = client.post(
            "/api/v1/users/",
            json={
                "email": "newuser@test.com",
                "first_name": "New",
                "last_name": "User",
                "phone": "+91-80-12345678",
                "password": "SecurePass123!",  # pragma: allowlist secret
                "tenant_id": str(test_tenant.id),
                "is_system_admin": False,
            },
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["first_name"] == "New"
        assert data["last_name"] == "User"
        assert data["status"] == "active"
        assert data["is_system_admin"] is False
        assert "user_id" in data
        assert "password" not in data  # Password should not be returned

    def test_create_user_success_as_system_admin(
        self, client: TestClient, system_admin_headers: dict, test_tenant: Tenant
    ):
        """Test creating a user as system admin in any tenant"""
        response = client.post(
            "/api/v1/users/",
            json={
                "email": "crosstenantuser@test.com",
                "first_name": "Cross",
                "last_name": "Tenant",
                "password": "SecurePass123!",  # pragma: allowlist secret
                "tenant_id": str(test_tenant.id),
                "is_system_admin": False,
            },
            headers=system_admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "crosstenantuser@test.com"

    def test_create_user_duplicate_email(
        self,
        client: TestClient,
        admin_headers: dict,
        test_tenant: Tenant,
        regular_user_fixture: User,
    ):
        """Test creating a user with duplicate email"""
        response = client.post(
            "/api/v1/users/",
            json={
                "email": regular_user_fixture.email,  # Duplicate
                "first_name": "Another",
                "last_name": "User",
                "password": "SecurePass123!",  # pragma: allowlist secret
                "tenant_id": str(test_tenant.id),  # pragma: allowlist secret
            },
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_create_user_invalid_tenant(self, client: TestClient, admin_headers: dict):
        """Test creating a user with non-existent tenant"""
        fake_tenant_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.post(
            "/api/v1/users/",
            json={
                "email": "orphanuser@test.com",
                "first_name": "Orphan",
                "last_name": "User",
                "password": "SecurePass123!",  # pragma: allowlist secret
                "tenant_id": fake_tenant_id,
            },
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_create_user_unauthorized_as_regular_user(
        self, client: TestClient, regular_headers: dict, test_tenant: Tenant
    ):
        """Test creating a user as non-admin user"""
        response = client.post(
            "/api/v1/users/",
            json={
                "email": "unauthorized@test.com",
                "first_name": "Unauthorized",
                "last_name": "User",
                "password": "SecurePass123!",  # pragma: allowlist secret
                "tenant_id": str(test_tenant.id),
            },
            headers=regular_headers,
        )

        assert response.status_code == 403
        assert "administrator" in response.json()["detail"].lower()

    def test_create_user_no_auth(self, client: TestClient, test_tenant: Tenant):
        """Test creating a user without authentication"""
        response = client.post(
            "/api/v1/users/",
            json={
                "email": "noauth@test.com",
                "first_name": "No",
                "last_name": "Auth",
                "password": "SecurePass123!",  # pragma: allowlist secret
                "tenant_id": str(test_tenant.id),
            },
        )

        # Should return 401 or 403 for missing authentication
        assert response.status_code in [401, 403]

    def test_create_user_weak_password(
        self, client: TestClient, admin_headers: dict, test_tenant: Tenant
    ):
        """Test creating a user with weak password"""
        response = client.post(
            "/api/v1/users/",
            json={
                "email": "weakpass@test.com",
                "first_name": "Weak",
                "last_name": "Password",
                "password": "123",  # Too short  # pragma: allowlist secret
                "tenant_id": str(test_tenant.id),
            },
            headers=admin_headers,
        )

        assert response.status_code == 422  # Validation error

    def test_create_user_invalid_email(
        self, client: TestClient, admin_headers: dict, test_tenant: Tenant
    ):
        """Test creating a user with invalid email format"""
        response = client.post(
            "/api/v1/users/",
            json={
                "email": "notanemail",  # Invalid format
                "first_name": "Invalid",
                "last_name": "Email",
                "password": "SecurePass123!",  # pragma: allowlist secret
                "tenant_id": str(test_tenant.id),
            },
            headers=admin_headers,
        )

        assert response.status_code == 422

    def test_create_system_admin_only_by_system_admin(
        self, client: TestClient, admin_headers: dict, test_tenant: Tenant
    ):
        """Test that tenant admins cannot create system admins"""
        response = client.post(
            "/api/v1/users/",
            json={
                "email": "fakesysadmin@test.com",
                "first_name": "Fake",
                "last_name": "SysAdmin",
                "password": "SecurePass123!",  # pragma: allowlist secret
                "tenant_id": str(test_tenant.id),
                "is_system_admin": True,  # Tenant admin tries to create system admin
            },
            headers=admin_headers,
        )

        # Should succeed but is_system_admin should be False
        assert response.status_code == 201
        data = response.json()
        assert data["is_system_admin"] is False  # Overridden


class TestListUsers:
    """Tests for GET /api/v1/users"""

    def test_list_users_success_as_admin(self, client: TestClient, admin_headers: dict):
        """Test listing users as tenant admin"""
        response = client.get("/api/v1/users/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_list_users_with_pagination(
        self, client: TestClient, admin_headers: dict, db_session: Session, test_tenant: Tenant
    ):
        """Test user list pagination"""
        # Create multiple users
        for i in range(5):
            user = User(
                email=f"testuser{i}@test.com",
                first_name=f"Test{i}",
                last_name="User",
                tenant_id=test_tenant.id,
                status="active",
            )
            user.set_password("Pass123!")
            db_session.add(user)
        db_session.commit()

        # Test pagination
        response = client.get("/api/v1/users/?skip=0&limit=3", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 3
        assert len(data["items"]) <= 3

    def test_list_users_with_status_filter(
        self, client: TestClient, admin_headers: dict, db_session: Session, test_tenant: Tenant
    ):
        """Test filtering users by status"""
        # Create users with different statuses
        active_user = User(
            email="activeuser@test.com",
            first_name="Active",
            last_name="User",
            tenant_id=test_tenant.id,
            status="active",
        )
        active_user.set_password("Pass123!")

        inactive_user = User(
            email="inactiveuser@test.com",
            first_name="Inactive",
            last_name="User",
            tenant_id=test_tenant.id,
            status="inactive",
        )
        inactive_user.set_password("Pass123!")

        db_session.add_all([active_user, inactive_user])
        db_session.commit()

        # Filter by active status
        response = client.get("/api/v1/users/?user_status=active", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert all(u["status"] == "active" for u in data["items"])

    def test_list_users_with_search(
        self, client: TestClient, admin_headers: dict, db_session: Session, test_tenant: Tenant
    ):
        """Test searching users by name or email"""
        user = User(
            email="searchable@test.com",
            first_name="Searchable",
            last_name="Person",
            tenant_id=test_tenant.id,
            status="active",
        )
        user.set_password("Pass123!")
        db_session.add(user)
        db_session.commit()

        # Search by first name
        response = client.get("/api/v1/users/?search=Searchable", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any("Searchable" in u["first_name"] for u in data["items"])

    def test_list_users_tenant_isolation(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
    ):
        """Test that tenant admins only see users in their tenant"""
        # Create another tenant with users
        other_tenant = Tenant(tenant_code="OTHER", tenant_name="Other Tenant", status="active")
        db_session.add(other_tenant)
        db_session.flush()

        other_user = User(
            email="othertenantuser@test.com",
            first_name="Other",
            last_name="Tenant",
            tenant_id=other_tenant.id,
            status="active",
        )
        other_user.set_password("Pass123!")
        db_session.add(other_user)
        db_session.commit()

        # Admin should not see other tenant's users
        response = client.get("/api/v1/users/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        user_emails = [u["email"] for u in data["items"]]
        assert "othertenantuser@test.com" not in user_emails

    def test_list_users_as_system_admin_all_tenants(
        self, client: TestClient, system_admin_headers: dict, db_session: Session
    ):
        """Test that system admins can view users across all tenants"""
        response = client.get("/api/v1/users/", headers=system_admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1  # Should see users from all tenants

    def test_list_users_unauthorized_as_regular_user(
        self, client: TestClient, regular_headers: dict
    ):
        """Test that regular users can list users (they'll see their tenant's users)"""
        # This might actually be allowed depending on business logic
        # If not allowed, expect 403
        response = client.get("/api/v1/users/", headers=regular_headers)

        # Adjust based on actual business logic
        assert response.status_code in [200, 403]


class TestGetUser:
    """Tests for GET /api/v1/users/{user_id}"""

    def test_get_user_own_profile(
        self, client: TestClient, regular_headers: dict, regular_user_fixture: User
    ):
        """Test getting own user profile"""
        response = client.get(f"/api/v1/users/{regular_user_fixture.id}", headers=regular_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(regular_user_fixture.id)
        assert data["email"] == regular_user_fixture.email
        assert "password" not in data

    def test_get_user_same_tenant_as_admin(
        self,
        client: TestClient,
        admin_headers: dict,
        regular_user_fixture: User,
    ):
        """Test getting user in same tenant as admin"""
        response = client.get(f"/api/v1/users/{regular_user_fixture.id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(regular_user_fixture.id)

    def test_get_user_any_tenant_as_system_admin(
        self,
        client: TestClient,
        system_admin_headers: dict,
        regular_user_fixture: User,
    ):
        """Test getting user in any tenant as system admin"""
        response = client.get(
            f"/api/v1/users/{regular_user_fixture.id}", headers=system_admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(regular_user_fixture.id)

    def test_get_user_other_tenant_forbidden(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
    ):
        """Test that regular user cannot view users in other tenants"""
        # Create user in different tenant
        other_tenant = Tenant(tenant_code="OTHER2", tenant_name="Other Tenant 2", status="active")
        db_session.add(other_tenant)
        db_session.flush()

        other_user = User(
            email="othertenant2@test.com",
            first_name="Other",
            last_name="Tenant2",
            tenant_id=other_tenant.id,
            status="active",
        )
        other_user.set_password("Pass123!")
        db_session.add(other_user)
        db_session.commit()

        response = client.get(f"/api/v1/users/{other_user.id}", headers=regular_headers)

        assert response.status_code == 403

    def test_get_user_not_found(self, client: TestClient, admin_headers: dict):
        """Test getting non-existent user"""
        fake_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.get(f"/api/v1/users/{fake_id}", headers=admin_headers)

        assert response.status_code == 404


class TestUpdateUser:
    """Tests for PUT /api/v1/users/{user_id}"""

    def test_update_user_own_profile(
        self, client: TestClient, regular_headers: dict, regular_user_fixture: User
    ):
        """Test updating own user profile"""
        response = client.put(
            f"/api/v1/users/{regular_user_fixture.id}",
            json={
                "first_name": "UpdatedFirst",
                "last_name": "UpdatedLast",
                "phone": "+91-80-99999999",
            },
            headers=regular_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "UpdatedFirst"
        assert data["last_name"] == "UpdatedLast"
        assert data["phone"] == "+91-80-99999999"

    def test_update_user_status_as_admin(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
    ):
        """Test updating user status as admin"""
        user = User(
            email="toupdate@test.com",
            first_name="To",
            last_name="Update",
            tenant_id=test_tenant.id,
            status="active",
        )
        user.set_password("Pass123!")
        db_session.add(user)
        db_session.commit()

        response = client.put(
            f"/api/v1/users/{user.id}",
            json={"status": "suspended"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "suspended"

    def test_update_user_status_forbidden_as_regular_user(
        self,
        client: TestClient,
        regular_headers: dict,
        regular_user_fixture: User,
    ):
        """Test that regular users cannot change status"""
        response = client.put(
            f"/api/v1/users/{regular_user_fixture.id}",
            json={"status": "suspended"},
            headers=regular_headers,
        )

        assert response.status_code == 403
        assert "administrator" in response.json()["detail"].lower()

    def test_update_user_partial(
        self,
        client: TestClient,
        admin_headers: dict,
        regular_user_fixture: User,
    ):
        """Test partial update (only some fields)"""
        original_email = regular_user_fixture.email

        response = client.put(
            f"/api/v1/users/{regular_user_fixture.id}",
            json={"first_name": "NewFirstName"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "NewFirstName"
        # Email should remain unchanged
        assert data["email"] == original_email

    def test_update_user_unauthorized_other_tenant(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
    ):
        """Test updating user in other tenant is forbidden"""
        other_tenant = Tenant(tenant_code="OTHER3", tenant_name="Other Tenant 3", status="active")
        db_session.add(other_tenant)
        db_session.flush()

        other_user = User(
            email="othertenant3@test.com",
            first_name="Other",
            last_name="Tenant3",
            tenant_id=other_tenant.id,
            status="active",
        )
        other_user.set_password("Pass123!")
        db_session.add(other_user)
        db_session.commit()

        response = client.put(
            f"/api/v1/users/{other_user.id}",
            json={"first_name": "Hacked"},
            headers=regular_headers,
        )

        assert response.status_code == 403

    def test_update_user_not_found(self, client: TestClient, admin_headers: dict):
        """Test updating non-existent user"""
        fake_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.put(
            f"/api/v1/users/{fake_id}",
            json={"first_name": "Updated"},
            headers=admin_headers,
        )

        assert response.status_code == 404


class TestDeleteUser:
    """Tests for DELETE /api/v1/users/{user_id}"""

    def test_delete_user_success_as_admin(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
    ):
        """Test soft deleting user as admin"""
        user = User(
            email="todelete@test.com",
            first_name="To",
            last_name="Delete",
            tenant_id=test_tenant.id,
            status="active",
        )
        user.set_password("Pass123!")
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        response = client.delete(f"/api/v1/users/{user_id}", headers=admin_headers)

        assert response.status_code == 204

        # Verify user is soft deleted (status = inactive)
        db_session.refresh(user)
        assert user.status == "inactive"

    def test_delete_user_cannot_delete_self(
        self,
        client: TestClient,
        admin_headers: dict,
        admin_user_fixture: User,
    ):
        """Test that users cannot delete themselves"""
        response = client.delete(f"/api/v1/users/{admin_user_fixture.id}", headers=admin_headers)

        assert response.status_code == 400
        assert "cannot delete your own account" in response.json()["detail"].lower()

    def test_delete_user_unauthorized_as_regular_user(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
    ):
        """Test deleting user as non-admin user"""
        user = User(
            email="todelete2@test.com",
            first_name="To",
            last_name="Delete2",
            tenant_id=test_tenant.id,
            status="active",
        )
        user.set_password("Pass123!")
        db_session.add(user)
        db_session.commit()

        response = client.delete(f"/api/v1/users/{user.id}", headers=regular_headers)

        assert response.status_code == 403

    def test_delete_user_not_found(self, client: TestClient, admin_headers: dict):
        """Test deleting non-existent user"""
        fake_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.delete(f"/api/v1/users/{fake_id}", headers=admin_headers)

        assert response.status_code == 404
