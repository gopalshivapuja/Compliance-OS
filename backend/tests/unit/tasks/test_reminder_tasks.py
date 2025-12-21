"""
Unit tests for reminder background tasks.

Tests cover:
- T-3 day reminders
- Due date reminders
- Overdue escalation
- Task reminders
- Notification cleanup
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock, call
from uuid import uuid4

from app.models import (
    Tenant,
    ComplianceInstance,
    ComplianceMaster,
    User,
    WorkflowTask,
    Role,
)


class TestSendT3Reminders:
    """Tests for send_t3_reminders task."""

    @patch("app.tasks.reminder_tasks.send_reminder_email_task")
    @patch("app.tasks.reminder_tasks.SessionLocal")
    @patch("app.tasks.reminder_tasks.notify_reminder_t3")
    @patch("app.tasks.reminder_tasks.get_instance_owner")
    def test_sends_reminder_3_days_before_due(self, mock_get_owner, mock_notify, mock_session, mock_email_task):
        """Test T-3 reminders are sent for instances due in 3 days."""
        from app.tasks.reminder_tasks import send_t3_reminders

        mock_db = MagicMock()

        # Create instance due in 3 days
        instance = MagicMock(spec=ComplianceInstance)
        instance.id = uuid4()
        instance.due_date = date.today() + timedelta(days=3)
        instance.status = "In Progress"

        owner = MagicMock(spec=User)
        owner.id = uuid4()
        owner.email = "owner@example.com"

        mock_db.query.return_value.filter.return_value.all.return_value = [instance]
        mock_session.return_value = mock_db
        mock_get_owner.return_value = owner
        mock_notify.return_value = MagicMock()  # Notification created

        result = send_t3_reminders()

        assert result["status"] == "success"
        assert result["reminders_sent"] == 1
        mock_notify.assert_called_once_with(mock_db, instance, owner)
        mock_email_task.delay.assert_called_once()

    @patch("app.tasks.reminder_tasks.SessionLocal")
    @patch("app.tasks.reminder_tasks.get_instance_owner")
    def test_skips_completed_instances(self, mock_get_owner, mock_session):
        """Test completed instances are not sent reminders."""
        from app.tasks.reminder_tasks import send_t3_reminders

        mock_db = MagicMock()
        # Query filters out completed, so returns empty
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_session.return_value = mock_db

        result = send_t3_reminders()

        assert result["status"] == "success"
        assert result["reminders_sent"] == 0
        mock_get_owner.assert_not_called()

    @patch("app.tasks.reminder_tasks.SessionLocal")
    @patch("app.tasks.reminder_tasks.notify_reminder_t3")
    @patch("app.tasks.reminder_tasks.get_instance_owner")
    def test_handles_missing_owner(self, mock_get_owner, mock_notify, mock_session):
        """Test task handles instances without owner."""
        from app.tasks.reminder_tasks import send_t3_reminders

        mock_db = MagicMock()

        instance = MagicMock(spec=ComplianceInstance)
        instance.id = uuid4()
        instance.due_date = date.today() + timedelta(days=3)

        mock_db.query.return_value.filter.return_value.all.return_value = [instance]
        mock_session.return_value = mock_db
        mock_get_owner.return_value = None  # No owner found

        result = send_t3_reminders()

        assert result["status"] == "success"
        assert result["reminders_sent"] == 0
        mock_notify.assert_not_called()


class TestSendDueDateReminders:
    """Tests for send_due_date_reminders task."""

    @patch("app.tasks.reminder_tasks.send_reminder_email_task")
    @patch("app.tasks.reminder_tasks.SessionLocal")
    @patch("app.tasks.reminder_tasks.notify_reminder_due")
    @patch("app.tasks.reminder_tasks.get_instance_owner")
    def test_sends_reminder_on_due_date(self, mock_get_owner, mock_notify, mock_session, mock_email_task):
        """Test due date reminders are sent for instances due today."""
        from app.tasks.reminder_tasks import send_due_date_reminders

        mock_db = MagicMock()

        instance = MagicMock(spec=ComplianceInstance)
        instance.id = uuid4()
        instance.due_date = date.today()
        instance.status = "In Progress"

        owner = MagicMock(spec=User)
        owner.id = uuid4()
        owner.email = "owner@example.com"

        mock_db.query.return_value.filter.return_value.all.return_value = [instance]
        mock_session.return_value = mock_db
        mock_get_owner.return_value = owner
        mock_notify.return_value = MagicMock()

        result = send_due_date_reminders()

        assert result["status"] == "success"
        assert result["reminders_sent"] == 1
        mock_email_task.delay.assert_called_once_with(
            user_id=str(owner.id),
            instance_id=str(instance.id),
            reminder_type="due",
        )

    @patch("app.tasks.reminder_tasks.SessionLocal")
    @patch("app.tasks.reminder_tasks.notify_reminder_due")
    @patch("app.tasks.reminder_tasks.get_instance_owner")
    def test_handles_missing_owner(self, mock_get_owner, mock_notify, mock_session):
        """Test task continues when owner not found."""
        from app.tasks.reminder_tasks import send_due_date_reminders

        mock_db = MagicMock()

        instance = MagicMock(spec=ComplianceInstance)
        instance.id = uuid4()
        instance.due_date = date.today()

        mock_db.query.return_value.filter.return_value.all.return_value = [instance]
        mock_session.return_value = mock_db
        mock_get_owner.return_value = None

        result = send_due_date_reminders()

        assert result["status"] == "success"
        assert result["reminders_sent"] == 0


class TestEscalateOverdueItems:
    """Tests for escalate_overdue_items task."""

    @patch("app.tasks.reminder_tasks.send_escalation_email_task")
    @patch("app.tasks.reminder_tasks.SessionLocal")
    @patch("app.tasks.reminder_tasks.notify_overdue_escalation")
    @patch("app.tasks.reminder_tasks.get_escalation_user")
    def test_escalates_3_days_overdue(self, mock_get_escalation_user, mock_notify, mock_session, mock_email_task):
        """Test items overdue by 3+ days are escalated."""
        from app.tasks.reminder_tasks import escalate_overdue_items

        mock_db = MagicMock()

        instance = MagicMock(spec=ComplianceInstance)
        instance.id = uuid4()
        instance.tenant_id = uuid4()
        instance.due_date = date.today() - timedelta(days=5)
        instance.status = "In Progress"
        instance.metadata = None

        cfo = MagicMock(spec=User)
        cfo.id = uuid4()
        cfo.email = "cfo@example.com"

        mock_db.query.return_value.filter.return_value.all.return_value = [instance]
        mock_session.return_value = mock_db
        mock_get_escalation_user.return_value = cfo
        mock_notify.return_value = MagicMock()

        result = escalate_overdue_items()

        assert result["status"] == "success"
        assert result["escalations_sent"] == 1
        mock_email_task.delay.assert_called_once()

    @patch("app.tasks.reminder_tasks.SessionLocal")
    @patch("app.tasks.reminder_tasks.get_escalation_user")
    def test_prevents_duplicate_escalations(self, mock_get_escalation_user, mock_session):
        """Test already escalated items are not re-escalated."""
        from app.tasks.reminder_tasks import escalate_overdue_items

        mock_db = MagicMock()

        # Instance already escalated
        instance = MagicMock(spec=ComplianceInstance)
        instance.id = uuid4()
        instance.tenant_id = uuid4()
        instance.due_date = date.today() - timedelta(days=5)
        instance.metadata = {"escalated": True}

        mock_db.query.return_value.filter.return_value.all.return_value = [instance]
        mock_session.return_value = mock_db

        result = escalate_overdue_items()

        assert result["status"] == "success"
        assert result["escalations_sent"] == 0
        mock_get_escalation_user.assert_not_called()

    @patch("app.tasks.reminder_tasks.SessionLocal")
    @patch("app.tasks.reminder_tasks.notify_overdue_escalation")
    @patch("app.tasks.reminder_tasks.get_escalation_user")
    def test_finds_cfo_for_escalation(self, mock_get_escalation_user, mock_notify, mock_session):
        """Test escalation user lookup is done per tenant."""
        from app.tasks.reminder_tasks import escalate_overdue_items

        mock_db = MagicMock()

        tenant1_id = uuid4()
        tenant2_id = uuid4()

        instance1 = MagicMock(spec=ComplianceInstance)
        instance1.id = uuid4()
        instance1.tenant_id = tenant1_id
        instance1.due_date = date.today() - timedelta(days=4)
        instance1.metadata = None

        instance2 = MagicMock(spec=ComplianceInstance)
        instance2.id = uuid4()
        instance2.tenant_id = tenant2_id
        instance2.due_date = date.today() - timedelta(days=4)
        instance2.metadata = None

        mock_db.query.return_value.filter.return_value.all.return_value = [instance1, instance2]
        mock_session.return_value = mock_db

        cfo1 = MagicMock(spec=User)
        cfo1.id = uuid4()
        cfo2 = MagicMock(spec=User)
        cfo2.id = uuid4()

        mock_get_escalation_user.side_effect = [cfo1, cfo2]
        mock_notify.return_value = MagicMock()

        result = escalate_overdue_items()

        assert mock_get_escalation_user.call_count == 2


class TestSendTaskReminders:
    """Tests for send_task_reminders task."""

    @patch("app.tasks.reminder_tasks.send_task_reminder_email_task")
    @patch("app.services.notification_service.create_notification")
    @patch("app.tasks.reminder_tasks.SessionLocal")
    def test_sends_reminder_2_days_before_task_due(self, mock_session, mock_create_notif, mock_email_task):
        """Test task reminders are sent for tasks due within 2 days."""
        from app.tasks.reminder_tasks import send_task_reminders

        mock_db = MagicMock()

        task = MagicMock(spec=WorkflowTask)
        task.id = uuid4()
        task.tenant_id = uuid4()
        task.compliance_instance_id = uuid4()
        task.task_name = "Upload GST Return"
        task.due_date = date.today() + timedelta(days=2)
        task.status = "Pending"
        task.assigned_to_user_id = uuid4()

        user = MagicMock(spec=User)
        user.id = task.assigned_to_user_id

        # Setup query mocks
        mock_db.query.return_value.filter.return_value.all.return_value = [task]
        mock_db.query.return_value.filter.return_value.first.return_value = user
        mock_session.return_value = mock_db
        mock_create_notif.return_value = MagicMock()

        result = send_task_reminders()

        assert result["status"] == "success"
        assert result["reminders_sent"] == 1
        mock_email_task.delay.assert_called_once()

    @patch("app.tasks.reminder_tasks.SessionLocal")
    def test_skips_completed_tasks(self, mock_session):
        """Test completed tasks are not reminded."""
        from app.tasks.reminder_tasks import send_task_reminders

        mock_db = MagicMock()
        # Query filters completed, returns empty
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_session.return_value = mock_db

        result = send_task_reminders()

        assert result["status"] == "success"
        assert result["reminders_sent"] == 0


class TestCleanupOldNotifications:
    """Tests for cleanup_old_notifications task."""

    @patch("app.services.notification_service.delete_old_notifications")
    @patch("app.tasks.reminder_tasks.SessionLocal")
    def test_deletes_notifications_older_than_90_days(self, mock_session, mock_delete_old):
        """Test old notifications are deleted for all tenants."""
        from app.tasks.reminder_tasks import cleanup_old_notifications

        mock_db = MagicMock()

        tenant1 = MagicMock(spec=Tenant)
        tenant1.id = uuid4()
        tenant2 = MagicMock(spec=Tenant)
        tenant2.id = uuid4()

        mock_db.query.return_value.filter.return_value.all.return_value = [tenant1, tenant2]
        mock_session.return_value = mock_db

        mock_delete_old.side_effect = [50, 30]  # Delete counts

        result = cleanup_old_notifications()

        assert result["status"] == "success"
        assert result["notifications_deleted"] == 80
        assert mock_delete_old.call_count == 2

    @patch("app.services.notification_service.delete_old_notifications")
    @patch("app.tasks.reminder_tasks.SessionLocal")
    def test_handles_empty_notifications(self, mock_session, mock_delete_old):
        """Test task handles case with no old notifications."""
        from app.tasks.reminder_tasks import cleanup_old_notifications

        mock_db = MagicMock()

        tenant = MagicMock(spec=Tenant)
        tenant.id = uuid4()

        mock_db.query.return_value.filter.return_value.all.return_value = [tenant]
        mock_session.return_value = mock_db
        mock_delete_old.return_value = 0

        result = cleanup_old_notifications()

        assert result["status"] == "success"
        assert result["notifications_deleted"] == 0


class TestGetInstanceOwner:
    """Tests for get_instance_owner helper function."""

    def test_finds_owner_by_role_and_entity_access(self, db_session, test_tenant):
        """Test owner is found by role code and entity access."""
        from app.tasks.reminder_tasks import get_instance_owner
        from app.models import Entity, ComplianceMaster, ComplianceInstance, Role, User
        from app.models.entity import entity_access
        from app.models.role import user_roles
        from app.core.security import get_password_hash

        # Create entity
        entity = Entity(
            tenant_id=test_tenant.id,
            entity_name="Test Entity",
            entity_code="ENT001",
            created_by=None,
        )
        db_session.add(entity)
        db_session.flush()

        # Create role
        role = Role(role_name="Tax Manager", role_code="TAX_MGR")
        db_session.add(role)
        db_session.flush()

        # Create user with role and entity access
        user = User(
            tenant_id=test_tenant.id,
            email="taxmgr@example.com",
            first_name="Tax",
            last_name="Manager",
            password_hash=get_password_hash("Test123!@#"),
            status="active",
        )
        db_session.add(user)
        db_session.flush()

        # Add role to user
        db_session.execute(user_roles.insert().values(user_id=user.id, role_id=role.id, tenant_id=test_tenant.id))
        # Add entity access
        db_session.execute(
            entity_access.insert().values(user_id=user.id, entity_id=entity.id, tenant_id=test_tenant.id)
        )
        db_session.flush()

        # Create compliance master with owner role
        master = ComplianceMaster(
            tenant_id=test_tenant.id,
            compliance_code="GST01",
            compliance_name="GST Return",
            category="GST",
            frequency="Monthly",
            owner_role_code="TAX_MGR",
            due_date_rule={"type": "monthly", "day": 11},
            created_by=user.id,
        )
        db_session.add(master)
        db_session.flush()

        # Create instance
        instance = ComplianceInstance(
            tenant_id=test_tenant.id,
            compliance_master_id=master.id,
            entity_id=entity.id,
            period_start=date.today(),
            period_end=date.today() + timedelta(days=30),
            due_date=date.today() + timedelta(days=10),
            status="Pending",
            rag_status="Green",
            created_by=user.id,
        )
        db_session.add(instance)
        db_session.commit()
        db_session.refresh(instance)

        # Test owner lookup
        owner = get_instance_owner(db_session, instance)

        assert owner is not None
        assert owner.id == user.id
        assert owner.email == "taxmgr@example.com"


class TestGetEscalationUser:
    """Tests for get_escalation_user helper function."""

    def test_finds_cfo_first(self, db_session, test_tenant):
        """Test CFO is preferred over Admin for escalation."""
        from app.tasks.reminder_tasks import get_escalation_user
        from app.models import Role, User
        from app.models.role import user_roles
        from app.core.security import get_password_hash

        # Create CFO role
        cfo_role = Role(role_name="CFO", role_code="CFO")
        db_session.add(cfo_role)

        # Create Admin role
        admin_role = Role(role_name="Admin", role_code="ADMIN")
        db_session.add(admin_role)
        db_session.flush()

        # Create CFO user
        cfo = User(
            tenant_id=test_tenant.id,
            email="cfo@example.com",
            first_name="Chief",
            last_name="Financial",
            password_hash=get_password_hash("Test123!@#"),
            status="active",
        )
        db_session.add(cfo)

        # Create Admin user
        admin = User(
            tenant_id=test_tenant.id,
            email="admin@example.com",
            first_name="System",
            last_name="Admin",
            password_hash=get_password_hash("Test123!@#"),
            status="active",
        )
        db_session.add(admin)
        db_session.flush()

        # Assign roles
        db_session.execute(user_roles.insert().values(user_id=cfo.id, role_id=cfo_role.id, tenant_id=test_tenant.id))
        db_session.execute(
            user_roles.insert().values(user_id=admin.id, role_id=admin_role.id, tenant_id=test_tenant.id)
        )
        db_session.commit()

        # Test - should find CFO first
        escalation_user = get_escalation_user(db_session, test_tenant.id)

        assert escalation_user is not None
        assert escalation_user.email == "cfo@example.com"

    def test_falls_back_to_admin(self, db_session, test_tenant):
        """Test Admin is used when no CFO exists."""
        from app.tasks.reminder_tasks import get_escalation_user
        from app.models import Role, User
        from app.models.role import user_roles
        from app.core.security import get_password_hash

        # Create only Admin role
        admin_role = Role(role_name="Admin", role_code="ADMIN")
        db_session.add(admin_role)
        db_session.flush()

        # Create Admin user
        admin = User(
            tenant_id=test_tenant.id,
            email="admin@example.com",
            first_name="System",
            last_name="Admin",
            password_hash=get_password_hash("Test123!@#"),
            status="active",
        )
        db_session.add(admin)
        db_session.flush()

        db_session.execute(
            user_roles.insert().values(user_id=admin.id, role_id=admin_role.id, tenant_id=test_tenant.id)
        )
        db_session.commit()

        # Test - should find Admin since no CFO
        escalation_user = get_escalation_user(db_session, test_tenant.id)

        assert escalation_user is not None
        assert escalation_user.email == "admin@example.com"
