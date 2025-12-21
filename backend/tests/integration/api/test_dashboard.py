"""
Integration tests for Dashboard endpoints.
Tests overview, overdue, upcoming, and category breakdown endpoints.
Includes multi-tenant isolation, RAG aggregation, and pagination tests.
"""

import pytest
from datetime import date, timedelta

from app.models import (
    Tenant,
    User,
    Entity,
    ComplianceMaster,
    ComplianceInstance,
)
from app.core.security import get_password_hash, create_access_token


@pytest.fixture
def test_entities(db_session, test_tenant):
    """Create test entities for compliance instances."""
    entity1 = Entity(
        tenant_id=test_tenant.id,
        entity_code="ENT001",
        entity_name="Test Entity 1",
        entity_type="Company",
        pan="AAAAA1234A",
        gstin="27AAAAA1234A1Z5",
        status="active",
    )
    entity2 = Entity(
        tenant_id=test_tenant.id,
        entity_code="ENT002",
        entity_name="Test Entity 2",
        entity_type="Branch",
        pan="BBBBB5678B",
        status="active",
    )
    db_session.add_all([entity1, entity2])
    db_session.commit()
    db_session.refresh(entity1)
    db_session.refresh(entity2)
    return [entity1, entity2]


@pytest.fixture
def test_compliance_masters(db_session, test_tenant):
    """Create test compliance masters across different categories."""
    masters = []

    # GST Compliance
    gst_master = ComplianceMaster(
        tenant_id=test_tenant.id,
        compliance_code="GSTR-1",
        compliance_name="GSTR-1 Monthly Return",
        description="Monthly GST return filing",
        category="GST",
        sub_category="Regular",
        frequency="Monthly",
        due_date_rule={"type": "monthly", "day": 11, "offset_days": 0},
        is_active=True,
        is_template=False,
        authority="CBIC",
    )
    masters.append(gst_master)

    # Direct Tax Compliance
    tax_master = ComplianceMaster(
        tenant_id=test_tenant.id,
        compliance_code="TDS-24Q",
        compliance_name="TDS Return for Salaries",
        description="Quarterly TDS return",
        category="Direct Tax",
        sub_category="TDS",
        frequency="Quarterly",
        due_date_rule={"type": "quarterly", "offset_days": 15},
        is_active=True,
        is_template=False,
        authority="Income Tax Department",
    )
    masters.append(tax_master)

    # Payroll Compliance
    payroll_master = ComplianceMaster(
        tenant_id=test_tenant.id,
        compliance_code="PF-12A",
        compliance_name="PF Return Monthly",
        description="Monthly PF contribution return",
        category="Payroll",
        sub_category="PF",
        frequency="Monthly",
        due_date_rule={"type": "monthly", "day": 15, "offset_days": 0},
        is_active=True,
        is_template=False,
        authority="EPFO",
    )
    masters.append(payroll_master)

    db_session.add_all(masters)
    db_session.commit()
    for master in masters:
        db_session.refresh(master)
    return masters


@pytest.fixture
def test_compliance_instances(db_session, test_tenant, test_entities, test_compliance_masters, test_user):
    """Create test compliance instances with various statuses and RAG colors."""
    today = date.today()
    instances = []

    # Green - On track, due in 10 days
    green_instance = ComplianceInstance(
        tenant_id=test_tenant.id,
        compliance_master_id=test_compliance_masters[0].id,
        entity_id=test_entities[0].id,
        period_start=date(today.year, today.month, 1),
        period_end=date(today.year, today.month, 28),
        due_date=today + timedelta(days=10),
        status="In Progress",
        rag_status="Green",
        owner_user_id=test_user.id,
    )
    instances.append(green_instance)

    # Amber - At risk, due in 5 days
    amber_instance = ComplianceInstance(
        tenant_id=test_tenant.id,
        compliance_master_id=test_compliance_masters[1].id,
        entity_id=test_entities[0].id,
        period_start=date(today.year, today.month, 1),
        period_end=date(today.year, today.month, 28),
        due_date=today + timedelta(days=5),
        status="Not Started",
        rag_status="Amber",
        owner_user_id=test_user.id,
    )
    instances.append(amber_instance)

    # Red - Overdue by 3 days
    red_instance = ComplianceInstance(
        tenant_id=test_tenant.id,
        compliance_master_id=test_compliance_masters[2].id,
        entity_id=test_entities[1].id,
        period_start=date(today.year, today.month - 1 if today.month > 1 else 12, 1),
        period_end=date(today.year, today.month - 1 if today.month > 1 else 12, 28),
        due_date=today - timedelta(days=3),
        status="In Progress",
        rag_status="Red",
        owner_user_id=test_user.id,
    )
    instances.append(red_instance)

    # Green - Completed (should not show in overdue/upcoming)
    completed_instance = ComplianceInstance(
        tenant_id=test_tenant.id,
        compliance_master_id=test_compliance_masters[0].id,
        entity_id=test_entities[1].id,
        period_start=date(today.year, today.month - 2 if today.month > 2 else 10, 1),
        period_end=date(today.year, today.month - 2 if today.month > 2 else 10, 28),
        due_date=today - timedelta(days=10),
        status="Completed",
        rag_status="Green",
        filed_date=today - timedelta(days=12),
        completion_date=today - timedelta(days=12),
        owner_user_id=test_user.id,
    )
    instances.append(completed_instance)

    # Amber - Another GST instance for category breakdown
    amber_instance_2 = ComplianceInstance(
        tenant_id=test_tenant.id,
        compliance_master_id=test_compliance_masters[0].id,
        entity_id=test_entities[0].id,
        period_start=date(today.year, today.month - 1 if today.month > 1 else 12, 1),
        period_end=date(today.year, today.month - 1 if today.month > 1 else 12, 28),
        due_date=today + timedelta(days=6),
        status="Review",
        rag_status="Amber",
        owner_user_id=test_user.id,
    )
    instances.append(amber_instance_2)

    db_session.add_all(instances)
    db_session.commit()
    for instance in instances:
        db_session.refresh(instance)
    return instances


@pytest.fixture
def other_tenant_data(db_session):
    """Create another tenant with data for multi-tenant isolation tests."""
    # Create other tenant
    other_tenant = Tenant(
        tenant_name="Other Company",
        tenant_code="OTHER001",
        contact_email="other@example.com",
        status="active",
    )
    db_session.add(other_tenant)
    db_session.flush()

    # Create other user
    other_user = User(
        tenant_id=other_tenant.id,
        email="otheruser@example.com",
        first_name="Other",
        last_name="User",
        password_hash=get_password_hash("OtherPass123!"),
        status="active",
    )
    db_session.add(other_user)
    db_session.flush()

    # Create other entity
    other_entity = Entity(
        tenant_id=other_tenant.id,
        entity_code="OTHER-ENT001",
        entity_name="Other Entity",
        entity_type="Company",
        status="active",
    )
    db_session.add(other_entity)
    db_session.flush()

    # Create other compliance master
    other_master = ComplianceMaster(
        tenant_id=other_tenant.id,
        compliance_code="OTHER-COMP",
        compliance_name="Other Compliance",
        category="GST",
        frequency="Monthly",
        due_date_rule={"type": "monthly", "day": 20},
        is_active=True,
    )
    db_session.add(other_master)
    db_session.flush()

    # Create other compliance instance
    today = date.today()
    other_instance = ComplianceInstance(
        tenant_id=other_tenant.id,
        compliance_master_id=other_master.id,
        entity_id=other_entity.id,
        period_start=today,
        period_end=today + timedelta(days=30),
        due_date=today + timedelta(days=5),
        status="Not Started",
        rag_status="Amber",
    )
    db_session.add(other_instance)
    db_session.commit()
    db_session.refresh(other_tenant)
    db_session.refresh(other_user)

    return {"tenant": other_tenant, "user": other_user}


@pytest.fixture
def auth_headers_with_tenant(test_tenant, test_user):
    """Create auth headers with tenant_id in JWT payload."""
    token = create_access_token(
        data={
            "user_id": str(test_user.id),
            "tenant_id": str(test_tenant.id),
            "email": test_user.email,
            "roles": [role.role_code for role in test_user.roles] if test_user.roles else [],
        }
    )
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_overview_success(
    client: TestClient,
    auth_headers_with_tenant,
    test_compliance_instances,
):
    """Test GET /api/v1/dashboard/overview returns correct aggregated data."""
    response = client.get(
        "/api/v1/dashboard/overview",
        headers=auth_headers_with_tenant,
    )

    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert "total_compliances" in data
    assert "rag_counts" in data
    assert "overdue_count" in data
    assert "upcoming_count" in data
    assert "category_breakdown" in data

    # Verify counts (5 instances total, 1 completed shouldn't affect RAG counts)
    assert data["total_compliances"] == 5

    # Verify RAG counts (2 Green, 2 Amber, 1 Red)
    rag = data["rag_counts"]
    assert rag["green"] == 2
    assert rag["amber"] == 2
    assert rag["red"] == 1

    # Verify overdue count (1 instance with due_date in past and not completed)
    assert data["overdue_count"] == 1

    # Verify upcoming count (2 instances due in next 7 days)
    assert data["upcoming_count"] == 2

    # Verify category breakdown exists
    assert len(data["category_breakdown"]) > 0
    assert isinstance(data["category_breakdown"], list)


def test_dashboard_overview_rag_aggregation(
    client: TestClient,
    auth_headers_with_tenant,
    test_compliance_instances,
):
    """Verify RAG status aggregation is mathematically correct."""
    response = client.get(
        "/api/v1/dashboard/overview",
        headers=auth_headers_with_tenant,
    )

    assert response.status_code == 200
    data = response.json()

    rag = data["rag_counts"]
    total_rag = rag["green"] + rag["amber"] + rag["red"]

    # Total RAG count should equal total compliances
    assert total_rag == data["total_compliances"]


def test_dashboard_overview_category_breakdown(
    client: TestClient,
    auth_headers_with_tenant,
    test_compliance_instances,
):
    """Test category breakdown returns correct RAG distribution per category."""
    response = client.get(
        "/api/v1/dashboard/overview",
        headers=auth_headers_with_tenant,
    )

    assert response.status_code == 200
    data = response.json()

    categories = data["category_breakdown"]
    assert len(categories) == 3  # GST, Direct Tax, Payroll

    # Find GST category (should have 3 instances based on fixture:
    # - green_instance: Green, In Progress
    # - completed_instance: Green, Completed
    # - amber_instance_2: Amber, Review
    # So: green=2, amber=1)
    gst_category = next((c for c in categories if c["category"] == "GST"), None)
    assert gst_category is not None
    assert gst_category["total"] == 3
    assert gst_category["green"] == 2  # 1 in progress + 1 completed
    assert gst_category["amber"] == 1
    assert gst_category["red"] == 0

    # Verify each category has correct structure
    for category in categories:
        assert "category" in category
        assert "green" in category
        assert "amber" in category
        assert "red" in category
        assert "total" in category
        assert category["total"] == category["green"] + category["amber"] + category["red"]


def test_dashboard_overdue_items(
    client: TestClient,
    auth_headers_with_tenant,
    test_compliance_instances,
):
    """Test GET /api/v1/dashboard/overdue returns only overdue instances."""
    response = client.get(
        "/api/v1/dashboard/overdue",
        headers=auth_headers_with_tenant,
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1  # Only 1 overdue instance (completed ones excluded)

    # Verify overdue instance details
    overdue = data[0]
    assert "compliance_instance_id" in overdue
    assert "compliance_name" in overdue
    assert "entity_name" in overdue
    assert "due_date" in overdue
    assert "rag_status" in overdue
    assert "days_overdue" in overdue

    # Verify it's actually overdue
    assert overdue["days_overdue"] > 0
    assert overdue["rag_status"] == "Red"


def test_dashboard_overdue_pagination(
    client: TestClient,
    auth_headers_with_tenant,
    test_compliance_instances,
):
    """Test overdue endpoint pagination with skip and limit."""
    # Get first page
    response = client.get(
        "/api/v1/dashboard/overdue?skip=0&limit=1",
        headers=auth_headers_with_tenant,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 1

    # Get second page (should be empty as we only have 1 overdue)
    response = client.get(
        "/api/v1/dashboard/overdue?skip=1&limit=1",
        headers=auth_headers_with_tenant,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_dashboard_upcoming_items(
    client: TestClient,
    auth_headers_with_tenant,
    test_compliance_instances,
):
    """Test GET /api/v1/dashboard/upcoming returns items due in next N days."""
    response = client.get(
        "/api/v1/dashboard/upcoming?days=7",
        headers=auth_headers_with_tenant,
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 2  # 2 instances due in next 7 days (5 and 6 days)

    # Verify upcoming instance details
    for item in data:
        assert "compliance_instance_id" in item
        assert "due_date" in item
        assert "days_overdue" in item
        # days_overdue should be negative for upcoming items
        assert item["days_overdue"] <= 0


def test_dashboard_upcoming_custom_days(
    client: TestClient,
    auth_headers_with_tenant,
    test_compliance_instances,
):
    """Test upcoming endpoint with custom days parameter."""
    # Look ahead 3 days (should find 0 items as nearest is 5 days away)
    response = client.get(
        "/api/v1/dashboard/upcoming?days=3",
        headers=auth_headers_with_tenant,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

    # Look ahead 15 days (should find 3 items: 5, 6, and 10 days away)
    response = client.get(
        "/api/v1/dashboard/upcoming?days=15",
        headers=auth_headers_with_tenant,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_dashboard_category_breakdown(
    client: TestClient,
    auth_headers_with_tenant,
    test_compliance_instances,
):
    """Test GET /api/v1/dashboard/category-breakdown returns correct data."""
    response = client.get(
        "/api/v1/dashboard/category-breakdown",
        headers=auth_headers_with_tenant,
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 3  # GST, Direct Tax, Payroll

    # Verify structure
    for category in data:
        assert "category" in category
        assert "green" in category
        assert "amber" in category
        assert "red" in category
        assert "total" in category


def test_dashboard_multi_tenant_isolation(
    client: TestClient,
    auth_headers_with_tenant,
    other_tenant_data,
    test_compliance_instances,
):
    """Test that dashboard only shows data for the authenticated user's tenant."""
    # Get dashboard for test tenant
    response = client.get(
        "/api/v1/dashboard/overview",
        headers=auth_headers_with_tenant,
    )

    assert response.status_code == 200
    data = response.json()

    # Should only see test tenant's 5 instances, not other tenant's data
    assert data["total_compliances"] == 5

    # Create auth headers for other tenant
    other_user = other_tenant_data["user"]
    other_tenant = other_tenant_data["tenant"]
    other_token = create_access_token(
        data={
            "sub": str(other_user.id),
            "tenant_id": str(other_tenant.id),
            "email": other_user.email,
            "roles": [],
        }
    )
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Get dashboard for other tenant
    response = client.get(
        "/api/v1/dashboard/overview",
        headers=other_headers,
    )

    assert response.status_code == 200
    other_data = response.json()

    # Should only see other tenant's 1 instance
    assert other_data["total_compliances"] == 1
    assert other_data["rag_counts"]["amber"] == 1


def test_dashboard_unauthorized(client: TestClient, test_compliance_instances):
    """Test dashboard endpoints return 401/403 without authentication."""
    response = client.get("/api/v1/dashboard/overview")
    assert response.status_code in [401, 403]

    response = client.get("/api/v1/dashboard/overdue")
    assert response.status_code in [401, 403]

    response = client.get("/api/v1/dashboard/upcoming")
    assert response.status_code in [401, 403]

    response = client.get("/api/v1/dashboard/category-breakdown")
    assert response.status_code in [401, 403]


def test_dashboard_empty_data(client: TestClient, test_tenant, test_user):
    """Test dashboard endpoints with no compliance instances."""
    token = create_access_token(
        data={
            "sub": str(test_user.id),
            "tenant_id": str(test_tenant.id),
            "email": test_user.email,
            "roles": [],
        }
    )
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/dashboard/overview", headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Should handle empty data gracefully
    assert data["total_compliances"] == 0
    assert data["rag_counts"]["green"] == 0
    assert data["rag_counts"]["amber"] == 0
    assert data["rag_counts"]["red"] == 0
    assert data["overdue_count"] == 0
    assert data["upcoming_count"] == 0
    assert data["category_breakdown"] == []
