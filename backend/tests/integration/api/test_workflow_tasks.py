"""
Integration tests for Workflow Task API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta

from app.models import (
    Tenant,
    User,
    Role,
    Entity,
    ComplianceMaster,
    ComplianceInstance,
    WorkflowTask,
)
from app.models.role import user_roles
from app.models.entity import entity_access
from app.core.security import create_access_token


@pytest.fixture
def test_tenant(db_session: Session):
    """Create a test tenant"""
    tenant = Tenant(
        tenant_code="TEST_WT",
        tenant_name="Test WT Tenant",
        status="active",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def admin_user_fixture(db_session: Session, test_tenant: Tenant):
    """Create a tenant admin user for testing"""
    admin_role = db_session.query(Role).filter(Role.role_code == "admin").first()
    if not admin_role:
        admin_role = Role(
            role_code="admin",
            role_name="Administrator",
        )
        db_session.add(admin_role)
        db_session.flush()

    admin = User(
        email="admin@wt.com",
        first_name="Admin",
        last_name="User",
        tenant_id=test_tenant.id,
        status="active",
        is_system_admin=False,
    )
    admin.set_password("AdminPass123!")  # pragma: allowlist secret
    db_session.add(admin)
    db_session.flush()

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
        email="user@wt.com",
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
        entity_code="TEST-WT-001",
        entity_name="Test WT Entity",
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
        compliance_code="WT_TEST",
        compliance_name="Workflow Test Compliance",
        category="GST",
        frequency="Monthly",
        due_date_rule={},
        is_active=True,
    )
    db_session.add(master)
    db_session.commit()
    db_session.refresh(master)
    return master


@pytest.fixture
def test_compliance_instance(
    db_session: Session,
    test_tenant: Tenant,
    test_entity: Entity,
    test_compliance_master: ComplianceMaster,
    admin_user_fixture: User,
):
    """Create a test compliance instance"""
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
    db_session.refresh(instance)
    return instance


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


class TestCreateWorkflowTask:
    """Tests for POST /api/v1/workflow-tasks"""

    def test_create_task_success(
        self,
        client: TestClient,
        admin_headers: dict,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test creating a workflow task successfully"""
        response = client.post(
            "/api/v1/workflow-tasks/",
            json={
                "compliance_instance_id": str(test_compliance_instance.id),
                "task_type": "Prepare",
                "task_name": "Prepare data",
                "task_description": "Collect all required data",
                "assigned_to_user_id": str(admin_user_fixture.id),
                "sequence_order": 1,
                "due_date": str(date.today() + timedelta(days=10)),
            },
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["task_type"] == "Prepare"
        assert data["task_name"] == "Prepare data"
        assert data["status"] == "Pending"
        assert "id" in data

    def test_create_task_with_role_assignment(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_compliance_instance: ComplianceInstance,
    ):
        """Test creating task assigned to role"""
        # Get admin role
        admin_role = db_session.query(Role).filter(Role.role_code == "admin").first()

        response = client.post(
            "/api/v1/workflow-tasks/",
            json={
                "compliance_instance_id": str(test_compliance_instance.id),
                "task_type": "Review",
                "task_name": "Review submission",
                "assigned_to_role_id": str(admin_role.id),
                "sequence_order": 2,
            },
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["assigned_to_role_id"] == str(admin_role.id)

    def test_create_task_invalid_instance(self, client: TestClient, admin_headers: dict):
        """Test creating task with invalid compliance instance ID"""
        fake_instance_id = "123e4567-e89b-12d3-a456-426614174999"

        response = client.post(
            "/api/v1/workflow-tasks/",
            json={
                "compliance_instance_id": fake_instance_id,
                "task_type": "Prepare",
                "task_name": "Test task",
                "sequence_order": 1,
            },
            headers=admin_headers,
        )

        assert response.status_code == 404
        assert "compliance instance not found" in response.json()["detail"].lower()

    def test_create_task_invalid_assigned_user(
        self, client: TestClient, admin_headers: dict, test_compliance_instance: ComplianceInstance
    ):
        """Test creating task with invalid assigned user ID"""
        fake_user_id = "123e4567-e89b-12d3-a456-426614174999"

        response = client.post(
            "/api/v1/workflow-tasks/",
            json={
                "compliance_instance_id": str(test_compliance_instance.id),
                "task_type": "Prepare",
                "task_name": "Test task",
                "assigned_to_user_id": fake_user_id,
                "sequence_order": 1,
            },
            headers=admin_headers,
        )

        assert response.status_code == 404
        assert "assigned user not found" in response.json()["detail"].lower()

    def test_create_task_no_entity_access(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test creating task for instance without entity access"""
        # Create entity without granting access to regular user
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="NO-ACCESS-WT",
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

        response = client.post(
            "/api/v1/workflow-tasks/",
            json={
                "compliance_instance_id": str(instance.id),
                "task_type": "Prepare",
                "task_name": "Test task",
                "sequence_order": 1,
            },
            headers=regular_headers,
        )

        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()

    def test_create_task_no_auth(self, client: TestClient, test_compliance_instance: ComplianceInstance):
        """Test creating task without authentication"""
        response = client.post(
            "/api/v1/workflow-tasks/",
            json={
                "compliance_instance_id": str(test_compliance_instance.id),
                "task_type": "Prepare",
                "task_name": "Test task",
                "sequence_order": 1,
            },
        )

        assert response.status_code in [401, 403]


class TestListWorkflowTasks:
    """Tests for GET /api/v1/workflow-tasks"""

    def test_list_tasks_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test listing workflow tasks"""
        # Create test task
        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Prepare",
            task_name="Test Task",
            status="Pending",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()

        response = client.get("/api/v1/workflow-tasks/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_list_tasks_with_pagination(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test workflow task list pagination"""
        # Create multiple tasks
        for i in range(5):
            task = WorkflowTask(
                tenant_id=test_tenant.id,
                compliance_instance_id=test_compliance_instance.id,
                task_type="Prepare",
                task_name=f"Task {i}",
                status="Pending",
                sequence_order=i + 1,
                created_by=admin_user_fixture.id,
                updated_by=admin_user_fixture.id,
            )
            db_session.add(task)
        db_session.commit()

        response = client.get("/api/v1/workflow-tasks/?skip=0&limit=3", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 3
        assert len(data["items"]) <= 3

    def test_list_tasks_filter_by_instance(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test filtering tasks by compliance instance"""
        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Prepare",
            task_name="Test Task",
            status="Pending",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()

        response = client.get(
            f"/api/v1/workflow-tasks/?compliance_instance_id={test_compliance_instance.id}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert all(item["compliance_instance_id"] == str(test_compliance_instance.id) for item in data["items"])

    def test_list_tasks_filter_by_status(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test filtering tasks by status"""
        # Create tasks with different statuses
        pending_task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Prepare",
            task_name="Pending Task",
            status="Pending",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        completed_task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Review",
            task_name="Completed Task",
            status="Completed",
            sequence_order=2,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add_all([pending_task, completed_task])
        db_session.commit()

        response = client.get("/api/v1/workflow-tasks/?status=Pending", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert all(item["status"] == "Pending" for item in data["items"])

    def test_list_tasks_filter_by_assigned_user(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test filtering tasks by assigned user"""
        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Prepare",
            task_name="Assigned Task",
            status="Pending",
            sequence_order=1,
            assigned_to_user_id=admin_user_fixture.id,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()

        response = client.get(
            f"/api/v1/workflow-tasks/?assigned_to_user_id={admin_user_fixture.id}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert all(item["assigned_to_user_id"] == str(admin_user_fixture.id) for item in data["items"])

    def test_list_tasks_filter_by_task_type(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test filtering tasks by task type"""
        prepare_task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Prepare",
            task_name="Prepare Task",
            status="Pending",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        review_task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Review",
            task_name="Review Task",
            status="Pending",
            sequence_order=2,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add_all([prepare_task, review_task])
        db_session.commit()

        response = client.get("/api/v1/workflow-tasks/?task_type=Prepare", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert all(item["task_type"] == "Prepare" for item in data["items"])

    def test_list_tasks_entity_access_filtering(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        regular_user_fixture: User,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test that regular users only see tasks for entities they have access to"""
        # Create entity with access
        accessible_entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="ACCESSIBLE-WT",
            entity_name="Accessible Entity",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(accessible_entity)
        db_session.flush()

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
            entity_code="NO-ACCESS-WT",
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
        db_session.flush()

        # Create tasks for both
        accessible_task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=accessible_instance.id,
            task_type="Prepare",
            task_name="Accessible Task",
            status="Pending",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        no_access_task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=no_access_instance.id,
            task_type="Prepare",
            task_name="No Access Task",
            status="Pending",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add_all([accessible_task, no_access_task])
        db_session.commit()

        # Regular user should only see accessible task
        response = client.get("/api/v1/workflow-tasks/", headers=regular_headers)

        assert response.status_code == 200
        data = response.json()
        task_names = [item["task_name"] for item in data["items"]]
        assert "Accessible Task" in task_names
        assert "No Access Task" not in task_names


class TestGetWorkflowTask:
    """Tests for GET /api/v1/workflow-tasks/{task_id}"""

    def test_get_task_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test getting a workflow task by ID"""
        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Prepare",
            task_name="Test Task",
            status="Pending",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()

        response = client.get(f"/api/v1/workflow-tasks/{task.id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(task.id)
        assert data["task_name"] == "Test Task"

    def test_get_task_with_access(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        regular_user_fixture: User,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test getting task for instance with access"""
        # Create entity and grant access
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="ACCESSIBLE-WT",
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

        # Create instance and task
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
        db_session.flush()

        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=instance.id,
            task_type="Prepare",
            task_name="Accessible Task",
            status="Pending",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()

        response = client.get(f"/api/v1/workflow-tasks/{task.id}", headers=regular_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(task.id)

    def test_get_task_without_access(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test getting task for instance without access"""
        # Create entity without access
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="NO-ACCESS-WT",
            entity_name="No Access Entity",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(entity)
        db_session.flush()

        # Create instance and task
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
        db_session.flush()

        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=instance.id,
            task_type="Prepare",
            task_name="No Access Task",
            status="Pending",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()

        response = client.get(f"/api/v1/workflow-tasks/{task.id}", headers=regular_headers)

        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()

    def test_get_task_not_found(self, client: TestClient, admin_headers: dict):
        """Test getting non-existent task"""
        fake_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.get(f"/api/v1/workflow-tasks/{fake_id}", headers=admin_headers)

        assert response.status_code == 404


class TestUpdateWorkflowTask:
    """Tests for PUT /api/v1/workflow-tasks/{task_id}"""

    def test_update_task_assignment(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test updating task assignment"""
        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Prepare",
            task_name="Test Task",
            status="Pending",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()

        response = client.put(
            f"/api/v1/workflow-tasks/{task.id}",
            json={"assigned_to_user_id": str(admin_user_fixture.id)},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["assigned_to_user_id"] == str(admin_user_fixture.id)

    def test_update_task_partial(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test partial update of task"""
        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Prepare",
            task_name="Original Name",
            status="Pending",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()

        original_status = task.status

        response = client.put(
            f"/api/v1/workflow-tasks/{task.id}",
            json={"task_name": "Updated Name"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task_name"] == "Updated Name"
        assert data["status"] == original_status

    def test_update_task_without_access(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test updating task without entity access"""
        # Create entity without access
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="NO-ACCESS-WT",
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
        db_session.flush()

        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=instance.id,
            task_type="Prepare",
            task_name="Test Task",
            status="Pending",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()

        response = client.put(
            f"/api/v1/workflow-tasks/{task.id}",
            json={"task_name": "Hacked"},
            headers=regular_headers,
        )

        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()

    def test_update_task_not_found(self, client: TestClient, admin_headers: dict):
        """Test updating non-existent task"""
        fake_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.put(
            f"/api/v1/workflow-tasks/{fake_id}",
            json={"task_name": "Updated"},
            headers=admin_headers,
        )

        assert response.status_code == 404


class TestDeleteWorkflowTask:
    """Tests for DELETE /api/v1/workflow-tasks/{task_id}"""

    def test_delete_task_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test deleting a pending task"""
        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Prepare",
            task_name="Task to Delete",
            status="Pending",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()
        task_id = task.id

        response = client.delete(f"/api/v1/workflow-tasks/{task_id}", headers=admin_headers)

        assert response.status_code == 204

        # Verify task is deleted
        deleted_task = db_session.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
        assert deleted_task is None

    def test_delete_task_in_progress_fails(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test that you cannot delete a task in progress"""
        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Prepare",
            task_name="In Progress Task",
            status="In Progress",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()

        response = client.delete(f"/api/v1/workflow-tasks/{task.id}", headers=admin_headers)

        assert response.status_code == 400
        assert "can only delete tasks in pending status" in response.json()["detail"].lower()

    def test_delete_task_without_access(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test deleting task without entity access"""
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="NO-ACCESS-WT",
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
        db_session.flush()

        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=instance.id,
            task_type="Prepare",
            task_name="Test Task",
            status="Pending",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()

        response = client.delete(f"/api/v1/workflow-tasks/{task.id}", headers=regular_headers)

        assert response.status_code == 403

    def test_delete_task_not_found(self, client: TestClient, admin_headers: dict):
        """Test deleting non-existent task"""
        fake_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.delete(f"/api/v1/workflow-tasks/{fake_id}", headers=admin_headers)

        assert response.status_code == 404


class TestStartTask:
    """Tests for POST /api/v1/workflow-tasks/{task_id}/start"""

    def test_start_task_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test starting a pending task"""
        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Prepare",
            task_name="Test Task",
            status="Pending",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()

        response = client.post(
            f"/api/v1/workflow-tasks/{task.id}/start",
            json={"remarks": "Starting task"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "In Progress"
        assert data["started_at"] is not None

    def test_start_task_already_started(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test starting a task that's already in progress"""
        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Prepare",
            task_name="Test Task",
            status="In Progress",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()

        response = client.post(
            f"/api/v1/workflow-tasks/{task.id}/start",
            json={},
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "can only start tasks in pending status" in response.json()["detail"].lower()

    def test_start_task_with_incomplete_parent(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test starting task when parent is not completed"""
        parent_task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Prepare",
            task_name="Parent Task",
            status="In Progress",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(parent_task)
        db_session.flush()

        child_task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Review",
            task_name="Child Task",
            status="Pending",
            sequence_order=2,
            parent_task_id=parent_task.id,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(child_task)
        db_session.commit()

        response = client.post(
            f"/api/v1/workflow-tasks/{child_task.id}/start",
            json={},
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "parent task must be completed first" in response.json()["detail"].lower()


class TestCompleteTask:
    """Tests for POST /api/v1/workflow-tasks/{task_id}/complete"""

    def test_complete_task_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test completing a task"""
        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Prepare",
            task_name="Test Task",
            status="In Progress",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()

        response = client.post(
            f"/api/v1/workflow-tasks/{task.id}/complete",
            json={"remarks": "Task completed successfully"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Completed"
        assert data["completed_at"] is not None
        assert data["completion_remarks"] == "Task completed successfully"

    def test_complete_task_already_completed(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test completing a task that's already completed"""
        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Prepare",
            task_name="Test Task",
            status="Completed",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()

        response = client.post(
            f"/api/v1/workflow-tasks/{task.id}/complete",
            json={},
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "already completed" in response.json()["detail"].lower()


class TestRejectTask:
    """Tests for POST /api/v1/workflow-tasks/{task_id}/reject"""

    def test_reject_task_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test rejecting a task"""
        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Review",
            task_name="Test Task",
            status="In Progress",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()

        response = client.post(
            f"/api/v1/workflow-tasks/{task.id}/reject",
            json={"rejection_reason": "Incomplete data"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Rejected"
        assert data["rejection_reason"] == "Incomplete data"

    def test_reject_task_already_completed(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test rejecting a task that's already completed"""
        task = WorkflowTask(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            task_type="Review",
            task_name="Test Task",
            status="Completed",
            sequence_order=1,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(task)
        db_session.commit()

        response = client.post(
            f"/api/v1/workflow-tasks/{task.id}/reject",
            json={"rejection_reason": "Should not work"},
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "already completed" in response.json()["detail"].lower()
