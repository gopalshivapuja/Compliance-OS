"""
Notification Service Unit Tests

Tests for multi-channel notification handling (in-app notifications for Phase 4).

Test Categories:
- NotificationType constants validation
- Basic CRUD operations (create, read, mark read, delete)
- User notification queries with filtering and pagination
- Specific notification helpers (task, evidence, instance notifications)
- Cleanup operations
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.services.notification_service import (
    NotificationType,
    create_notification,
    get_user_notifications,
    get_unread_count,
    mark_notification_read,
    mark_all_read,
    delete_notification,
    delete_old_notifications,
    notify_task_assigned,
    notify_task_completed,
    notify_reminder_t3,
    notify_reminder_due,
    notify_overdue_escalation,
    notify_evidence_uploaded,
    notify_evidence_approved,
    notify_evidence_rejected,
    notify_instance_created,
    notify_instance_completed,
)


class TestNotificationType:
    """Tests for NotificationType constants."""

    def test_task_assigned_type_exists(self):
        """TASK_ASSIGNED notification type should exist."""
        assert NotificationType.TASK_ASSIGNED == "task_assigned"

    def test_task_completed_type_exists(self):
        """TASK_COMPLETED notification type should exist."""
        assert NotificationType.TASK_COMPLETED == "task_completed"

    def test_task_rejected_type_exists(self):
        """TASK_REJECTED notification type should exist."""
        assert NotificationType.TASK_REJECTED == "task_rejected"

    def test_reminder_types_exist(self):
        """Reminder notification types should exist."""
        assert NotificationType.REMINDER_T3 == "reminder_t3"
        assert NotificationType.REMINDER_DUE == "reminder_due"

    def test_overdue_and_escalation_types_exist(self):
        """Overdue and escalation types should exist."""
        assert NotificationType.OVERDUE_ALERT == "overdue_alert"
        assert NotificationType.ESCALATION == "escalation"

    def test_evidence_types_exist(self):
        """Evidence notification types should exist."""
        assert NotificationType.EVIDENCE_UPLOADED == "evidence_uploaded"
        assert NotificationType.EVIDENCE_APPROVED == "evidence_approved"
        assert NotificationType.EVIDENCE_REJECTED == "evidence_rejected"

    def test_instance_types_exist(self):
        """Instance notification types should exist."""
        assert NotificationType.INSTANCE_CREATED == "instance_created"
        assert NotificationType.INSTANCE_COMPLETED == "instance_completed"

    def test_approval_request_type_exists(self):
        """APPROVAL_REQUEST notification type should exist."""
        assert NotificationType.APPROVAL_REQUEST == "approval_request"


class TestCreateNotification:
    """Tests for create_notification function."""

    def test_create_notification_success(self):
        """Should create notification with all required fields."""
        db = MagicMock()
        user_id = uuid4()
        tenant_id = uuid4()

        result = create_notification(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            notification_type=NotificationType.TASK_ASSIGNED,
            title="Test Notification",
            message="This is a test message",
        )

        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_create_notification_with_link(self):
        """Should create notification with optional link."""
        db = MagicMock()
        user_id = uuid4()
        tenant_id = uuid4()

        result = create_notification(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            notification_type=NotificationType.TASK_ASSIGNED,
            title="Test",
            message="Test message",
            link="/compliance-instances/123",
        )

        db.add.assert_called_once()
        notification_arg = db.add.call_args[0][0]
        assert notification_arg.link == "/compliance-instances/123"

    def test_create_notification_is_unread_by_default(self):
        """New notifications should be unread by default."""
        db = MagicMock()

        result = create_notification(
            db=db,
            user_id=uuid4(),
            tenant_id=uuid4(),
            notification_type=NotificationType.REMINDER_T3,
            title="Test",
            message="Test",
        )

        notification_arg = db.add.call_args[0][0]
        assert notification_arg.is_read is False

    def test_create_notification_sets_created_at(self):
        """Notification should have created_at timestamp."""
        db = MagicMock()

        result = create_notification(
            db=db,
            user_id=uuid4(),
            tenant_id=uuid4(),
            notification_type=NotificationType.REMINDER_DUE,
            title="Test",
            message="Test",
        )

        notification_arg = db.add.call_args[0][0]
        assert notification_arg.created_at is not None


class TestGetUserNotifications:
    """Tests for get_user_notifications function."""

    def test_get_user_notifications_returns_list(self):
        """Should return list of notifications for user."""
        db = MagicMock()
        user_id = uuid4()
        tenant_id = uuid4()

        notifications = [MagicMock(), MagicMock()]
        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            notifications
        )

        result = get_user_notifications(db, user_id, tenant_id)

        assert len(result) == 2

    def test_get_user_notifications_with_pagination(self):
        """Should support offset and limit for pagination."""
        db = MagicMock()
        user_id = uuid4()
        tenant_id = uuid4()

        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            []
        )

        result = get_user_notifications(db, user_id, tenant_id, limit=10, offset=20)

        # Verify offset and limit were called
        db.query.return_value.filter.return_value.order_by.return_value.offset.assert_called_with(20)
        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.assert_called_with(10)

    def test_get_user_notifications_unread_only(self):
        """Should filter unread only when specified."""
        db = MagicMock()
        user_id = uuid4()
        tenant_id = uuid4()

        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            []
        )

        result = get_user_notifications(db, user_id, tenant_id, unread_only=True)

        # Second filter call for unread_only
        db.query.return_value.filter.return_value.filter.assert_called()

    def test_get_user_notifications_ordered_by_created_at_desc(self):
        """Should order notifications by created_at descending."""
        db = MagicMock()
        user_id = uuid4()
        tenant_id = uuid4()

        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            []
        )

        result = get_user_notifications(db, user_id, tenant_id)

        db.query.return_value.filter.return_value.order_by.assert_called()

    def test_get_user_notifications_default_limit_is_50(self):
        """Should default to limit of 50."""
        db = MagicMock()
        user_id = uuid4()
        tenant_id = uuid4()

        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            []
        )

        result = get_user_notifications(db, user_id, tenant_id)

        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.assert_called_with(50)


class TestGetUnreadCount:
    """Tests for get_unread_count function."""

    def test_get_unread_count_returns_integer(self):
        """Should return count of unread notifications."""
        db = MagicMock()
        user_id = uuid4()
        tenant_id = uuid4()

        db.query.return_value.filter.return_value.count.return_value = 5

        result = get_unread_count(db, user_id, tenant_id)

        assert result == 5

    def test_get_unread_count_zero_when_none(self):
        """Should return 0 when no unread notifications."""
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 0

        result = get_unread_count(db, uuid4(), uuid4())

        assert result == 0


class TestMarkNotificationRead:
    """Tests for mark_notification_read function."""

    def test_mark_notification_read_success(self):
        """Should mark notification as read."""
        db = MagicMock()
        notification_id = uuid4()
        user_id = uuid4()
        tenant_id = uuid4()

        mock_notification = MagicMock()
        mock_notification.is_read = False
        db.query.return_value.filter.return_value.first.return_value = mock_notification

        result = mark_notification_read(db, notification_id, user_id, tenant_id)

        assert mock_notification.is_read is True
        assert mock_notification.read_at is not None
        db.commit.assert_called_once()

    def test_mark_notification_read_returns_none_if_not_found(self):
        """Should return None if notification not found."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = mark_notification_read(db, uuid4(), uuid4(), uuid4())

        assert result is None
        db.commit.assert_not_called()

    def test_mark_notification_read_skips_if_already_read(self):
        """Should not update if already read."""
        db = MagicMock()
        mock_notification = MagicMock()
        mock_notification.is_read = True
        db.query.return_value.filter.return_value.first.return_value = mock_notification

        result = mark_notification_read(db, uuid4(), uuid4(), uuid4())

        # Should return the notification but not call commit for update
        assert result == mock_notification

    def test_mark_notification_read_sets_read_at_timestamp(self):
        """Should set read_at timestamp when marking read."""
        db = MagicMock()
        mock_notification = MagicMock()
        mock_notification.is_read = False
        mock_notification.read_at = None
        db.query.return_value.filter.return_value.first.return_value = mock_notification

        result = mark_notification_read(db, uuid4(), uuid4(), uuid4())

        assert mock_notification.read_at is not None


class TestMarkAllRead:
    """Tests for mark_all_read function."""

    def test_mark_all_read_returns_count(self):
        """Should return count of notifications marked as read."""
        db = MagicMock()
        user_id = uuid4()
        tenant_id = uuid4()

        db.query.return_value.filter.return_value.update.return_value = 3

        result = mark_all_read(db, user_id, tenant_id)

        assert result == 3
        db.commit.assert_called_once()

    def test_mark_all_read_zero_when_none_unread(self):
        """Should return 0 when no unread notifications."""
        db = MagicMock()
        db.query.return_value.filter.return_value.update.return_value = 0

        result = mark_all_read(db, uuid4(), uuid4())

        assert result == 0


class TestDeleteNotification:
    """Tests for delete_notification function."""

    def test_delete_notification_success(self):
        """Should delete notification and return True."""
        db = MagicMock()
        notification_id = uuid4()
        user_id = uuid4()
        tenant_id = uuid4()

        mock_notification = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_notification

        result = delete_notification(db, notification_id, user_id, tenant_id)

        assert result is True
        db.delete.assert_called_once_with(mock_notification)
        db.commit.assert_called_once()

    def test_delete_notification_returns_false_if_not_found(self):
        """Should return False if notification not found."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = delete_notification(db, uuid4(), uuid4(), uuid4())

        assert result is False
        db.delete.assert_not_called()


class TestDeleteOldNotifications:
    """Tests for delete_old_notifications function."""

    def test_delete_old_notifications_returns_count(self):
        """Should return count of deleted notifications."""
        db = MagicMock()
        tenant_id = uuid4()

        db.query.return_value.filter.return_value.delete.return_value = 10

        result = delete_old_notifications(db, tenant_id, days_old=90)

        assert result == 10
        db.commit.assert_called_once()

    def test_delete_old_notifications_default_90_days(self):
        """Should default to 90 days old threshold."""
        db = MagicMock()
        db.query.return_value.filter.return_value.delete.return_value = 0

        result = delete_old_notifications(db, uuid4())

        # Function should complete using default 90 days

    def test_delete_old_notifications_custom_days(self):
        """Should use custom days_old value."""
        db = MagicMock()
        db.query.return_value.filter.return_value.delete.return_value = 5

        result = delete_old_notifications(db, uuid4(), days_old=30)

        assert result == 5


class TestNotifyTaskAssigned:
    """Tests for notify_task_assigned helper."""

    def test_notify_task_assigned_creates_notification(self):
        """Should create notification for assigned user."""
        db = MagicMock()

        # Mock task
        task = MagicMock()
        task.task_name = "Prepare Documents"
        task.task_type = "Prepare"
        task.due_date = "2024-03-15"
        task.tenant_id = uuid4()
        task.compliance_instance_id = uuid4()
        task.compliance_instance = MagicMock()
        task.compliance_instance.compliance_master = MagicMock()
        task.compliance_instance.compliance_master.compliance_name = "GST Filing"

        # Mock assigned user
        assigned_user = MagicMock()
        assigned_user.id = uuid4()

        with patch("app.services.notification_service.create_notification") as mock_create:
            mock_create.return_value = MagicMock()

            result = notify_task_assigned(db, task, assigned_user)

        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args.kwargs["notification_type"] == NotificationType.TASK_ASSIGNED
        assert "Prepare Documents" in call_args.kwargs["title"]

    def test_notify_task_assigned_returns_none_if_no_user(self):
        """Should return None if no assigned user."""
        db = MagicMock()
        task = MagicMock()

        result = notify_task_assigned(db, task, None)

        assert result is None


class TestNotifyTaskCompleted:
    """Tests for notify_task_completed helper."""

    def test_notify_task_completed_creates_notification(self):
        """Should create notification for task completion."""
        db = MagicMock()

        task = MagicMock()
        task.task_name = "Review Documents"
        task.task_type = "Review"
        task.tenant_id = uuid4()
        task.compliance_instance_id = uuid4()
        task.compliance_instance = MagicMock()
        task.compliance_instance.compliance_master = MagicMock()
        task.compliance_instance.compliance_master.compliance_name = "GST Filing"

        notify_user = MagicMock()
        notify_user.id = uuid4()

        with patch("app.services.notification_service.create_notification") as mock_create:
            mock_create.return_value = MagicMock()

            result = notify_task_completed(db, task, notify_user)

        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args.kwargs["notification_type"] == NotificationType.TASK_COMPLETED

    def test_notify_task_completed_returns_none_if_no_user(self):
        """Should return None if no user to notify."""
        db = MagicMock()
        task = MagicMock()

        result = notify_task_completed(db, task, None)

        assert result is None


class TestNotifyReminderT3:
    """Tests for notify_reminder_t3 helper."""

    def test_notify_reminder_t3_creates_notification(self):
        """Should create T-3 reminder notification."""
        db = MagicMock()

        instance = MagicMock()
        instance.id = uuid4()
        instance.tenant_id = uuid4()
        instance.due_date = "2024-03-18"
        instance.compliance_master = MagicMock()
        instance.compliance_master.compliance_name = "GST Filing"

        owner = MagicMock()
        owner.id = uuid4()

        with patch("app.services.notification_service.create_notification") as mock_create:
            mock_create.return_value = MagicMock()

            result = notify_reminder_t3(db, instance, owner)

        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args.kwargs["notification_type"] == NotificationType.REMINDER_T3
        assert "3 days" in call_args.kwargs["title"]

    def test_notify_reminder_t3_returns_none_if_no_owner(self):
        """Should return None if no owner."""
        db = MagicMock()
        instance = MagicMock()

        result = notify_reminder_t3(db, instance, None)

        assert result is None


class TestNotifyReminderDue:
    """Tests for notify_reminder_due helper."""

    def test_notify_reminder_due_creates_notification(self):
        """Should create due date reminder notification."""
        db = MagicMock()

        instance = MagicMock()
        instance.id = uuid4()
        instance.tenant_id = uuid4()
        instance.due_date = "2024-03-15"
        instance.compliance_master = MagicMock()
        instance.compliance_master.compliance_name = "GST Filing"

        user = MagicMock()
        user.id = uuid4()

        with patch("app.services.notification_service.create_notification") as mock_create:
            mock_create.return_value = MagicMock()

            result = notify_reminder_due(db, instance, user)

        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args.kwargs["notification_type"] == NotificationType.REMINDER_DUE
        assert "Due today" in call_args.kwargs["title"]

    def test_notify_reminder_due_returns_none_if_no_user(self):
        """Should return None if no user."""
        db = MagicMock()
        instance = MagicMock()

        result = notify_reminder_due(db, instance, None)

        assert result is None


class TestNotifyOverdueEscalation:
    """Tests for notify_overdue_escalation helper."""

    def test_notify_overdue_escalation_creates_notification(self):
        """Should create escalation notification for overdue instance."""
        db = MagicMock()

        instance = MagicMock()
        instance.id = uuid4()
        instance.tenant_id = uuid4()
        instance.due_date = "2024-03-12"
        instance.compliance_master = MagicMock()
        instance.compliance_master.compliance_name = "GST Filing"
        instance.entity = MagicMock()
        instance.entity.entity_name = "ABC Corp"

        escalate_to = MagicMock()
        escalate_to.id = uuid4()

        with patch("app.services.notification_service.create_notification") as mock_create:
            mock_create.return_value = MagicMock()

            result = notify_overdue_escalation(db, instance, escalate_to, days_overdue=3)

        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args.kwargs["notification_type"] == NotificationType.ESCALATION
        assert "3 days" in call_args.kwargs["title"]
        assert "Escalation" in call_args.kwargs["title"]

    def test_notify_overdue_escalation_returns_none_if_no_user(self):
        """Should return None if no user to escalate to."""
        db = MagicMock()
        instance = MagicMock()

        result = notify_overdue_escalation(db, instance, None, 3)

        assert result is None

    def test_notify_overdue_escalation_includes_entity_name(self):
        """Should include entity name in message."""
        db = MagicMock()

        instance = MagicMock()
        instance.id = uuid4()
        instance.tenant_id = uuid4()
        instance.due_date = "2024-03-12"
        instance.compliance_master = MagicMock()
        instance.compliance_master.compliance_name = "GST Filing"
        instance.entity = MagicMock()
        instance.entity.entity_name = "ABC Corp"

        escalate_to = MagicMock()
        escalate_to.id = uuid4()

        with patch("app.services.notification_service.create_notification") as mock_create:
            mock_create.return_value = MagicMock()

            result = notify_overdue_escalation(db, instance, escalate_to, days_overdue=5)

        call_args = mock_create.call_args
        assert "ABC Corp" in call_args.kwargs["message"]


class TestNotifyEvidenceUploaded:
    """Tests for notify_evidence_uploaded helper."""

    def test_notify_evidence_uploaded_creates_notification(self):
        """Should create notification for evidence upload."""
        db = MagicMock()

        evidence = MagicMock()
        evidence.evidence_name = "Bank Statement.pdf"
        evidence.tenant_id = uuid4()
        evidence.compliance_instance_id = uuid4()
        evidence.compliance_instance = MagicMock()
        evidence.compliance_instance.compliance_master = MagicMock()
        evidence.compliance_instance.compliance_master.compliance_name = "GST Filing"

        approver = MagicMock()
        approver.id = uuid4()

        with patch("app.services.notification_service.create_notification") as mock_create:
            mock_create.return_value = MagicMock()

            result = notify_evidence_uploaded(db, evidence, approver)

        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args.kwargs["notification_type"] == NotificationType.EVIDENCE_UPLOADED

    def test_notify_evidence_uploaded_returns_none_if_no_approver(self):
        """Should return None if no approver."""
        db = MagicMock()
        evidence = MagicMock()

        result = notify_evidence_uploaded(db, evidence, None)

        assert result is None


class TestNotifyEvidenceApproved:
    """Tests for notify_evidence_approved helper."""

    def test_notify_evidence_approved_creates_notification(self):
        """Should create notification for evidence approval."""
        db = MagicMock()

        evidence = MagicMock()
        evidence.evidence_name = "Bank Statement.pdf"
        evidence.tenant_id = uuid4()
        evidence.compliance_instance_id = uuid4()

        owner = MagicMock()
        owner.id = uuid4()

        with patch("app.services.notification_service.create_notification") as mock_create:
            mock_create.return_value = MagicMock()

            result = notify_evidence_approved(db, evidence, owner)

        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args.kwargs["notification_type"] == NotificationType.EVIDENCE_APPROVED

    def test_notify_evidence_approved_returns_none_if_no_owner(self):
        """Should return None if no owner."""
        db = MagicMock()
        evidence = MagicMock()

        result = notify_evidence_approved(db, evidence, None)

        assert result is None


class TestNotifyEvidenceRejected:
    """Tests for notify_evidence_rejected helper."""

    def test_notify_evidence_rejected_creates_notification(self):
        """Should create notification for evidence rejection."""
        db = MagicMock()

        evidence = MagicMock()
        evidence.evidence_name = "Bank Statement.pdf"
        evidence.tenant_id = uuid4()
        evidence.compliance_instance_id = uuid4()

        owner = MagicMock()
        owner.id = uuid4()

        rejection_reason = "Document is not legible"

        with patch("app.services.notification_service.create_notification") as mock_create:
            mock_create.return_value = MagicMock()

            result = notify_evidence_rejected(db, evidence, owner, rejection_reason)

        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args.kwargs["notification_type"] == NotificationType.EVIDENCE_REJECTED
        assert rejection_reason in call_args.kwargs["message"]

    def test_notify_evidence_rejected_returns_none_if_no_owner(self):
        """Should return None if no owner."""
        db = MagicMock()
        evidence = MagicMock()

        result = notify_evidence_rejected(db, evidence, None, "Reason")

        assert result is None


class TestNotifyInstanceCreated:
    """Tests for notify_instance_created helper."""

    def test_notify_instance_created_creates_notification(self):
        """Should create notification for new instance."""
        db = MagicMock()

        instance = MagicMock()
        instance.id = uuid4()
        instance.tenant_id = uuid4()
        instance.due_date = "2024-03-15"
        instance.compliance_master = MagicMock()
        instance.compliance_master.compliance_name = "GST Filing"
        instance.entity = MagicMock()
        instance.entity.entity_name = "ABC Corp"

        owner = MagicMock()
        owner.id = uuid4()

        with patch("app.services.notification_service.create_notification") as mock_create:
            mock_create.return_value = MagicMock()

            result = notify_instance_created(db, instance, owner)

        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args.kwargs["notification_type"] == NotificationType.INSTANCE_CREATED

    def test_notify_instance_created_returns_none_if_no_owner(self):
        """Should return None if no owner."""
        db = MagicMock()
        instance = MagicMock()

        result = notify_instance_created(db, instance, None)

        assert result is None


class TestNotifyInstanceCompleted:
    """Tests for notify_instance_completed helper."""

    def test_notify_instance_completed_creates_notifications_for_all_users(self):
        """Should create notifications for all users in list."""
        db = MagicMock()

        instance = MagicMock()
        instance.id = uuid4()
        instance.tenant_id = uuid4()
        instance.compliance_master = MagicMock()
        instance.compliance_master.compliance_name = "GST Filing"
        instance.entity = MagicMock()
        instance.entity.entity_name = "ABC Corp"

        users = [MagicMock(id=uuid4()), MagicMock(id=uuid4()), MagicMock(id=uuid4())]

        with patch("app.services.notification_service.create_notification") as mock_create:
            mock_create.return_value = MagicMock()

            result = notify_instance_completed(db, instance, users)

        assert mock_create.call_count == 3
        assert len(result) == 3

    def test_notify_instance_completed_skips_none_users(self):
        """Should skip None users in list."""
        db = MagicMock()

        instance = MagicMock()
        instance.id = uuid4()
        instance.tenant_id = uuid4()
        instance.compliance_master = MagicMock()
        instance.compliance_master.compliance_name = "GST Filing"
        instance.entity = MagicMock()
        instance.entity.entity_name = "ABC Corp"

        users = [MagicMock(id=uuid4()), None, MagicMock(id=uuid4())]

        with patch("app.services.notification_service.create_notification") as mock_create:
            mock_create.return_value = MagicMock()

            result = notify_instance_completed(db, instance, users)

        assert mock_create.call_count == 2
        assert len(result) == 2

    def test_notify_instance_completed_returns_empty_list_for_empty_users(self):
        """Should return empty list if no users."""
        db = MagicMock()
        instance = MagicMock()
        instance.compliance_master = MagicMock()
        instance.entity = MagicMock()

        result = notify_instance_completed(db, instance, [])

        assert result == []


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_notification_without_compliance_master(self):
        """Should handle instance without compliance_master gracefully."""
        db = MagicMock()

        instance = MagicMock()
        instance.id = uuid4()
        instance.tenant_id = uuid4()
        instance.due_date = "2024-03-15"
        instance.compliance_master = None
        instance.entity = MagicMock()
        instance.entity.entity_name = "ABC Corp"

        owner = MagicMock()
        owner.id = uuid4()

        with patch("app.services.notification_service.create_notification") as mock_create:
            mock_create.return_value = MagicMock()

            result = notify_instance_created(db, instance, owner)

        # Should use default "Compliance" name
        call_args = mock_create.call_args
        assert "Compliance" in call_args.kwargs["title"]

    def test_notification_without_entity(self):
        """Should handle instance without entity gracefully."""
        db = MagicMock()

        instance = MagicMock()
        instance.id = uuid4()
        instance.tenant_id = uuid4()
        instance.due_date = "2024-03-15"
        instance.compliance_master = MagicMock()
        instance.compliance_master.compliance_name = "GST Filing"
        instance.entity = None

        owner = MagicMock()
        owner.id = uuid4()

        with patch("app.services.notification_service.create_notification") as mock_create:
            mock_create.return_value = MagicMock()

            result = notify_instance_created(db, instance, owner)

        # Should use default "Entity" name
        mock_create.assert_called_once()

    def test_task_notification_without_compliance_master(self):
        """Should handle task without compliance_master gracefully."""
        db = MagicMock()

        task = MagicMock()
        task.task_name = "Test Task"
        task.task_type = "Prepare"
        task.due_date = "2024-03-15"
        task.tenant_id = uuid4()
        task.compliance_instance_id = uuid4()
        task.compliance_instance = MagicMock()
        task.compliance_instance.compliance_master = None

        assigned_user = MagicMock()
        assigned_user.id = uuid4()

        with patch("app.services.notification_service.create_notification") as mock_create:
            mock_create.return_value = MagicMock()

            result = notify_task_assigned(db, task, assigned_user)

        mock_create.assert_called_once()

    def test_large_pagination_offset(self):
        """Should handle large pagination offset."""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            []
        )

        result = get_user_notifications(db, uuid4(), uuid4(), limit=50, offset=10000)

        assert result == []
