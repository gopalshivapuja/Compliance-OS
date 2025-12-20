"""
Integration tests for Evidence API endpoints
"""

import pytest
import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta

from app.models import Tenant, User, Role, Entity, ComplianceMaster, ComplianceInstance, Evidence
from app.models.role import user_roles
from app.models.entity import entity_access
from app.core.security import create_access_token


@pytest.fixture
def test_tenant(db_session: Session):
    """Create a test tenant"""
    tenant = Tenant(
        tenant_code="TEST_EV",
        tenant_name="Test Evidence Tenant",
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
        email="admin@evidence.com",
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
        email="user@evidence.com",
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
        entity_code="TEST-EV-001",
        entity_name="Test Evidence Entity",
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
        compliance_code="EV_TEST",
        compliance_name="Evidence Test Compliance",
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


class TestUploadEvidence:
    """Tests for POST /api/v1/evidence/upload"""

    def test_upload_evidence_success(
        self,
        client: TestClient,
        admin_headers: dict,
        test_compliance_instance: ComplianceInstance,
    ):
        """Test uploading evidence file successfully"""
        # Create a test file
        file_content = b"Test PDF content"
        files = {"file": ("test_document.pdf", io.BytesIO(file_content), "application/pdf")}
        data = {
            "compliance_instance_id": str(test_compliance_instance.id),
            "evidence_name": "Test Evidence",
            "description": "Test description",
        }

        response = client.post(
            "/api/v1/evidence/upload",
            files=files,
            data=data,
            headers=admin_headers,
        )

        assert response.status_code == 201
        response_data = response.json()
        assert response_data["evidence_name"] == "Test Evidence"
        assert response_data["approval_status"] == "Pending"
        assert response_data["is_immutable"] is False
        assert response_data["file_size"] == len(file_content)
        assert "id" in response_data

    def test_upload_evidence_with_default_name(
        self,
        client: TestClient,
        admin_headers: dict,
        test_compliance_instance: ComplianceInstance,
    ):
        """Test uploading evidence without custom name uses filename"""
        file_content = b"Test content"
        files = {"file": ("original_file.pdf", io.BytesIO(file_content), "application/pdf")}
        data = {
            "compliance_instance_id": str(test_compliance_instance.id),
        }

        response = client.post(
            "/api/v1/evidence/upload",
            files=files,
            data=data,
            headers=admin_headers,
        )

        assert response.status_code == 201
        response_data = response.json()
        assert response_data["evidence_name"] == "original_file.pdf"

    def test_upload_evidence_invalid_instance(
        self,
        client: TestClient,
        admin_headers: dict,
    ):
        """Test uploading evidence with invalid compliance instance ID"""
        fake_instance_id = "123e4567-e89b-12d3-a456-426614174999"
        file_content = b"Test content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        data = {
            "compliance_instance_id": fake_instance_id,
        }

        response = client.post(
            "/api/v1/evidence/upload",
            files=files,
            data=data,
            headers=admin_headers,
        )

        assert response.status_code == 404
        assert "compliance instance not found" in response.json()["detail"].lower()

    def test_upload_evidence_invalid_file_type(
        self,
        client: TestClient,
        admin_headers: dict,
        test_compliance_instance: ComplianceInstance,
    ):
        """Test uploading evidence with invalid file type"""
        file_content = b"#!/bin/bash\necho 'test'"
        files = {"file": ("malicious.sh", io.BytesIO(file_content), "application/x-sh")}
        data = {
            "compliance_instance_id": str(test_compliance_instance.id),
        }

        response = client.post(
            "/api/v1/evidence/upload",
            files=files,
            data=data,
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "invalid file type" in response.json()["detail"].lower()

    def test_upload_evidence_file_too_large(
        self,
        client: TestClient,
        admin_headers: dict,
        test_compliance_instance: ComplianceInstance,
    ):
        """Test uploading evidence with file size exceeding limit"""
        # Create a file larger than 50MB
        file_content = b"x" * (51 * 1024 * 1024)  # 51MB
        files = {"file": ("large_file.pdf", io.BytesIO(file_content), "application/pdf")}
        data = {
            "compliance_instance_id": str(test_compliance_instance.id),
        }

        response = client.post(
            "/api/v1/evidence/upload",
            files=files,
            data=data,
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "file size exceeds" in response.json()["detail"].lower()

    def test_upload_evidence_no_entity_access(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test uploading evidence for instance without entity access"""
        # Create entity without granting access to regular user
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="NO-ACCESS-EV",
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

        file_content = b"Test content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        data = {
            "compliance_instance_id": str(instance.id),
        }

        response = client.post(
            "/api/v1/evidence/upload",
            files=files,
            data=data,
            headers=regular_headers,
        )

        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()

    def test_upload_evidence_no_auth(
        self,
        client: TestClient,
        test_compliance_instance: ComplianceInstance,
    ):
        """Test uploading evidence without authentication"""
        file_content = b"Test content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        data = {
            "compliance_instance_id": str(test_compliance_instance.id),
        }

        response = client.post(
            "/api/v1/evidence/upload",
            files=files,
            data=data,
        )

        assert response.status_code in [401, 403]


class TestListEvidence:
    """Tests for GET /api/v1/evidence"""

    def test_list_evidence_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test listing evidence"""
        # Create test evidence
        evidence = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            evidence_name="Test Evidence",
            file_path="test/path.pdf",
            file_hash="abc123",
            version=1,
            approval_status="Pending",
            is_immutable=False,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(evidence)
        db_session.commit()

        response = client.get("/api/v1/evidence/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_list_evidence_with_pagination(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test evidence list pagination"""
        # Create multiple evidence items
        for i in range(5):
            evidence = Evidence(
                tenant_id=test_tenant.id,
                compliance_instance_id=test_compliance_instance.id,
                evidence_name=f"Evidence {i}",
                file_path=f"test/path{i}.pdf",
                file_hash=f"hash{i}",
                version=1,
                approval_status="Pending",
                is_immutable=False,
                created_by=admin_user_fixture.id,
                updated_by=admin_user_fixture.id,
            )
            db_session.add(evidence)
        db_session.commit()

        response = client.get("/api/v1/evidence/?skip=0&limit=3", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 3
        assert len(data["items"]) <= 3

    def test_list_evidence_filter_by_instance(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test filtering evidence by compliance instance"""
        evidence = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            evidence_name="Test Evidence",
            file_path="test/path.pdf",
            file_hash="abc123",
            version=1,
            approval_status="Pending",
            is_immutable=False,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(evidence)
        db_session.commit()

        response = client.get(
            f"/api/v1/evidence/?compliance_instance_id={test_compliance_instance.id}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert all(
            item["compliance_instance_id"] == str(test_compliance_instance.id)
            for item in data["items"]
        )

    def test_list_evidence_filter_by_approval_status(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test filtering evidence by approval status"""
        # Create evidence with different statuses
        pending = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            evidence_name="Pending Evidence",
            file_path="test/pending.pdf",
            file_hash="pending123",
            version=1,
            approval_status="Pending",
            is_immutable=False,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        approved = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            evidence_name="Approved Evidence",
            file_path="test/approved.pdf",
            file_hash="approved123",
            version=1,
            approval_status="Approved",
            is_immutable=True,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add_all([pending, approved])
        db_session.commit()

        response = client.get("/api/v1/evidence/?approval_status=Approved", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert all(item["approval_status"] == "Approved" for item in data["items"])

    def test_list_evidence_entity_access_filtering(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        regular_user_fixture: User,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test that regular users only see evidence for entities they have access to"""
        # Create entity with access
        accessible_entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="ACCESSIBLE-EV",
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
            entity_code="NO-ACCESS-EV",
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

        # Create evidence for both
        accessible_evidence = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=accessible_instance.id,
            evidence_name="Accessible Evidence",
            file_path="test/accessible.pdf",
            file_hash="accessible123",
            version=1,
            approval_status="Pending",
            is_immutable=False,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        no_access_evidence = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=no_access_instance.id,
            evidence_name="No Access Evidence",
            file_path="test/no_access.pdf",
            file_hash="noaccess123",
            version=1,
            approval_status="Pending",
            is_immutable=False,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add_all([accessible_evidence, no_access_evidence])
        db_session.commit()

        # Regular user should only see accessible evidence
        response = client.get("/api/v1/evidence/", headers=regular_headers)

        assert response.status_code == 200
        data = response.json()
        evidence_names = [item["evidence_name"] for item in data["items"]]
        assert "Accessible Evidence" in evidence_names
        assert "No Access Evidence" not in evidence_names


class TestGetEvidence:
    """Tests for GET /api/v1/evidence/{evidence_id}"""

    def test_get_evidence_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test getting evidence by ID"""
        evidence = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            evidence_name="Test Evidence",
            file_path="test/path.pdf",
            file_hash="abc123",
            version=1,
            approval_status="Pending",
            is_immutable=False,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(evidence)
        db_session.commit()

        response = client.get(f"/api/v1/evidence/{evidence.id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(evidence.id)
        assert data["evidence_name"] == "Test Evidence"

    def test_get_evidence_with_access(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        regular_user_fixture: User,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test getting evidence for instance with access"""
        # Create entity and grant access
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="ACCESSIBLE-EV",
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

        # Create instance and evidence
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

        evidence = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=instance.id,
            evidence_name="Accessible Evidence",
            file_path="test/path.pdf",
            file_hash="abc123",
            version=1,
            approval_status="Pending",
            is_immutable=False,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(evidence)
        db_session.commit()

        response = client.get(f"/api/v1/evidence/{evidence.id}", headers=regular_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(evidence.id)

    def test_get_evidence_without_access(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test getting evidence for instance without access"""
        # Create entity without access
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="NO-ACCESS-EV",
            entity_name="No Access Entity",
            status="active",
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(entity)
        db_session.flush()

        # Create instance and evidence
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

        evidence = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=instance.id,
            evidence_name="No Access Evidence",
            file_path="test/path.pdf",
            file_hash="abc123",
            version=1,
            approval_status="Pending",
            is_immutable=False,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(evidence)
        db_session.commit()

        response = client.get(f"/api/v1/evidence/{evidence.id}", headers=regular_headers)

        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()

    def test_get_evidence_not_found(self, client: TestClient, admin_headers: dict):
        """Test getting non-existent evidence"""
        fake_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.get(f"/api/v1/evidence/{fake_id}", headers=admin_headers)

        assert response.status_code == 404


class TestDownloadEvidence:
    """Tests for GET /api/v1/evidence/{evidence_id}/download"""

    def test_download_evidence_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test downloading evidence"""
        evidence = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            evidence_name="Test Evidence",
            file_path="test/path.pdf",
            file_hash="abc123",
            version=1,
            approval_status="Pending",
            is_immutable=False,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(evidence)
        db_session.commit()

        response = client.get(f"/api/v1/evidence/{evidence.id}/download", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["evidence_id"] == str(evidence.id)
        assert data["evidence_name"] == "Test Evidence"
        assert "download_url" in data
        assert data["expires_in_seconds"] == 300

    def test_download_evidence_without_access(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test downloading evidence without entity access"""
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="NO-ACCESS-EV",
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

        evidence = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=instance.id,
            evidence_name="No Access Evidence",
            file_path="test/path.pdf",
            file_hash="abc123",
            version=1,
            approval_status="Pending",
            is_immutable=False,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(evidence)
        db_session.commit()

        response = client.get(f"/api/v1/evidence/{evidence.id}/download", headers=regular_headers)

        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()


class TestApproveEvidence:
    """Tests for POST /api/v1/evidence/{evidence_id}/approve"""

    def test_approve_evidence_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test approving evidence"""
        evidence = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            evidence_name="Test Evidence",
            file_path="test/path.pdf",
            file_hash="abc123",
            version=1,
            approval_status="Pending",
            is_immutable=False,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(evidence)
        db_session.commit()

        response = client.post(
            f"/api/v1/evidence/{evidence.id}/approve",
            json={"remarks": "Approved for filing"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "Approved"
        assert data["is_immutable"] is True
        assert data["approved_by_user_id"] == str(admin_user_fixture.id)
        assert data["approval_remarks"] == "Approved for filing"
        assert data["approved_at"] is not None

    def test_approve_evidence_already_approved(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test approving already approved evidence"""
        evidence = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            evidence_name="Test Evidence",
            file_path="test/path.pdf",
            file_hash="abc123",
            version=1,
            approval_status="Approved",
            is_immutable=True,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(evidence)
        db_session.commit()

        response = client.post(
            f"/api/v1/evidence/{evidence.id}/approve",
            json={},
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "cannot approve" in response.json()["detail"].lower()

    def test_approve_evidence_without_access(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test approving evidence without entity access"""
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="NO-ACCESS-EV",
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

        evidence = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=instance.id,
            evidence_name="No Access Evidence",
            file_path="test/path.pdf",
            file_hash="abc123",
            version=1,
            approval_status="Pending",
            is_immutable=False,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(evidence)
        db_session.commit()

        response = client.post(
            f"/api/v1/evidence/{evidence.id}/approve",
            json={},
            headers=regular_headers,
        )

        assert response.status_code == 403


class TestRejectEvidence:
    """Tests for POST /api/v1/evidence/{evidence_id}/reject"""

    def test_reject_evidence_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test rejecting evidence"""
        evidence = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            evidence_name="Test Evidence",
            file_path="test/path.pdf",
            file_hash="abc123",
            version=1,
            approval_status="Pending",
            is_immutable=False,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(evidence)
        db_session.commit()

        response = client.post(
            f"/api/v1/evidence/{evidence.id}/reject",
            json={"rejection_reason": "Incomplete documentation"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "Rejected"
        assert data["rejection_reason"] == "Incomplete documentation"

    def test_reject_evidence_already_approved(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test rejecting already approved evidence"""
        evidence = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            evidence_name="Test Evidence",
            file_path="test/path.pdf",
            file_hash="abc123",
            version=1,
            approval_status="Approved",
            is_immutable=True,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(evidence)
        db_session.commit()

        response = client.post(
            f"/api/v1/evidence/{evidence.id}/reject",
            json={"rejection_reason": "Should not work"},
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "cannot reject" in response.json()["detail"].lower()


class TestDeleteEvidence:
    """Tests for DELETE /api/v1/evidence/{evidence_id}"""

    def test_delete_evidence_success(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test deleting pending evidence"""
        evidence = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            evidence_name="Evidence to Delete",
            file_path="test/to_delete.pdf",
            file_hash="delete123",
            version=1,
            approval_status="Pending",
            is_immutable=False,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(evidence)
        db_session.commit()
        evidence_id = evidence.id

        response = client.delete(f"/api/v1/evidence/{evidence_id}", headers=admin_headers)

        assert response.status_code == 204

        # Verify evidence is deleted
        deleted_evidence = db_session.query(Evidence).filter(Evidence.id == evidence_id).first()
        assert deleted_evidence is None

    def test_delete_evidence_immutable_fails(
        self,
        client: TestClient,
        admin_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_instance: ComplianceInstance,
        admin_user_fixture: User,
    ):
        """Test that you cannot delete immutable (approved) evidence"""
        evidence = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=test_compliance_instance.id,
            evidence_name="Immutable Evidence",
            file_path="test/immutable.pdf",
            file_hash="immutable123",
            version=1,
            approval_status="Approved",
            is_immutable=True,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(evidence)
        db_session.commit()

        response = client.delete(f"/api/v1/evidence/{evidence.id}", headers=admin_headers)

        assert response.status_code == 400
        assert "cannot delete approved evidence" in response.json()["detail"].lower()

    def test_delete_evidence_without_access(
        self,
        client: TestClient,
        regular_headers: dict,
        db_session: Session,
        test_tenant: Tenant,
        test_compliance_master: ComplianceMaster,
        admin_user_fixture: User,
    ):
        """Test deleting evidence without entity access"""
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="NO-ACCESS-EV",
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

        evidence = Evidence(
            tenant_id=test_tenant.id,
            compliance_instance_id=instance.id,
            evidence_name="No Access Evidence",
            file_path="test/path.pdf",
            file_hash="abc123",
            version=1,
            approval_status="Pending",
            is_immutable=False,
            created_by=admin_user_fixture.id,
            updated_by=admin_user_fixture.id,
        )
        db_session.add(evidence)
        db_session.commit()

        response = client.delete(f"/api/v1/evidence/{evidence.id}", headers=regular_headers)

        assert response.status_code == 403

    def test_delete_evidence_not_found(self, client: TestClient, admin_headers: dict):
        """Test deleting non-existent evidence"""
        fake_id = "123e4567-e89b-12d3-a456-426614174999"
        response = client.delete(f"/api/v1/evidence/{fake_id}", headers=admin_headers)

        assert response.status_code == 404
