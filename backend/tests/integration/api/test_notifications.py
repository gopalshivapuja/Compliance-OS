"""
Integration tests for Notification API endpoints
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Tenant, User, Role, Notification
from app.core.security import create_access_token
from app.services.notification_service import NotificationType


@pytest.fixture
def test_tenant(db_session: Session):
    """Create a test tenant"""
    tenant = Tenant(
        tenant_code="TEST_NOTIF",
        tenant_name="Test Notification Tenant",
        status="active",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def test_user(db_session: Session, test_tenant: Tenant):
    """Create a test user"""
    user = User(
        email="user@notifications.com",
        first_name="Test",
        last_name="User",
        tenant_id=test_tenant.id,
        status="active",
        is_system_admin=False,
    )
    user.set_password("TestPass123!")  # pragma: allowlist secret
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_user(db_session: Session, test_tenant: Tenant):
    """Create another user in the same tenant"""
    user = User(
        email="other@notifications.com",
        first_name="Other",
        last_name="User",
        tenant_id=test_tenant.id,
        status="active",
        is_system_admin=False,
    )
    user.set_password("OtherPass123!")  # pragma: allowlist secret
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User, test_tenant: Tenant):
    """Generate auth headers for the test user"""
    token_data = {
        "user_id": str(test_user.id),
        "tenant_id": str(test_tenant.id),
        "email": test_user.email,
    }
    token = create_access_token(data=token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_auth_headers(other_user: User, test_tenant: Tenant):
    """Generate auth headers for the other user"""
    token_data = {
        "user_id": str(other_user.id),
        "tenant_id": str(test_tenant.id),
        "email": other_user.email,
    }
    token = create_access_token(data=token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_notifications(db_session: Session, test_user: User, test_tenant: Tenant):
    """Create test notifications for the user"""
    notifications = []
    for i in range(5):
        notification = Notification(
            user_id=test_user.id,
            tenant_id=test_tenant.id,
            notification_type=NotificationType.TASK_ASSIGNED,
            title=f"Test Notification {i + 1}",
            message=f"This is test notification {i + 1}",
            link=f"/compliance-instances/{i + 1}",
            is_read=i < 2,  # First 2 are read
            created_at=datetime.utcnow(),
        )
        db_session.add(notification)
        notifications.append(notification)

    db_session.commit()
    for n in notifications:
        db_session.refresh(n)

    return notifications


class TestListNotifications:
    """Tests for GET /api/v1/notifications/"""

    def test_list_notifications_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should list notifications for authenticated user."""
        response = client.get("/api/v1/notifications/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 5
        assert "total" in data
        assert "unread_count" in data

    def test_list_notifications_unread_only(
        self,
        client: TestClient,
        auth_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should filter to unread only when specified."""
        response = client.get("/api/v1/notifications/?unread_only=true", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        # First 2 are read, so 3 should be unread
        assert len(data["items"]) == 3
        for item in data["items"]:
            assert item["is_read"] is False

    def test_list_notifications_pagination(
        self,
        client: TestClient,
        auth_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should support pagination with skip and limit."""
        response = client.get("/api/v1/notifications/?skip=2&limit=2", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["skip"] == 2
        assert data["limit"] == 2

    def test_list_notifications_requires_auth(self, client: TestClient):
        """Should require authentication (returns 403 for unauthenticated requests)."""
        response = client.get("/api/v1/notifications/")

        assert response.status_code == 403

    def test_list_notifications_empty(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Should return empty list if no notifications."""
        response = client.get("/api/v1/notifications/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_notifications_user_isolation(
        self,
        client: TestClient,
        other_auth_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should not show other user's notifications."""
        response = client.get("/api/v1/notifications/", headers=other_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


class TestGetNotificationCount:
    """Tests for GET /api/v1/notifications/count"""

    def test_get_notification_count_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should return unread count."""
        response = client.get("/api/v1/notifications/count", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "unread_count" in data
        assert data["unread_count"] == 3  # 5 total, 2 read

    def test_get_notification_count_requires_auth(self, client: TestClient):
        """Should require authentication (returns 403 for unauthenticated requests)."""
        response = client.get("/api/v1/notifications/count")

        assert response.status_code == 403

    def test_get_notification_count_zero(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Should return 0 when no notifications."""
        response = client.get("/api/v1/notifications/count", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] == 0


class TestGetNotification:
    """Tests for GET /api/v1/notifications/{notification_id}"""

    def test_get_notification_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should return specific notification."""
        notification = test_notifications[0]
        response = client.get(f"/api/v1/notifications/{notification.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(notification.id)
        assert data["title"] == notification.title

    def test_get_notification_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Should return 404 for non-existent notification."""
        import uuid

        fake_id = uuid.uuid4()
        response = client.get(f"/api/v1/notifications/{fake_id}", headers=auth_headers)

        assert response.status_code == 404

    def test_get_notification_other_user(
        self,
        client: TestClient,
        other_auth_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should not access other user's notification."""
        notification = test_notifications[0]
        response = client.get(f"/api/v1/notifications/{notification.id}", headers=other_auth_headers)

        assert response.status_code == 404


class TestMarkNotificationRead:
    """Tests for PUT /api/v1/notifications/{notification_id}/read"""

    def test_mark_notification_read_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should mark notification as read."""
        # Get an unread notification (index 2+ are unread)
        notification = test_notifications[2]
        assert notification.is_read is False

        response = client.put(f"/api/v1/notifications/{notification.id}/read", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["is_read"] is True
        assert data["read_at"] is not None

    def test_mark_notification_read_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Should return 404 for non-existent notification."""
        import uuid

        fake_id = uuid.uuid4()
        response = client.put(f"/api/v1/notifications/{fake_id}/read", headers=auth_headers)

        assert response.status_code == 404

    def test_mark_notification_read_idempotent(
        self,
        client: TestClient,
        auth_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should be idempotent (marking already read is OK)."""
        # First read notification is already read
        notification = test_notifications[0]

        response = client.put(f"/api/v1/notifications/{notification.id}/read", headers=auth_headers)

        assert response.status_code == 200


class TestMarkAllNotificationsRead:
    """Tests for POST /api/v1/notifications/mark-all-read"""

    def test_mark_all_read_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should mark all notifications as read."""
        response = client.post("/api/v1/notifications/mark-all-read", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "marked_count" in data
        assert data["marked_count"] == 3  # 3 were unread

        # Verify all are now read
        count_response = client.get("/api/v1/notifications/count", headers=auth_headers)
        assert count_response.json()["unread_count"] == 0

    def test_mark_all_read_none_unread(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Should return 0 if no unread notifications."""
        response = client.post("/api/v1/notifications/mark-all-read", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["marked_count"] == 0


class TestMarkMultipleNotificationsRead:
    """Tests for POST /api/v1/notifications/mark-read"""

    def test_mark_specific_notifications_read(
        self,
        client: TestClient,
        auth_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should mark specific notifications as read."""
        # Get 2 unread notification IDs
        ids_to_mark = [str(test_notifications[2].id), str(test_notifications[3].id)]

        response = client.post(
            "/api/v1/notifications/mark-read", headers=auth_headers, json={"notification_ids": ids_to_mark}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["marked_count"] == 2

    def test_mark_empty_list_marks_all(
        self,
        client: TestClient,
        auth_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should mark all when notification_ids is empty."""
        response = client.post("/api/v1/notifications/mark-read", headers=auth_headers, json={"notification_ids": []})

        assert response.status_code == 200
        data = response.json()
        assert data["marked_count"] == 3  # All unread


class TestDeleteNotification:
    """Tests for DELETE /api/v1/notifications/{notification_id}"""

    def test_delete_notification_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should delete notification."""
        notification = test_notifications[0]
        response = client.delete(f"/api/v1/notifications/{notification.id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify deleted
        get_response = client.get(f"/api/v1/notifications/{notification.id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_notification_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Should return 404 for non-existent notification."""
        import uuid

        fake_id = uuid.uuid4()
        response = client.delete(f"/api/v1/notifications/{fake_id}", headers=auth_headers)

        assert response.status_code == 404

    def test_delete_notification_other_user(
        self,
        client: TestClient,
        other_auth_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should not delete other user's notification."""
        notification = test_notifications[0]
        response = client.delete(f"/api/v1/notifications/{notification.id}", headers=other_auth_headers)

        assert response.status_code == 404


class TestDeleteMultipleNotifications:
    """Tests for DELETE /api/v1/notifications/"""

    def test_delete_multiple_notifications(
        self,
        client: TestClient,
        auth_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should delete multiple notifications."""
        ids_to_delete = f"{test_notifications[0].id},{test_notifications[1].id}"

        response = client.delete(f"/api/v1/notifications/?notification_ids={ids_to_delete}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 2

    def test_delete_empty_ids_fails(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Should fail if no IDs provided."""
        response = client.delete("/api/v1/notifications/?notification_ids=", headers=auth_headers)

        assert response.status_code == 400

    def test_delete_invalid_ids_skipped(
        self,
        client: TestClient,
        auth_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should skip invalid UUIDs."""
        # Mix valid and invalid IDs
        ids_to_delete = f"{test_notifications[0].id},invalid-uuid,{test_notifications[1].id}"

        response = client.delete(f"/api/v1/notifications/?notification_ids={ids_to_delete}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 2  # Only valid ones deleted


class TestNotificationTenantIsolation:
    """Tests for multi-tenant isolation"""

    @pytest.fixture
    def other_tenant(self, db_session: Session):
        """Create another tenant"""
        tenant = Tenant(
            tenant_code="OTHER_TENANT",
            tenant_name="Other Tenant",
            status="active",
        )
        db_session.add(tenant)
        db_session.commit()
        db_session.refresh(tenant)
        return tenant

    @pytest.fixture
    def other_tenant_user(self, db_session: Session, other_tenant: Tenant):
        """Create user in other tenant"""
        user = User(
            email="user@other.com",
            first_name="Other",
            last_name="Tenant",
            tenant_id=other_tenant.id,
            status="active",
            is_system_admin=False,
        )
        user.set_password("OtherPass123!")  # pragma: allowlist secret
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def other_tenant_headers(self, other_tenant_user: User, other_tenant: Tenant):
        """Generate auth headers for other tenant user"""
        token_data = {
            "user_id": str(other_tenant_user.id),
            "tenant_id": str(other_tenant.id),
            "email": other_tenant_user.email,
        }
        token = create_access_token(data=token_data)
        return {"Authorization": f"Bearer {token}"}

    def test_cross_tenant_notification_access(
        self,
        client: TestClient,
        other_tenant_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should not see notifications from other tenants."""
        response = client.get("/api/v1/notifications/", headers=other_tenant_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_cross_tenant_notification_count(
        self,
        client: TestClient,
        other_tenant_headers: dict,
        test_notifications: list[Notification],
    ):
        """Should not count notifications from other tenants."""
        response = client.get("/api/v1/notifications/count", headers=other_tenant_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] == 0
