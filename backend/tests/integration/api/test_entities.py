"""
Integration tests for Entity API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Tenant, User, Role, Entity
from app.models.role import user_roles
from app.models.entity import entity_access
from app.core.security import create_access_token


@pytest.fixture
def test_tenant(db_session: Session):
    """Create a test tenant"""
    tenant = Tenant(
        tenant_code="TEST_ENT",
        tenant_name="Test Entity Tenant",
        status="active",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def admin_user_fixture(db_session: Session, test_tenant: Tenant):
    """Create a tenant admin user for testing"""
    # Check if admin role exists
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
        email="admin@entities.com",
        first_name="Admin",
        last_name="User",
        tenant_id=test_tenant.id,
        status="active",
        is_system_admin=False,
    )
    admin.set_password("AdminPass123!")  # pragma: allowlist secret
    db_session.add(admin)
    db_session.flush()

    # Assign role
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
def regular_user_fixture(db_session: Session, test_tenant: Tenant):
    """Create a regular (non-admin) user for testing"""
    user = User(
        email="user@entities.com",
        first_name="Regular",
        last_name="User",
        tenant_id=test_tenant.id,
        status="active",
        is_system_admin=False,
    )
    user.set_password("UserPass123!")  # pragma: allowlist secret
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_entity(db_session: Session, test_tenant: Tenant, admin_user_fixture: User):
    """Create a test entity"""
    entity = Entity(
        tenant_id=test_tenant.id,
        entity_code="TEST-001",
        entity_name="Test Entity One",
        entity_type="Company",
        pan="AAAPL1234C",
        gstin="27AAAPL1234C1Z5",
        status="active",
        created_by=admin_user_fixture.id,
        updated_by=admin_user_fixture.id,
    )
    db_session.add(entity)
    db_session.flush()

    # Grant access to admin
    db_session.execute(
        entity_access.insert().values(
            user_id=admin_user_fixture.id,
            entity_id=entity.id,
            tenant_id=test_tenant.id,
        )
    )
    db_session.commit()
    db_session.refresh(entity)
    return entity


@pytest.fixture
def admin_headers(admin_user_fixture: User):
    """Create auth headers for tenant admin user"""
    token = create_access_token(
        data={
            "user_id": str(admin_user_fixture.id),
            "tenant_id": str(admin_user_fixture.tenant_id),
            "email": admin_user_fixture.email,
            "roles": ["TENANT_ADMIN"],
            "is_system_admin": False,
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


class TestCreateEntity:
    """Tests for POST /api/v1/entities"""

    def test_create_entity_success(self, client: TestClient, admin_headers: dict, test_tenant: Tenant):
        """Test creating an entity as tenant admin"""
        response = client.post(
            "/api/v1/entities/",
            json={
                "entity_code": "ACME-MUM",
                "entity_name": "Acme Corporation Mumbai",
                "entity_type": "Company",
                "pan": "AAAPL1234C",
                "gstin": "27AAAPL1234C1Z5",  # pragma: allowlist secret
                "city": "Mumbai",
                "state": "Maharashtra",
            },
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["entity_code"] == "ACME-MUM"
        assert data["entity_name"] == "Acme Corporation Mumbai"
        assert data["entity_type"] == "Company"
        assert data["pan"] == "AAAPL1234C"
        assert data["status"] == "active"
        assert data["users_with_access_count"] == 1  # Creator auto-granted access
        assert "id" in data

    def test_create_entity_duplicate_code(self, client: TestClient, admin_headers: dict, test_entity: Entity):
        """Test creating entity with duplicate code"""
        response = client.post(
            "/api/v1/entities/",
            json={
                "entity_code": test_entity.entity_code,  # Duplicate
                "entity_name": "Another Entity",
                "entity_type": "Company",
            },
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_create_entity_invalid_pan(self, client: TestClient, admin_headers: dict):
        """Test creating entity with invalid PAN format"""
        response = client.post(
            "/api/v1/entities/",
            json={
                "entity_code": "INVALID-PAN",
                "entity_name": "Invalid PAN Entity",
                "pan": "INVALID",  # Wrong format
            },
            headers=admin_headers,
        )

        assert response.status_code == 422  # Validation error

    def test_create_entity_invalid_gstin(self, client: TestClient, admin_headers: dict):
        """Test creating entity with invalid GSTIN format"""
        response = client.post(
            "/api/v1/entities/",
            json={
                "entity_code": "INVALID-GST",
                "entity_name": "Invalid GSTIN Entity",
                "gstin": "INVALID",  # Wrong format
            },
            headers=admin_headers,
        )

        assert response.status_code == 422

    def test_create_entity_unauthorized_regular_user(self, client: TestClient, regular_headers: dict):
        """Test creating entity as non-admin user"""
        response = client.post(
            "/api/v1/entities/",
            json={
                "entity_code": "UNAUTH",
                "entity_name": "Unauthorized Entity",
            },
            headers=regular_headers,
        )

        assert response.status_code == 403
        assert "administrator" in response.json()["detail"].lower()

    def test_create_entity_no_auth(self, client: TestClient):
        """Test creating entity without authentication"""
        response = client.post(
            "/api/v1/entities/",
            json={
                "entity_code": "NOAUTH",
                "entity_name": "No Auth Entity",
            },
        )

        assert response.status_code in [401, 403]


class TestListEntities:
    """Tests for GET /api/v1/entities"""

    def test_list_entities_as_admin(self, client: TestClient, admin_headers: dict, test_entity: Entity):
        """Test listing entities as tenant admin"""
        response = client.get("/api/v1/entities/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_list_entities_with_pagination(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        admin_user_fixture: User,
    ):
        """Test entity list pagination"""
        # Create multiple entities
        for i in range(5):
            entity = Entity(
                tenant_id=test_tenant.id,
                entity_code=f"TEST-{i:03d}",
                entity_name=f"Test Entity {i}",
                status="active",
                created_by=admin_user_fixture.id,
                updated_by=admin_user_fixture.id,
            )
            db_session.add(entity)
        db_session.commit()

        # Test pagination
        response = client.get("/api/v1/entities/?skip=0&limit=3", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 3
        assert len(data["items"]) <= 3

    def test_list_entities_with_status_filter(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        admin_user_fixture: User,
    ):
        """Test filtering entities by status"""
        # Create entities with different statuses
        active_entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="ACTIVE-001",
            entity_name="Active Entity",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        inactive_entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="INACTIVE-001",
            entity_name="Inactive Entity",
            status="inactive",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add_all([active_entity, inactive_entity])
        db_session.commit()

        # Filter by active status
        response = client.get("/api/v1/entities/?entity_status=active", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert all(e["status"] == "active" for e in data["items"])

    def test_list_entities_with_search(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        admin_user_fixture: User,
    ):
        """Test searching entities by name or code"""
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="SEARCH-001",
            entity_name="Searchable Entity Name",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(entity)
        db_session.commit()

        # Search by name
        response = client.get("/api/v1/entities/?search=Searchable", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any("Searchable" in e["entity_name"] for e in data["items"])

    def test_list_entities_tenant_isolation(self, client: TestClient, admin_headers: dict, db_session: Session):
        """Test that tenant admins only see entities in their tenant"""
        # Create another tenant with entity
        other_tenant = Tenant(
            tenant_code="OTHER_ENT",
            tenant_name="Other Entity Tenant",
            status="active",
        )
        db_session.add(other_tenant)
        db_session.flush()

        other_entity = Entity(
            tenant_id=other_tenant.id,
            entity_code="OTHER-001",
            entity_name="Other Tenant Entity",
            status="active",
        )
        db_session.add(other_entity)
        db_session.commit()

        # Admin should not see other tenant's entities
        response = client.get("/api/v1/entities/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        entity_codes = [e["entity_code"] for e in data["items"]]
        assert "OTHER-001" not in entity_codes

    def test_list_entities_entity_access_filtering(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        regular_user_fixture: User,
        admin_user_fixture: User,
    ):
        """Test that regular users only see entities they have access to"""
        # Create entity user has access to
        accessible_entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="ACCESSIBLE-001",
            entity_name="Accessible Entity",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(accessible_entity)
        db_session.flush()

        # Grant access to regular user
        db_session.execute(
            entity_access.insert().values(
                user_id=regular_user_fixture.id,
                entity_id=accessible_entity.id,
                tenant_id=test_tenant.id,
            )
        )

        # Create entity user doesn't have access to
        no_access_entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="NO-ACCESS-001",
            entity_name="No Access Entity",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(no_access_entity)
        db_session.commit()

        # User should only see accessible entity
        response = client.get("/api/v1/entities/", headers=regular_headers)

        assert response.status_code == 200
        data = response.json()
        entity_codes = [e["entity_code"] for e in data["items"]]
        assert "ACCESSIBLE-001" in entity_codes
        assert "NO-ACCESS-001" not in entity_codes


class TestGetEntity:
    """Tests for GET /api/v1/entities/{entity_id}"""

    def test_get_entity_success_as_admin(self, client: TestClient, admin_headers: dict, test_entity: Entity):
        """Test getting entity as tenant admin"""
        response = client.get(f"/api/v1/entities/{test_entity.id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_entity.id)
        assert data["entity_code"] == test_entity.entity_code

    def test_get_entity_with_access_as_regular_user(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        regular_user_fixture: User,
        admin_user_fixture: User,
    ):
        """Test getting entity user has access to"""
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="ACCESSIBLE-002",
            entity_name="Accessible Entity 2",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(entity)
        db_session.flush()

        # Grant access
        db_session.execute(
            entity_access.insert().values(
                user_id=regular_user_fixture.id,
                entity_id=entity.id,
                tenant_id=test_tenant.id,
            )
        )
        db_session.commit()

        response = client.get(f"/api/v1/entities/{entity.id}", headers=regular_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(entity.id)

    def test_get_entity_without_access_forbidden(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        admin_user_fixture: User,
    ):
        """Test getting entity user doesn't have access to"""
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="NO-ACCESS-002",
            entity_name="No Access Entity 2",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(entity)
        db_session.commit()

        response = client.get(f"/api/v1/entities/{entity.id}", headers=regular_headers)

        assert response.status_code == 403
        assert "access" in response.json()["detail"].lower()

    def test_get_entity_not_found(self, client: TestClient, admin_headers: dict):
        """Test getting non-existent entity"""
        fake_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.get(f"/api/v1/entities/{fake_id}", headers=admin_headers)

        assert response.status_code == 404


class TestUpdateEntity:
    """Tests for PUT /api/v1/entities/{entity_id}"""

    def test_update_entity_success(self, client: TestClient, admin_headers: dict, test_entity: Entity):
        """Test updating entity as tenant admin"""
        response = client.put(
            f"/api/v1/entities/{test_entity.id}",
            json={
                "entity_name": "Updated Entity Name",
                "contact_email": "updated@entity.com",
            },
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["entity_name"] == "Updated Entity Name"
        assert data["contact_email"] == "updated@entity.com"

    def test_update_entity_partial(self, client: TestClient, admin_headers: dict, test_entity: Entity):
        """Test partial update (only some fields)"""
        original_name = test_entity.entity_name

        response = client.put(
            f"/api/v1/entities/{test_entity.id}",
            json={"city": "Bangalore"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["city"] == "Bangalore"
        # entity_name should remain unchanged
        assert data["entity_name"] == original_name

    def test_update_entity_unauthorized_regular_user(
        self, client: TestClient, regular_headers: dict, test_entity: Entity
    ):
        """Test updating entity as non-admin user"""
        response = client.put(
            f"/api/v1/entities/{test_entity.id}",
            json={"entity_name": "Hacked"},
            headers=regular_headers,
        )

        assert response.status_code == 403
        assert "administrator" in response.json()["detail"].lower()

    def test_update_entity_not_found(self, client: TestClient, admin_headers: dict):
        """Test updating non-existent entity"""
        fake_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.put(
            f"/api/v1/entities/{fake_id}",
            json={"entity_name": "Updated"},
            headers=admin_headers,
        )

        assert response.status_code == 404


class TestDeleteEntity:
    """Tests for DELETE /api/v1/entities/{entity_id}"""

    def test_delete_entity_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        admin_user_fixture: User,
    ):
        """Test soft deleting entity as tenant admin"""
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="TO-DELETE",
            entity_name="Entity To Delete",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(entity)
        db_session.commit()
        entity_id = entity.id

        response = client.delete(f"/api/v1/entities/{entity_id}", headers=admin_headers)

        assert response.status_code == 204

        # Verify entity is soft deleted (status = inactive)
        db_session.refresh(entity)
        assert entity.status == "inactive"

    def test_delete_entity_with_active_instances(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        admin_user_fixture: User,
    ):
        """Test deleting entity with active compliance instances"""
        from app.models import ComplianceInstance

        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="HAS-INSTANCES",
            entity_name="Entity With Instances",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(entity)
        db_session.flush()

        # Create a compliance instance (mocking required fields)
        # ComplianceInstance requires compliance_master_id, not compliance_code
        from app.models import ComplianceMaster
        from datetime import date

        # Create a compliance master first
        master = ComplianceMaster(
            tenant_id=test_tenant.id,
            compliance_code="TEST-COMP",
            compliance_name="Test Compliance",
            category="GST",
            frequency="Monthly",
            due_date_rule={},
            is_active=True,
        )
        db_session.add(master)
        db_session.flush()

        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            entity_id=entity.id,
            compliance_master_id=master.id,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            due_date=date(2024, 2, 11),
            status="In Progress",  # Active status
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(instance)
        db_session.commit()

        response = client.delete(f"/api/v1/entities/{entity.id}", headers=admin_headers)

        assert response.status_code == 400
        assert "active compliance instances" in response.json()["detail"].lower()

    def test_delete_entity_unauthorized(self, client: TestClient, regular_headers: dict, test_entity: Entity):
        """Test deleting entity as non-admin user"""
        response = client.delete(f"/api/v1/entities/{test_entity.id}", headers=regular_headers)

        assert response.status_code == 403

    def test_delete_entity_not_found(self, client: TestClient, admin_headers: dict):
        """Test deleting non-existent entity"""
        fake_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.delete(f"/api/v1/entities/{fake_id}", headers=admin_headers)

        assert response.status_code == 404
