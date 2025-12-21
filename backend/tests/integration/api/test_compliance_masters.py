"""
Integration tests for Compliance Masters API endpoints
"""

import pytest
from datetime import datetime, timedelta
import uuid
from fastapi import status

from app.models import Tenant, User, ComplianceMaster, ComplianceInstance, Entity, Role
from app.models.role import user_roles
from app.core.security import create_access_token


@pytest.fixture
def test_tenant(db_session):
    """Create test tenant"""
    tenant = Tenant(
        tenant_code="TEST_CM_TENANT",
        tenant_name="Test Tenant for Compliance Masters",
        status="active",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def admin_user_fixture(db_session, test_tenant):
    """Create admin user"""
    # Check if admin role exists
    admin_role = db_session.query(Role).filter(Role.role_code == "admin").first()
    if not admin_role:
        admin_role = Role(
            role_code="admin",
            role_name="Administrator",
        )
        db_session.add(admin_role)
        db_session.flush()

    user = User(
        email=f"admin-cm-{uuid.uuid4()}@test.com",
        first_name="Admin",
        last_name="User",
        tenant_id=test_tenant.id,
        status="active",
        is_system_admin=False,
    )
    user.set_password("AdminPass123!")
    db_session.add(user)
    db_session.flush()

    # Assign role
    db_session.execute(
        user_roles.insert().values(
            user_id=user.id,
            role_id=admin_role.id,
            tenant_id=test_tenant.id,
        )
    )
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def system_admin_user(db_session, test_tenant):
    """Create system admin user"""
    user = User(
        email=f"sysadmin-cm-{uuid.uuid4()}@test.com",
        first_name="System",
        last_name="Admin",
        tenant_id=test_tenant.id,
        status="active",
        is_system_admin=True,
    )
    user.set_password("SysAdminPass123!")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user_fixture(db_session, test_tenant):
    """Create regular user"""
    user = User(
        email=f"user-cm-{uuid.uuid4()}@test.com",
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
def test_compliance_master(db_session, test_tenant, admin_user_fixture):
    """Create test compliance master"""
    master = ComplianceMaster(
        tenant_id=test_tenant.id,
        compliance_code="GSTR-1",
        compliance_name="GSTR-1 Monthly Return",
        description="Monthly return for outward supplies",
        category="GST",
        sub_category="Returns",
        frequency="Monthly",
        due_date_rule={"type": "monthly", "day": 11, "offset_days": 0},
        owner_role_code="tax_lead",
        approver_role_code="tax_manager",
        is_active=True,
        is_template=False,
        authority="CBIC",
    )
    db_session.add(master)
    db_session.commit()
    db_session.refresh(master)
    return master


@pytest.fixture
def system_template_master(db_session, system_admin_user):
    """Create system-wide template compliance master"""
    master = ComplianceMaster(
        tenant_id=None,  # System-wide template
        compliance_code="TDS-24Q",
        compliance_name="TDS Return (24Q) - Quarterly",
        description="Quarterly TDS return for salary payments",
        category="Direct Tax",
        sub_category="TDS",
        frequency="Quarterly",
        due_date_rule={"type": "quarterly", "offset_days": 31},
        owner_role_code="finance_lead",
        approver_role_code="cfo",
        is_active=True,
        is_template=True,
        authority="Income Tax Department",
    )
    db_session.add(master)
    db_session.commit()
    db_session.refresh(master)
    return master


@pytest.fixture
def admin_headers(admin_user_fixture, test_tenant):
    """Create headers with admin JWT token"""
    token = create_access_token(
        data={
            "user_id": str(admin_user_fixture.id),
            "tenant_id": str(test_tenant.id),
            "email": admin_user_fixture.email,
            "roles": ["TENANT_ADMIN"],
            "is_system_admin": False,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def system_admin_headers(system_admin_user, test_tenant):
    """Create headers with system admin JWT token"""
    token = create_access_token(
        data={
            "user_id": str(system_admin_user.id),
            "tenant_id": str(test_tenant.id),
            "email": system_admin_user.email,
            "roles": ["SYSTEM_ADMIN"],
            "is_system_admin": True,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def regular_headers(regular_user_fixture, test_tenant):
    """Create headers with regular user JWT token"""
    token = create_access_token(
        data={
            "user_id": str(regular_user_fixture.id),
            "tenant_id": str(test_tenant.id),
            "email": regular_user_fixture.email,
            "roles": [],
            "is_system_admin": False,
        }
    )
    return {"Authorization": f"Bearer {token}"}


class TestCreateComplianceMaster:
    """Tests for creating compliance masters"""

    def test_create_compliance_master_success(self, client, db_session, admin_headers):
        """Test successful compliance master creation"""
        payload = {
            "compliance_code": "GSTR-3B",
            "compliance_name": "GSTR-3B Monthly Return",
            "description": "Monthly summary return",
            "category": "GST",
            "sub_category": "Returns",
            "frequency": "Monthly",
            "due_date_rule": {"type": "monthly", "day": 20, "offset_days": 0},
            "owner_role_code": "tax_lead",
            "approver_role_code": "tax_manager",
            "authority": "CBIC",
            "is_template": False,
        }

        response = client.post("/api/v1/compliance-masters/", json=payload, headers=admin_headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["compliance_code"] == "GSTR-3B"
        assert data["compliance_name"] == "GSTR-3B Monthly Return"
        assert data["category"] == "GST"
        assert data["frequency"] == "Monthly"
        assert data["is_active"] is True
        assert data["is_template"] is False
        assert data["instances_count"] == 0

    def test_create_duplicate_compliance_code(self, client, db_session, admin_headers, test_compliance_master):
        """Test creating compliance master with duplicate code fails"""
        payload = {
            "compliance_code": "GSTR-1",  # Same as test_compliance_master
            "compliance_name": "Duplicate Master",
            "category": "GST",
            "frequency": "Monthly",
            "due_date_rule": {"type": "monthly", "day": 11, "offset_days": 0},
            "is_template": False,
        }

        response = client.post("/api/v1/compliance-masters/", json=payload, headers=admin_headers)

        # Either 400 (bad request) or 409 (conflict) for duplicates
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT]
        assert "already exists" in response.json()["detail"].lower() or "duplicate" in response.json()["detail"].lower()

    def test_create_with_invalid_category(self, client, db_session, admin_headers):
        """Test creating compliance master with invalid category"""
        payload = {
            "compliance_code": "INVALID-1",
            "compliance_name": "Invalid Category Test",
            "category": "InvalidCategory",  # Not in allowed list
            "frequency": "Monthly",
            "due_date_rule": {"type": "monthly", "day": 11, "offset_days": 0},
            "is_template": False,
        }

        response = client.post("/api/v1/compliance-masters/", json=payload, headers=admin_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_with_invalid_frequency(self, client, db_session, admin_headers):
        """Test creating compliance master with invalid frequency"""
        payload = {
            "compliance_code": "INVALID-2",
            "compliance_name": "Invalid Frequency Test",
            "category": "GST",
            "frequency": "InvalidFrequency",  # Not in allowed list
            "due_date_rule": {"type": "monthly", "day": 11, "offset_days": 0},
            "is_template": False,
        }

        response = client.post("/api/v1/compliance-masters/", json=payload, headers=admin_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_system_template_requires_system_admin(self, client, db_session, admin_headers):
        """Test that creating system templates requires system admin"""
        payload = {
            "compliance_code": "TEMPLATE-1",
            "compliance_name": "System Template",
            "category": "GST",
            "frequency": "Monthly",
            "due_date_rule": {"type": "monthly", "day": 11, "offset_days": 0},
            "is_template": True,  # Trying to create template
        }

        response = client.post("/api/v1/compliance-masters/", json=payload, headers=admin_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "system administrators" in response.json()["detail"].lower()

    def test_create_system_template_as_system_admin(self, client, db_session, system_admin_headers):
        """Test system admin can create system templates"""
        payload = {
            "compliance_code": "TEMPLATE-2",
            "compliance_name": "System Template by SysAdmin",
            "category": "Direct Tax",
            "frequency": "Quarterly",
            "due_date_rule": {"type": "quarterly", "offset_days": 30},
            "is_template": True,
        }

        response = client.post("/api/v1/compliance-masters/", json=payload, headers=system_admin_headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["is_template"] is True
        assert data["tenant_id"] is None  # System template has NULL tenant_id

    def test_create_unauthorized_regular_user(self, client, db_session, regular_headers):
        """Test regular user cannot create compliance masters"""
        payload = {
            "compliance_code": "TEST-1",
            "compliance_name": "Test Master",
            "category": "GST",
            "frequency": "Monthly",
            "due_date_rule": {"type": "monthly", "day": 11, "offset_days": 0},
            "is_template": False,
        }

        response = client.post("/api/v1/compliance-masters/", json=payload, headers=regular_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestListComplianceMasters:
    """Tests for listing compliance masters"""

    def test_list_compliance_masters_includes_templates(
        self,
        client,
        db_session,
        admin_headers,
        test_compliance_master,
        system_template_master,
    ):
        """Test that listing shows both tenant masters and system templates"""
        response = client.get("/api/v1/compliance-masters/", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 2

        codes = [item["compliance_code"] for item in data["items"]]
        assert "GSTR-1" in codes  # Tenant-specific
        assert "TDS-24Q" in codes  # System template

    def test_list_with_category_filter(self, client, db_session, admin_headers, test_compliance_master):
        """Test filtering by category"""
        response = client.get("/api/v1/compliance-masters/?category=GST", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item["category"] == "GST" for item in data["items"])

    def test_list_with_frequency_filter(self, client, db_session, admin_headers, test_compliance_master):
        """Test filtering by frequency"""
        response = client.get("/api/v1/compliance-masters/?frequency=Monthly", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item["frequency"] == "Monthly" for item in data["items"])

    def test_list_with_is_active_filter(self, client, db_session, admin_headers, test_compliance_master):
        """Test filtering by active status"""
        # Create inactive master
        inactive_master = ComplianceMaster(
            tenant_id=test_compliance_master.tenant_id,
            compliance_code="INACTIVE-1",
            compliance_name="Inactive Master",
            category="GST",
            frequency="Monthly",
            due_date_rule={"type": "monthly", "day": 11, "offset_days": 0},
            is_active=False,
            is_template=False,
        )
        db_session.add(inactive_master)
        db_session.commit()

        response = client.get("/api/v1/compliance-masters/?is_active=true", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item["is_active"] is True for item in data["items"])

    def test_list_with_is_template_filter(
        self,
        client,
        db_session,
        admin_headers,
        test_compliance_master,
        system_template_master,
    ):
        """Test filtering by template status"""
        response = client.get("/api/v1/compliance-masters/?is_template=true", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item["is_template"] is True for item in data["items"])
        assert "TDS-24Q" in [item["compliance_code"] for item in data["items"]]

    def test_list_with_search(self, client, db_session, admin_headers, test_compliance_master):
        """Test searching by code and name"""
        response = client.get("/api/v1/compliance-masters/?search=GSTR", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        assert any("GSTR" in item["compliance_code"] for item in data["items"])

    def test_list_with_pagination(self, client, db_session, admin_headers, test_compliance_master):
        """Test pagination"""
        # Create additional masters
        for i in range(5):
            master = ComplianceMaster(
                tenant_id=test_compliance_master.tenant_id,
                compliance_code=f"TEST-{i}",
                compliance_name=f"Test Master {i}",
                category="GST",
                frequency="Monthly",
                due_date_rule={"type": "monthly", "day": 11, "offset_days": 0},
                is_active=True,
                is_template=False,
            )
            db_session.add(master)
        db_session.commit()

        response = client.get("/api/v1/compliance-masters/?skip=0&limit=3", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) <= 3
        assert data["skip"] == 0
        assert data["limit"] == 3

    def test_list_tenant_isolation(self, client, db_session, admin_headers, test_compliance_master):
        """Test that users only see their tenant's masters plus system templates"""
        # Create another tenant and master
        other_tenant = Tenant(
            tenant_code="OTHER_TENANT",
            tenant_name="Other Tenant",
            status="active",
        )
        db_session.add(other_tenant)
        db_session.commit()

        other_master = ComplianceMaster(
            tenant_id=other_tenant.id,
            compliance_code="OTHER-1",
            compliance_name="Other Tenant Master",
            category="GST",
            frequency="Monthly",
            due_date_rule={"type": "monthly", "day": 11, "offset_days": 0},
            is_active=True,
            is_template=False,
        )
        db_session.add(other_master)
        db_session.commit()

        response = client.get("/api/v1/compliance-masters/", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        codes = [item["compliance_code"] for item in data["items"]]
        assert "GSTR-1" in codes  # Own tenant
        assert "OTHER-1" not in codes  # Other tenant


class TestGetComplianceMaster:
    """Tests for getting a single compliance master"""

    def test_get_compliance_master_success(self, client, db_session, admin_headers, test_compliance_master):
        """Test successful retrieval of compliance master"""
        response = client.get(
            f"/api/v1/compliance-masters/{test_compliance_master.id}",
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_compliance_master.id)
        assert data["compliance_code"] == "GSTR-1"
        assert data["compliance_name"] == "GSTR-1 Monthly Return"

    def test_get_system_template(self, client, db_session, admin_headers, system_template_master):
        """Test tenant can access system templates"""
        response = client.get(
            f"/api/v1/compliance-masters/{system_template_master.id}",
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_template"] is True
        assert data["tenant_id"] is None

    def test_get_compliance_master_not_found(self, client, db_session, admin_headers):
        """Test getting non-existent compliance master"""
        fake_id = uuid.uuid4()
        response = client.get(f"/api/v1/compliance-masters/{fake_id}", headers=admin_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_other_tenant_master_forbidden(self, client, db_session, admin_headers):
        """Test cannot access other tenant's masters"""
        # Create another tenant and master
        other_tenant = Tenant(
            tenant_code="OTHER_TENANT_2",
            tenant_name="Other Tenant",
            status="active",
        )
        db_session.add(other_tenant)
        db_session.commit()

        other_master = ComplianceMaster(
            tenant_id=other_tenant.id,
            compliance_code="OTHER-MASTER",
            compliance_name="Other Master",
            category="GST",
            frequency="Monthly",
            due_date_rule={"type": "monthly", "day": 11, "offset_days": 0},
            is_active=True,
            is_template=False,
        )
        db_session.add(other_master)
        db_session.commit()

        response = client.get(f"/api/v1/compliance-masters/{other_master.id}", headers=admin_headers)

        # Either 404 (not found from tenant perspective) or 403 (forbidden)
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN]


class TestUpdateComplianceMaster:
    """Tests for updating compliance masters"""

    def test_update_compliance_master_success(self, client, db_session, admin_headers, test_compliance_master):
        """Test successful update of compliance master"""
        payload = {
            "compliance_name": "Updated GSTR-1 Return",
            "description": "Updated description",
        }

        response = client.put(
            f"/api/v1/compliance-masters/{test_compliance_master.id}",
            json=payload,
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["compliance_name"] == "Updated GSTR-1 Return"
        assert data["description"] == "Updated description"

    def test_update_partial_fields(self, client, db_session, admin_headers, test_compliance_master):
        """Test partial update of compliance master"""
        payload = {"is_active": False}

        response = client.put(
            f"/api/v1/compliance-masters/{test_compliance_master.id}",
            json=payload,
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is False
        # Other fields unchanged
        assert data["compliance_code"] == "GSTR-1"

    def test_update_system_template_requires_system_admin(
        self, client, db_session, admin_headers, system_template_master
    ):
        """Test that updating system templates requires system admin"""
        payload = {"compliance_name": "Updated Template"}

        response = client.put(
            f"/api/v1/compliance-masters/{system_template_master.id}",
            json=payload,
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_system_template_as_system_admin(
        self, client, db_session, system_admin_headers, system_template_master
    ):
        """Test system admin can update system templates"""
        payload = {"compliance_name": "Updated System Template"}

        response = client.put(
            f"/api/v1/compliance-masters/{system_template_master.id}",
            json=payload,
            headers=system_admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["compliance_name"] == "Updated System Template"

    def test_update_compliance_master_not_found(self, client, db_session, admin_headers):
        """Test updating non-existent compliance master"""
        fake_id = uuid.uuid4()
        payload = {"compliance_name": "Updated Name"}

        response = client.put(
            f"/api/v1/compliance-masters/{fake_id}",
            json=payload,
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_unauthorized_regular_user(self, client, db_session, regular_headers, test_compliance_master):
        """Test regular user cannot update compliance masters"""
        payload = {"compliance_name": "Updated Name"}

        response = client.put(
            f"/api/v1/compliance-masters/{test_compliance_master.id}",
            json=payload,
            headers=regular_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeleteComplianceMaster:
    """Tests for deleting compliance masters"""

    def test_delete_compliance_master_success(self, client, db_session, admin_headers, admin_user_fixture, test_tenant):
        """Test successful deletion of compliance master without instances"""
        master = ComplianceMaster(
            tenant_id=test_tenant.id,
            compliance_code="DELETE-TEST",
            compliance_name="To Be Deleted",
            category="GST",
            frequency="Monthly",
            due_date_rule={"type": "monthly", "day": 11, "offset_days": 0},
            is_active=True,
            is_template=False,
        )
        db_session.add(master)
        db_session.commit()

        response = client.delete(f"/api/v1/compliance-masters/{master.id}", headers=admin_headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify soft deleted (is_active=False)
        db_session.expire_all()  # Clear cached objects
        deleted = db_session.query(ComplianceMaster).filter(ComplianceMaster.id == master.id).first()
        # Soft delete: record exists but is_active=False OR hard delete: record is None
        assert deleted is None or deleted.is_active is False

    def test_delete_with_instances_without_force(
        self,
        client,
        db_session,
        admin_headers,
        test_compliance_master,
        admin_user_fixture,
        test_tenant,
    ):
        """Test deletion fails when master has instances without force flag"""
        # Create entity for instance
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="TEST-ENTITY",
            entity_name="Test Entity",
            status="active",
        )
        db_session.add(entity)
        db_session.commit()

        # Create instance
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=entity.id,
            period_start=datetime.now(),
            period_end=datetime.now() + timedelta(days=30),
            due_date=datetime.now() + timedelta(days=15),
            status="Pending",
        )
        db_session.add(instance)
        db_session.commit()

        response = client.delete(
            f"/api/v1/compliance-masters/{test_compliance_master.id}",
            headers=admin_headers,
        )

        # Either 400 (bad request) or 409 (conflict) for active instances
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT]
        assert "instances" in response.json()["detail"].lower()

    def test_delete_with_instances_with_force(
        self,
        client,
        db_session,
        admin_headers,
        test_compliance_master,
        admin_user_fixture,
        test_tenant,
    ):
        """Test soft deletion when master has instances with force flag"""
        # Create entity for instance
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_code="TEST-ENTITY-2",
            entity_name="Test Entity 2",
            status="active",
        )
        db_session.add(entity)
        db_session.commit()

        # Create instance
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=test_compliance_master.id,
            entity_id=entity.id,
            period_start=datetime.now(),
            period_end=datetime.now() + timedelta(days=30),
            due_date=datetime.now() + timedelta(days=15),
            status="Pending",
        )
        db_session.add(instance)
        db_session.commit()

        response = client.delete(
            f"/api/v1/compliance-masters/{test_compliance_master.id}?force=true",
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify soft deleted (is_active = False)
        db_session.refresh(test_compliance_master)
        assert test_compliance_master.is_active is False

    def test_delete_system_template_requires_system_admin(
        self, client, db_session, admin_headers, system_template_master
    ):
        """Test that deleting system templates requires system admin"""
        response = client.delete(
            f"/api/v1/compliance-masters/{system_template_master.id}",
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_system_template_as_system_admin(self, client, db_session, system_admin_headers, system_admin_user):
        """Test system admin can delete system templates"""
        template = ComplianceMaster(
            tenant_id=None,
            compliance_code="DELETE-TEMPLATE",
            compliance_name="Template to Delete",
            category="GST",
            frequency="Monthly",
            due_date_rule={"type": "monthly", "day": 11, "offset_days": 0},
            is_active=True,
            is_template=True,
        )
        db_session.add(template)
        db_session.commit()

        response = client.delete(
            f"/api/v1/compliance-masters/{template.id}",
            headers=system_admin_headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_compliance_master_not_found(self, client, db_session, admin_headers):
        """Test deleting non-existent compliance master"""
        fake_id = uuid.uuid4()
        response = client.delete(f"/api/v1/compliance-masters/{fake_id}", headers=admin_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestBulkImportComplianceMasters:
    """Tests for bulk importing compliance masters"""

    def test_bulk_import_success(self, client, db_session, admin_headers):
        """Test successful bulk import"""
        payload = {
            "masters": [
                {
                    "compliance_code": "BULK-1",
                    "compliance_name": "Bulk Import 1",
                    "category": "GST",
                    "frequency": "Monthly",
                    "due_date_rule": {"type": "monthly", "day": 10, "offset_days": 0},
                    "is_template": False,
                },
                {
                    "compliance_code": "BULK-2",
                    "compliance_name": "Bulk Import 2",
                    "category": "Direct Tax",
                    "frequency": "Quarterly",
                    "due_date_rule": {"type": "quarterly", "offset_days": 15},
                    "is_template": False,
                },
            ],
            "overwrite_existing": False,
        }

        response = client.post(
            "/api/v1/compliance-masters/bulk-import",
            json=payload,
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["created_count"] == 2
        assert data["updated_count"] == 0
        assert data["skipped_count"] == 0
        assert len(data["errors"]) == 0

    def test_bulk_import_with_overwrite(self, client, db_session, admin_headers, test_compliance_master):
        """Test bulk import with overwrite existing"""
        payload = {
            "masters": [
                {
                    "compliance_code": "GSTR-1",  # Existing
                    "compliance_name": "Updated via Bulk Import",
                    "category": "GST",
                    "frequency": "Monthly",
                    "due_date_rule": {"type": "monthly", "day": 11, "offset_days": 0},
                    "is_template": False,
                },
            ],
            "overwrite_existing": True,
        }

        response = client.post(
            "/api/v1/compliance-masters/bulk-import",
            json=payload,
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["updated_count"] == 1
        assert data["created_count"] == 0

    def test_bulk_import_skip_duplicates(self, client, db_session, admin_headers, test_compliance_master):
        """Test bulk import skips duplicates when overwrite=False"""
        payload = {
            "masters": [
                {
                    "compliance_code": "GSTR-1",  # Existing
                    "compliance_name": "Should be Skipped",
                    "category": "GST",
                    "frequency": "Monthly",
                    "due_date_rule": {"type": "monthly", "day": 11, "offset_days": 0},
                    "is_template": False,
                },
            ],
            "overwrite_existing": False,
        }

        response = client.post(
            "/api/v1/compliance-masters/bulk-import",
            json=payload,
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["skipped_count"] == 1
        assert data["created_count"] == 0
        assert data["updated_count"] == 0

    def test_bulk_import_templates_requires_system_admin(self, client, db_session, admin_headers):
        """Test bulk importing templates requires system admin"""
        payload = {
            "masters": [
                {
                    "compliance_code": "TEMPLATE-BULK",
                    "compliance_name": "Template via Bulk",
                    "category": "GST",
                    "frequency": "Monthly",
                    "due_date_rule": {"type": "monthly", "day": 11, "offset_days": 0},
                    "is_template": True,  # Template
                },
            ],
            "overwrite_existing": False,
        }

        response = client.post(
            "/api/v1/compliance-masters/bulk-import",
            json=payload,
            headers=admin_headers,
        )

        # Either:
        # - 200 OK with skipped_count=1 and errors (partial import approach)
        # - 403 Forbidden (strict role check approach)
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["skipped_count"] == 1
            assert len(data["errors"]) > 0
            assert (
                "system admin" in data["errors"][0]["error"].lower()
                or "permission" in data["errors"][0]["error"].lower()
            )
        else:
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_bulk_import_unauthorized_regular_user(self, client, db_session, regular_headers):
        """Test regular user cannot bulk import"""
        payload = {
            "masters": [
                {
                    "compliance_code": "BULK-TEST",
                    "compliance_name": "Bulk Test",
                    "category": "GST",
                    "frequency": "Monthly",
                    "due_date_rule": {"type": "monthly", "day": 11, "offset_days": 0},
                    "is_template": False,
                },
            ],
            "overwrite_existing": False,
        }

        response = client.post(
            "/api/v1/compliance-masters/bulk-import",
            json=payload,
            headers=regular_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
