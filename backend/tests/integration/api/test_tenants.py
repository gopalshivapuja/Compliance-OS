"""
Integration tests for Tenant API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Tenant, User, Role
from app.core.security import create_access_token


@pytest.fixture
def admin_user(db_session: Session):
    """Create an admin user for testing"""
    # Create tenant for admin
    tenant = Tenant(
        tenant_code="ADMIN_TENANT",
        tenant_name="Admin Tenant",
        status="active",
    )
    db_session.add(tenant)
    db_session.flush()

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
        tenant_id=tenant.id,
        status="active",
        is_system_admin=True,
    )
    admin.set_password("AdminPass123!")
    admin.roles.append(admin_role)
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def admin_headers(admin_user: User):
    """Create auth headers for admin user"""
    token = create_access_token(
        data={
            "user_id": str(admin_user.id),
            "tenant_id": str(admin_user.tenant_id),
            "email": admin_user.email,
            "roles": ["admin"],
            "is_system_admin": True,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def regular_user(db_session: Session):
    """Create a regular (non-admin) user for testing"""
    # Create tenant for regular user
    tenant = Tenant(
        tenant_code="USER_TENANT",
        tenant_name="User Tenant",
        status="active",
    )
    db_session.add(tenant)
    db_session.flush()

    user = User(
        email="user@test.com",
        first_name="Regular",
        last_name="User",
        tenant_id=tenant.id,
        status="active",
        is_system_admin=False,
    )
    user.set_password("UserPass123!")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_headers(regular_user: User):
    """Create auth headers for regular user"""
    token = create_access_token(
        data={
            "user_id": str(regular_user.id),
            "tenant_id": str(regular_user.tenant_id),
            "email": regular_user.email,
            "roles": [],
            "is_system_admin": False,
        }
    )
    return {"Authorization": f"Bearer {token}"}


class TestCreateTenant:
    """Tests for POST /api/v1/tenants"""

    def test_create_tenant_success(self, client: TestClient, admin_headers: dict):
        """Test creating a tenant with valid data"""
        response = client.post(
            "/api/v1/tenants/",
            json={
                "tenant_code": "ACME001",
                "tenant_name": "Acme Corporation",
                "contact_email": "admin@acme.com",
                "contact_phone": "+91-80-12345678",
                "address": "123 MG Road, Bangalore",
                "status": "active",
            },
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["tenant_code"] == "ACME001"
        assert data["tenant_name"] == "Acme Corporation"
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data

    def test_create_tenant_duplicate_code(
        self, client: TestClient, admin_headers: dict, db_session: Session
    ):
        """Test creating a tenant with duplicate tenant_code"""
        # Create existing tenant
        existing = Tenant(
            tenant_code="DUP001",
            tenant_name="Existing Tenant",
            status="active",
        )
        db_session.add(existing)
        db_session.commit()

        response = client.post(
            "/api/v1/tenants/",
            json={
                "tenant_code": "DUP001",  # Duplicate
                "tenant_name": "Another Corp",
            },
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_create_tenant_unauthorized(self, client: TestClient, regular_headers: dict):
        """Test creating a tenant as non-admin user"""
        response = client.post(
            "/api/v1/tenants/",
            json={
                "tenant_code": "ACME001",
                "tenant_name": "Acme Corporation",
            },
            headers=regular_headers,
        )

        assert response.status_code == 403
        assert "system administrator" in response.json()["detail"].lower()

    def test_create_tenant_no_auth(self, client: TestClient):
        """Test creating a tenant without authentication"""
        response = client.post(
            "/api/v1/tenants/",
            json={
                "tenant_code": "ACME001",
                "tenant_name": "Acme Corporation",
            },
        )

        assert response.status_code == 401

    def test_create_tenant_invalid_data(self, client: TestClient, admin_headers: dict):
        """Test creating a tenant with invalid data"""
        response = client.post(
            "/api/v1/tenants/",
            json={
                "tenant_code": "A",  # Too short (min 2 chars)
                "tenant_name": "Acme Corporation",
            },
            headers=admin_headers,
        )

        assert response.status_code == 422  # Validation error

    def test_create_tenant_missing_required_fields(self, client: TestClient, admin_headers: dict):
        """Test creating a tenant without required fields"""
        response = client.post(
            "/api/v1/tenants/",
            json={
                "tenant_code": "ACME001",
                # Missing tenant_name
            },
            headers=admin_headers,
        )

        assert response.status_code == 422


class TestListTenants:
    """Tests for GET /api/v1/tenants"""

    def test_list_tenants_success(self, client: TestClient, admin_headers: dict):
        """Test listing tenants as admin"""
        response = client.get("/api/v1/tenants/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "tenants" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["total"] >= 1
        assert len(data["tenants"]) >= 1

    def test_list_tenants_with_pagination(
        self, client: TestClient, admin_headers: dict, db_session: Session
    ):
        """Test tenant list pagination"""
        # Create multiple tenants
        for i in range(5):
            tenant = Tenant(
                tenant_code=f"TEST{i:03d}",
                tenant_name=f"Test Tenant {i}",
                status="active",
            )
            db_session.add(tenant)
        db_session.commit()

        # Test first page
        response = client.get("/api/v1/tenants/?page=1&page_size=3", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 3
        assert len(data["tenants"]) <= 3

    def test_list_tenants_with_status_filter(
        self, client: TestClient, admin_headers: dict, db_session: Session
    ):
        """Test filtering tenants by status"""
        # Create tenants with different statuses
        active_tenant = Tenant(
            tenant_code="ACTIVE001", tenant_name="Active Tenant", status="active"
        )
        suspended_tenant = Tenant(
            tenant_code="SUSP001", tenant_name="Suspended Tenant", status="suspended"
        )
        db_session.add_all([active_tenant, suspended_tenant])
        db_session.commit()

        # Filter by active status
        response = client.get("/api/v1/tenants/?status=active", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert all(t["status"] == "active" for t in data["tenants"])

    def test_list_tenants_with_search(
        self, client: TestClient, admin_headers: dict, db_session: Session
    ):
        """Test searching tenants by name or code"""
        tenant = Tenant(
            tenant_code="SEARCH001",
            tenant_name="Searchable Corporation",
            status="active",
        )
        db_session.add(tenant)
        db_session.commit()

        # Search by name
        response = client.get("/api/v1/tenants/?search=Searchable", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any("Searchable" in t["tenant_name"] for t in data["tenants"])

    def test_list_tenants_unauthorized(self, client: TestClient, regular_headers: dict):
        """Test listing tenants as non-admin user"""
        response = client.get("/api/v1/tenants/", headers=regular_headers)

        assert response.status_code == 403


class TestGetTenant:
    """Tests for GET /api/v1/tenants/{tenant_id}"""

    def test_get_tenant_success_own_tenant(
        self, client: TestClient, regular_headers: dict, regular_user: User, db_session: Session
    ):
        """Test getting own tenant as regular user"""
        # Get the user's tenant
        tenant = db_session.query(Tenant).filter(Tenant.id == regular_user.tenant_id).first()

        response = client.get(f"/api/v1/tenants/{tenant.id}", headers=regular_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(tenant.id)
        assert data["tenant_code"] == tenant.tenant_code

    def test_get_tenant_success_admin(
        self, client: TestClient, admin_headers: dict, db_session: Session
    ):
        """Test getting any tenant as admin"""
        # Create another tenant
        other_tenant = Tenant(tenant_code="OTHER001", tenant_name="Other Tenant", status="active")
        db_session.add(other_tenant)
        db_session.commit()

        response = client.get(f"/api/v1/tenants/{other_tenant.id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(other_tenant.id)

    def test_get_tenant_forbidden_other_tenant(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        regular_user: User,
    ):
        """Test that regular user cannot view other tenants"""
        # Create another tenant
        other_tenant = Tenant(tenant_code="OTHER001", tenant_name="Other Tenant", status="active")
        db_session.add(other_tenant)
        db_session.commit()

        response = client.get(f"/api/v1/tenants/{other_tenant.id}", headers=regular_headers)

        assert response.status_code == 403

    def test_get_tenant_not_found(self, client: TestClient, admin_headers: dict):
        """Test getting non-existent tenant"""
        fake_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.get(f"/api/v1/tenants/{fake_id}", headers=admin_headers)

        assert response.status_code == 404


class TestUpdateTenant:
    """Tests for PUT /api/v1/tenants/{tenant_id}"""

    def test_update_tenant_success(
        self, client: TestClient, admin_headers: dict, db_session: Session
    ):
        """Test updating tenant as admin"""
        # Create tenant to update
        tenant = Tenant(
            tenant_code="UPDATE001",
            tenant_name="Original Name",
            status="active",
        )
        db_session.add(tenant)
        db_session.commit()

        response = client.put(
            f"/api/v1/tenants/{tenant.id}",
            json={
                "tenant_name": "Updated Corporation Name",
                "contact_email": "newemail@test.com",
            },
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tenant_name"] == "Updated Corporation Name"
        assert data["contact_email"] == "newemail@test.com"
        # tenant_code should not change
        assert data["tenant_code"] == "UPDATE001"

    def test_update_tenant_unauthorized(
        self, client: TestClient, regular_headers: dict, db_session: Session
    ):
        """Test updating tenant as non-admin user"""
        tenant = Tenant(
            tenant_code="UPDATE002",
            tenant_name="Original Name",
            status="active",
        )
        db_session.add(tenant)
        db_session.commit()

        response = client.put(
            f"/api/v1/tenants/{tenant.id}",
            json={"tenant_name": "Updated Name"},
            headers=regular_headers,
        )

        assert response.status_code == 403

    def test_update_tenant_not_found(self, client: TestClient, admin_headers: dict):
        """Test updating non-existent tenant"""
        fake_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.put(
            f"/api/v1/tenants/{fake_id}",
            json={"tenant_name": "Updated Name"},
            headers=admin_headers,
        )

        assert response.status_code == 404

    def test_update_tenant_partial(
        self, client: TestClient, admin_headers: dict, db_session: Session
    ):
        """Test partial update (only some fields)"""
        tenant = Tenant(
            tenant_code="UPDATE003",
            tenant_name="Original Name",
            contact_email="original@test.com",
            status="active",
        )
        db_session.add(tenant)
        db_session.commit()

        response = client.put(
            f"/api/v1/tenants/{tenant.id}",
            json={"tenant_name": "New Name Only"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tenant_name"] == "New Name Only"
        # Email should remain unchanged
        assert data["contact_email"] == "original@test.com"


class TestDeleteTenant:
    """Tests for DELETE /api/v1/tenants/{tenant_id}"""

    def test_delete_tenant_success(
        self, client: TestClient, admin_headers: dict, db_session: Session
    ):
        """Test soft deleting tenant"""
        # Create tenant without active users
        tenant = Tenant(tenant_code="DELETE001", tenant_name="To Be Deleted", status="active")
        db_session.add(tenant)
        db_session.commit()
        tenant_id = tenant.id

        response = client.delete(f"/api/v1/tenants/{tenant_id}", headers=admin_headers)

        assert response.status_code == 204

        # Verify tenant is soft deleted (status = inactive)
        db_session.refresh(tenant)
        assert tenant.status == "inactive"

    def test_delete_tenant_with_active_users(
        self,
        client: TestClient,
        admin_headers: dict,
        regular_user: User,
        db_session: Session,
    ):
        """Test that tenant with active users cannot be deleted"""
        # Use the regular_user's tenant (which has an active user)
        tenant = db_session.query(Tenant).filter(Tenant.id == regular_user.tenant_id).first()

        response = client.delete(f"/api/v1/tenants/{tenant.id}", headers=admin_headers)

        assert response.status_code == 400
        assert "active users" in response.json()["detail"].lower()

    def test_delete_tenant_unauthorized(
        self, client: TestClient, regular_headers: dict, db_session: Session
    ):
        """Test deleting tenant as non-admin user"""
        tenant = Tenant(tenant_code="DELETE002", tenant_name="To Be Deleted", status="active")
        db_session.add(tenant)
        db_session.commit()

        response = client.delete(f"/api/v1/tenants/{tenant.id}", headers=regular_headers)

        assert response.status_code == 403

    def test_delete_tenant_not_found(self, client: TestClient, admin_headers: dict):
        """Test deleting non-existent tenant"""
        fake_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.delete(f"/api/v1/tenants/{fake_id}", headers=admin_headers)

        assert response.status_code == 404
