"""
Integration tests for Compliance Instance API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta

from app.models import Tenant, User, Role, Entity, ComplianceMaster, ComplianceInstance
from app.models.role import user_roles
from app.models.entity import entity_access
from app.core.security import create_access_token


@pytest.fixture
def test_tenant(db_session: Session):
    """Create a test tenant"""
    tenant = Tenant(
        tenant_code="TEST_CI",
        tenant_name="Test CI Tenant",
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
        email="admin@ci.com",
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
        email="user@ci.com",
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
        entity_code="TEST-CI-001",
        entity_name="Test CI Entity",
        entity_type="Company",
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
def test_compliance_master(db_session: Session, test_tenant: Tenant):
    """Create a test compliance master"""
    master = ComplianceMaster(
        tenant_id=test_tenant.id,
        compliance_code="GST_GSTR3B",
        compliance_name="GSTR-3B Monthly Return",
        category="GST",
        sub_category="Monthly Returns",
        frequency="Monthly",
        due_date_rule={"type": "monthly", "day": 20},
        is_active=True,
    )
    db_session.add(master)
    db_session.commit()
    db_session.refresh(master)
    return master


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


class TestCreateComplianceInstance:
    """Tests for POST /api/v1/compliance-instances"""

    def test_create_instance_success(
        self,
        client: TestClient,
        admin_headers: dict,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
    ):
        """Test creating a compliance instance successfully"""
        today = date.today()
        response = client.post(
            "/api/v1/compliance-instances/",
            json={
                "compliance_master_id": str(test_compliance_master.id),
                "entity_id": str(test_entity.id),
                "period_start": str(today),
                "period_end": str(today + timedelta(days=30)),
                "due_date": str(today + timedelta(days=40)),
                "status": "Not Started",
                "rag_status": "Green",
            },
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["compliance_code"] == test_compliance_master.compliance_code
        assert data["entity_code"] == test_entity.entity_code
        assert data["status"] == "Not Started"
        assert data["rag_status"] == "Green"
        assert "compliance_instance_id" in data

    def test_create_instance_with_owner(
        self,
        client: TestClient,
        admin_headers: dict,
        admin_user_fixture: User,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
    ):
        """Test creating instance with owner and approver"""
        today = date.today()
        response = client.post(
            "/api/v1/compliance-instances/",
            json={
                "compliance_master_id": str(test_compliance_master.id),
                "entity_id": str(test_entity.id),
                "period_start": str(today),
                "period_end": str(today + timedelta(days=30)),
                "due_date": str(today + timedelta(days=40)),
                "owner_user_id": str(admin_user_fixture.id),
                "approver_user_id": str(admin_user_fixture.id),
            },
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["owner_id"] == str(admin_user_fixture.id)
        assert data["approver_id"] == str(admin_user_fixture.id)

    def test_create_instance_duplicate_period(
        self,
        client: TestClient,
        admin_headers: dict,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
    ):
        """Test creating duplicate instance for same period"""
        today = date.today()
        period_start = today
        period_end = today + timedelta(days=30)

        # Create first instance
        client.post(
            "/api/v1/compliance-instances/",
            json={
                "compliance_master_id": str(test_compliance_master.id),
                "entity_id": str(test_entity.id),
                "period_start": str(period_start),
                "period_end": str(period_end),
                "due_date": str(today + timedelta(days=40)),
            },
            headers=admin_headers,
        )

        # Try to create duplicate
        response = client.post(
            "/api/v1/compliance-instances/",
            json={
                "compliance_master_id": str(test_compliance_master.id),
                "entity_id": str(test_entity.id),
                "period_start": str(period_start),
                "period_end": str(period_end),
                "due_date": str(today + timedelta(days=40)),
            },
            headers=admin_headers,
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_create_instance_invalid_master(
        self, client: TestClient, admin_headers: dict, test_entity: Entity
    ):
        """Test creating instance with invalid compliance master ID"""
        today = date.today()
        fake_master_id = "123e4567-e89b-12d3-a456-426614174999"

        response = client.post(
            "/api/v1/compliance-instances/",
            json={
                "compliance_master_id": fake_master_id,
                "entity_id": str(test_entity.id),
                "period_start": str(today),
                "period_end": str(today + timedelta(days=30)),
                "due_date": str(today + timedelta(days=40)),
            },
            headers=admin_headers,
        )

        assert response.status_code == 404
        assert "compliance master not found" in response.json()["detail"].lower()

    def test_create_instance_invalid_entity(
        self, client: TestClient, admin_headers: dict, test_compliance_master: ComplianceMaster
    ):
        """Test creating instance with invalid entity ID"""
        today = date.today()
        fake_entity_id = "123e4567-e89b-12d3-a456-426614174999"

        response = client.post(
            "/api/v1/compliance-instances/",
            json={
                "compliance_master_id": str(test_compliance_master.id),
                "entity_id": fake_entity_id,
                "period_start": str(today),
                "period_end": str(today + timedelta(days=30)),
                "due_date": str(today + timedelta(days=40)),
            },
            headers=admin_headers,
        )

        assert response.status_code == 404
        assert "entity not found" in response.json()["detail"].lower()

    def test_create_instance_no_entity_access(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test creating instance for entity without access"""
        # Create entity without granting access to regular user
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="NO-ACCESS",
            entity_name="No Access Entity",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(entity)
        db_session.commit()

        today = date.today()
        response = client.post(
            "/api/v1/compliance-instances/",
            json={
                "compliance_master_id": str(test_compliance_master.id),
                "entity_id": str(entity.id),
                "period_start": str(today),
                "period_end": str(today + timedelta(days=30)),
                "due_date": str(today + timedelta(days=40)),
            },
            headers=regular_headers,
        )

        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()

    def test_create_instance_no_auth(
        self, client: TestClient, test_entity: Entity, test_compliance_master: ComplianceMaster
    ):
        """Test creating instance without authentication"""
        today = date.today()
        response = client.post(
            "/api/v1/compliance-instances/",
            json={
                "compliance_master_id": str(test_compliance_master.id),
                "entity_id": str(test_entity.id),
                "period_start": str(today),
                "period_end": str(today + timedelta(days=30)),
                "due_date": str(today + timedelta(days=40)),
            },
        )

        assert response.status_code in [401, 403]


class TestListComplianceInstances:
    """Tests for GET /api/v1/compliance-instances"""

    def test_list_instances_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test listing compliance instances"""
        # Create test instances
        today = date.today()
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=test_entity.id,
            period_start=today,
            period_end=today + timedelta(days=30),
            due_date=today + timedelta(days=40),
            status="Not Started",
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(instance)
        db_session.commit()

        response = client.get("/api/v1/compliance-instances/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_list_instances_with_pagination(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test compliance instance list pagination"""
        # Create multiple instances
        today = date.today()
        for i in range(5):
            instance = ComplianceInstance(
                tenant_id=test_tenant.id,
                compliance_master_id=test_compliance_master.id,
                entity_id=test_entity.id,
                period_start=today + timedelta(days=i * 30),
                period_end=today + timedelta(days=(i + 1) * 30),
                due_date=today + timedelta(days=(i + 1) * 30 + 10),
                status="Not Started",
                rag_status="Green",
                created_by=admin_user_fixture.id,
                updated_by=admin_user_fixture.id,
            )
            db_session.add(instance)
        db_session.commit()

        response = client.get("/api/v1/compliance-instances/?skip=0&limit=3", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 3
        assert len(data["items"]) <= 3

    def test_list_instances_filter_by_entity(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test filtering instances by entity"""
        # Create instance for test entity
        today = date.today()
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=test_entity.id,
            period_start=today,
            period_end=today + timedelta(days=30),
            due_date=today + timedelta(days=40),
            status="Not Started",
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(instance)
        db_session.commit()

        response = client.get(
            f"/api/v1/compliance-instances/?entity_id={test_entity.id}", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert all(item["entity_id"] == str(test_entity.id) for item in data["items"])

    def test_list_instances_filter_by_status(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test filtering instances by status"""
        today = date.today()
        # Create instances with different statuses
        instance1 = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=test_entity.id,
            period_start=today,
            period_end=today + timedelta(days=30),
            due_date=today + timedelta(days=40),
            status="Not Started",
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        instance2 = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=test_entity.id,
            period_start=today - timedelta(days=30),
            period_end=today,
            due_date=today + timedelta(days=10),
            status="In Progress",
            rag_status="Amber",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add_all([instance1, instance2])
        db_session.commit()

        response = client.get(
            "/api/v1/compliance-instances/?status=In Progress", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert all(item["status"] == "In Progress" for item in data["items"])

    def test_list_instances_filter_by_rag(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test filtering instances by RAG status"""
        today = date.today()
        # Create instances with different RAG statuses
        instance1 = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=test_entity.id,
            period_start=today,
            period_end=today + timedelta(days=30),
            due_date=today + timedelta(days=40),
            status="Not Started",
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        instance2 = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=test_entity.id,
            period_start=today - timedelta(days=30),
            period_end=today,
            due_date=today + timedelta(days=5),
            status="In Progress",
            rag_status="Amber",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add_all([instance1, instance2])
        db_session.commit()

        response = client.get(
            "/api/v1/compliance-instances/?rag_status=Green", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert all(item["rag_status"] == "Green" for item in data["items"])

    def test_list_instances_filter_by_category(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_entity: Entity,
        admin_user_fixture: User,
    ):
        """Test filtering instances by category"""
        # Create masters with different categories
        gst_master = ComplianceMaster(
            tenant_id=test_tenant.id,
            compliance_code="GST_TEST",
            compliance_name="GST Test",
            category="GST",
            frequency="Monthly",
            due_date_rule={},
            is_active=True,
        )
        tax_master = ComplianceMaster(
            tenant_id=test_tenant.id,
            compliance_code="TAX_TEST",
            compliance_name="Tax Test",
            category="Direct Tax",
            frequency="Quarterly",
            due_date_rule={},
            is_active=True,
        )
        db_session.add_all([gst_master, tax_master])
        db_session.flush()

        today = date.today()
        gst_instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=gst_master.id,
            entity_id=test_entity.id,
            period_start=today,
            period_end=today + timedelta(days=30),
            due_date=today + timedelta(days=40),
            status="Not Started",
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(gst_instance)
        db_session.commit()

        response = client.get("/api/v1/compliance-instances/?category=GST", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert all(item["category"] == "GST" for item in data["items"])

    def test_list_instances_entity_access_filtering(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        regular_user_fixture: User,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test that regular users only see instances for entities they have access to"""
        # Create entity with access
        accessible_entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="ACCESSIBLE",
            entity_name="Accessible Entity",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(accessible_entity)
        db_session.flush()

        # Grant access
        db_session.execute(
            entity_access.insert().values(
                user_id=regular_user_fixture.id,
                entity_id=accessible_entity.id,
                tenant_id=test_tenant.id,
            )
        )

        # Create entity without access
        no_access_entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="NO-ACCESS",
            entity_name="No Access Entity",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(no_access_entity)
        db_session.flush()

        # Create instances for both
        today = date.today()
        accessible_instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=accessible_entity.id,
            period_start=today,
            period_end=today + timedelta(days=30),
            due_date=today + timedelta(days=40),
            status="Not Started",
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        no_access_instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=no_access_entity.id,
            period_start=today,
            period_end=today + timedelta(days=30),
            due_date=today + timedelta(days=40),
            status="Not Started",
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add_all([accessible_instance, no_access_instance])
        db_session.commit()

        # Regular user should only see accessible instance
        response = client.get("/api/v1/compliance-instances/", headers=regular_headers)

        assert response.status_code == 200
        data = response.json()
        entity_ids = [item["entity_id"] for item in data["items"]]
        assert str(accessible_entity.id) in entity_ids
        assert str(no_access_entity.id) not in entity_ids


class TestGetComplianceInstance:
    """Tests for GET /api/v1/compliance-instances/{instance_id}"""

    def test_get_instance_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test getting a compliance instance by ID"""
        today = date.today()
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=test_entity.id,
            period_start=today,
            period_end=today + timedelta(days=30),
            due_date=today + timedelta(days=40),
            status="Not Started",
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(instance)
        db_session.commit()

        response = client.get(f"/api/v1/compliance-instances/{instance.id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["compliance_instance_id"] == str(instance.id)
        assert data["compliance_code"] == test_compliance_master.compliance_code
        assert data["entity_code"] == test_entity.entity_code

    def test_get_instance_with_access(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        regular_user_fixture: User,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test getting instance for entity with access"""
        # Create entity and grant access
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="ACCESSIBLE",
            entity_name="Accessible Entity",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(entity)
        db_session.flush()

        db_session.execute(
            entity_access.insert().values(
                user_id=regular_user_fixture.id,
                entity_id=entity.id,
                tenant_id=test_tenant.id,
            )
        )

        # Create instance
        today = date.today()
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=entity.id,
            period_start=today,
            period_end=today + timedelta(days=30),
            due_date=today + timedelta(days=40),
            status="Not Started",
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(instance)
        db_session.commit()

        response = client.get(
            f"/api/v1/compliance-instances/{instance.id}", headers=regular_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["compliance_instance_id"] == str(instance.id)

    def test_get_instance_without_access(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test getting instance for entity without access"""
        # Create entity without granting access
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="NO-ACCESS",
            entity_name="No Access Entity",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(entity)
        db_session.flush()

        # Create instance
        today = date.today()
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=entity.id,
            period_start=today,
            period_end=today + timedelta(days=30),
            due_date=today + timedelta(days=40),
            status="Not Started",
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(instance)
        db_session.commit()

        response = client.get(
            f"/api/v1/compliance-instances/{instance.id}", headers=regular_headers
        )

        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()

    def test_get_instance_not_found(self, client: TestClient, admin_headers: dict):
        """Test getting non-existent instance"""
        fake_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.get(f"/api/v1/compliance-instances/{fake_id}", headers=admin_headers)

        assert response.status_code == 404


class TestUpdateComplianceInstance:
    """Tests for PUT /api/v1/compliance-instances/{instance_id}"""

    def test_update_instance_status(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test updating instance status"""
        today = date.today()
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=test_entity.id,
            period_start=today,
            period_end=today + timedelta(days=30),
            due_date=today + timedelta(days=40),
            status="Not Started",
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(instance)
        db_session.commit()

        response = client.put(
            f"/api/v1/compliance-instances/{instance.id}",
            json={"status": "In Progress"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "In Progress"

    def test_update_instance_partial(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test partial update of instance"""
        today = date.today()
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=test_entity.id,
            period_start=today,
            period_end=today + timedelta(days=30),
            due_date=today + timedelta(days=40),
            status="Not Started",
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(instance)
        db_session.commit()

        original_status = instance.status

        response = client.put(
            f"/api/v1/compliance-instances/{instance.id}",
            json={"remarks": "Updated remarks"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["remarks"] == "Updated remarks"
        assert data["status"] == original_status  # Should remain unchanged

    def test_update_instance_completion(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test marking instance as completed"""
        today = date.today()
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=test_entity.id,
            period_start=today,
            period_end=today + timedelta(days=30),
            due_date=today + timedelta(days=40),
            status="In Progress",
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(instance)
        db_session.commit()

        completion_date = str(date.today())
        response = client.put(
            f"/api/v1/compliance-instances/{instance.id}",
            json={
                "status": "Filed",
                "completion_date": completion_date,
                "completion_remarks": "Filed successfully",
            },
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Filed"
        assert data["completion_date"] == completion_date
        assert data["completion_remarks"] == "Filed successfully"

    def test_update_instance_without_access(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test updating instance without entity access"""
        # Create entity without access
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="NO-ACCESS",
            entity_name="No Access Entity",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(entity)
        db_session.flush()

        today = date.today()
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=entity.id,
            period_start=today,
            period_end=today + timedelta(days=30),
            due_date=today + timedelta(days=40),
            status="Not Started",
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(instance)
        db_session.commit()

        response = client.put(
            f"/api/v1/compliance-instances/{instance.id}",
            json={"status": "Hacked"},
            headers=regular_headers,
        )

        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()

    def test_update_instance_not_found(self, client: TestClient, admin_headers: dict):
        """Test updating non-existent instance"""
        fake_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.put(
            f"/api/v1/compliance-instances/{fake_id}",
            json={"status": "In Progress"},
            headers=admin_headers,
        )

        assert response.status_code == 404


class TestRecalculateStatus:
    """Tests for POST /api/v1/compliance-instances/{instance_id}/recalculate-status"""

    def test_recalculate_overdue_status(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test recalculation for overdue instance"""
        # Create instance that's overdue
        overdue_date = date.today() - timedelta(days=5)
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=test_entity.id,
            period_start=overdue_date - timedelta(days=30),
            period_end=overdue_date,
            due_date=overdue_date,
            status="Not Started",
            rag_status="Green",  # Wrong status
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(instance)
        db_session.commit()

        response = client.post(
            f"/api/v1/compliance-instances/{instance.id}/recalculate-status",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rag_status"] == "Red"
        assert data["status"] == "Overdue"

    def test_recalculate_red_status_due_soon(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test recalculation for instance due in <3 days"""
        # Create instance due in 1 day
        due_date = date.today() + timedelta(days=1)
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=test_entity.id,
            period_start=due_date - timedelta(days=30),
            period_end=due_date,
            due_date=due_date,
            status="In Progress",
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(instance)
        db_session.commit()

        response = client.post(
            f"/api/v1/compliance-instances/{instance.id}/recalculate-status",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rag_status"] == "Red"

    def test_recalculate_amber_status(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test recalculation for instance due in 3-7 days"""
        # Create instance due in 5 days
        due_date = date.today() + timedelta(days=5)
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=test_entity.id,
            period_start=due_date - timedelta(days=30),
            period_end=due_date,
            due_date=due_date,
            status="In Progress",
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(instance)
        db_session.commit()

        response = client.post(
            f"/api/v1/compliance-instances/{instance.id}/recalculate-status",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rag_status"] == "Amber"

    def test_recalculate_green_status(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test recalculation for instance due in >7 days"""
        # Create instance due in 20 days
        due_date = date.today() + timedelta(days=20)
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=test_entity.id,
            period_start=due_date - timedelta(days=30),
            period_end=due_date,
            due_date=due_date,
            status="Not Started",
            rag_status="Red",  # Wrong status
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(instance)
        db_session.commit()

        response = client.post(
            f"/api/v1/compliance-instances/{instance.id}/recalculate-status",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rag_status"] == "Green"

    def test_recalculate_completed_always_green(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test that completed instances are always Green"""
        # Create completed instance that's overdue
        overdue_date = date.today() - timedelta(days=10)
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=test_entity.id,
            period_start=overdue_date - timedelta(days=30),
            period_end=overdue_date,
            due_date=overdue_date,
            status="Filed",
            rag_status="Red",  # Should become Green
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(instance)
        db_session.commit()

        response = client.post(
            f"/api/v1/compliance-instances/{instance.id}/recalculate-status",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rag_status"] == "Green"
        assert data["status"] == "Filed"

    def test_recalculate_with_blocking_dependency(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_entity: Entity,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test recalculation with blocking dependencies"""
        # Create blocking instance (not completed)
        today = date.today()
        blocking_instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=test_entity.id,
            period_start=today - timedelta(days=60),
            period_end=today - timedelta(days=30),
            due_date=today - timedelta(days=20),
            status="In Progress",
            rag_status="Red",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(blocking_instance)
        db_session.flush()

        # Create instance with blocker
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=test_entity.id,
            period_start=today,
            period_end=today + timedelta(days=30),
            due_date=today + timedelta(days=40),
            status="Not Started",
            rag_status="Green",
            blocking_compliance_instance_id=blocking_instance.id,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(instance)
        db_session.commit()

        response = client.post(
            f"/api/v1/compliance-instances/{instance.id}/recalculate-status",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rag_status"] == "Amber"  # At least Amber when blocked
        assert data["status"] == "Blocked"

    def test_recalculate_without_access(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test recalculation without entity access"""
        # Create entity without access
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="NO-ACCESS",
            entity_name="No Access Entity",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(entity)
        db_session.flush()

        today = date.today()
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=entity.id,
            period_start=today,
            period_end=today + timedelta(days=30),
            due_date=today + timedelta(days=40),
            status="Not Started",
            rag_status="Green",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(instance)
        db_session.commit()

        response = client.post(
            f"/api/v1/compliance-instances/{instance.id}/recalculate-status",
            headers=regular_headers,
        )

        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()

    def test_recalculate_not_found(self, client: TestClient, admin_headers: dict):
        """Test recalculating non-existent instance"""
        fake_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.post(
            f"/api/v1/compliance-instances/{fake_id}/recalculate-status",
            headers=admin_headers,
        )

        assert response.status_code == 404
