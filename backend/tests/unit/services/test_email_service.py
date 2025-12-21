"""
Unit tests for email service.

Tests cover:
- Email sending with SendGrid
- Template rendering
- Dev mode (email disabled)
- Error handling and retries
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from uuid import uuid4


class TestEmailService:
    """Tests for EmailService class."""

    @patch("app.services.email_service.settings")
    def test_email_disabled_in_dev_mode(self, mock_settings):
        """Test emails are not sent when EMAIL_ENABLED is False."""
        mock_settings.EMAIL_ENABLED = False
        mock_settings.SENDGRID_API_KEY = "test_key"  # pragma: allowlist secret
        mock_settings.EMAIL_FROM_ADDRESS = "noreply@test.com"
        mock_settings.EMAIL_FROM_NAME = "Test"

        from app.services.email_service import EmailService

        service = EmailService()

        result = service.send_email(
            to_email="user@example.com",
            subject="Test Subject",
            template_name="reminder_t3.html",
            context={"user_name": "Test User"},
        )

        # Should return True (logged only) without actually sending
        assert result is True
        assert service.client is None  # No SendGrid client initialized

    @patch("app.services.email_service.SendGridAPIClient")
    @patch("app.services.email_service.settings")
    def test_send_email_success(self, mock_settings, mock_sg_client):
        """Test successful email sending via SendGrid."""
        mock_settings.EMAIL_ENABLED = True
        mock_settings.SENDGRID_API_KEY = "SG.test_api_key"  # pragma: allowlist secret
        mock_settings.EMAIL_FROM_ADDRESS = "noreply@complianceos.com"
        mock_settings.EMAIL_FROM_NAME = "Compliance OS"
        mock_settings.CORS_ORIGINS = ["http://localhost:3000"]

        # Mock SendGrid response
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_sg_instance = MagicMock()
        mock_sg_instance.send.return_value = mock_response
        mock_sg_client.return_value = mock_sg_instance

        from app.services.email_service import EmailService

        service = EmailService()

        result = service.send_email(
            to_email="user@example.com",
            subject="Test Subject",
            template_name="reminder_t3.html",
            context={
                "user_name": "Test User",
                "compliance_name": "GST Return",
                "entity_name": "Test Entity",
                "due_date": "December 25, 2025",
                "days_until_due": 3,
                "dashboard_url": "http://localhost:3000/dashboard",
            },
        )

        assert result is True
        mock_sg_instance.send.assert_called_once()

    @patch("app.services.email_service.SendGridAPIClient")
    @patch("app.services.email_service.settings")
    def test_handles_sendgrid_error(self, mock_settings, mock_sg_client):
        """Test error handling when SendGrid fails."""
        mock_settings.EMAIL_ENABLED = True
        mock_settings.SENDGRID_API_KEY = "SG.test_api_key"  # pragma: allowlist secret
        mock_settings.EMAIL_FROM_ADDRESS = "noreply@complianceos.com"
        mock_settings.EMAIL_FROM_NAME = "Compliance OS"

        # Mock SendGrid exception
        mock_sg_instance = MagicMock()
        mock_sg_instance.send.side_effect = Exception("SendGrid API Error")
        mock_sg_client.return_value = mock_sg_instance

        from app.services.email_service import EmailService

        service = EmailService()

        result = service.send_email(
            to_email="user@example.com",
            subject="Test Subject",
            template_name="reminder_t3.html",
            context={"user_name": "Test"},
        )

        assert result is False

    @patch("app.services.email_service.SendGridAPIClient")
    @patch("app.services.email_service.settings")
    def test_handles_non_success_status_code(self, mock_settings, mock_sg_client):
        """Test handling of non-200 status codes from SendGrid."""
        mock_settings.EMAIL_ENABLED = True
        mock_settings.SENDGRID_API_KEY = "SG.test_api_key"  # pragma: allowlist secret
        mock_settings.EMAIL_FROM_ADDRESS = "noreply@complianceos.com"
        mock_settings.EMAIL_FROM_NAME = "Compliance OS"

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.body = b"Bad Request"
        mock_sg_instance = MagicMock()
        mock_sg_instance.send.return_value = mock_response
        mock_sg_client.return_value = mock_sg_instance

        from app.services.email_service import EmailService

        service = EmailService()

        result = service.send_email(
            to_email="user@example.com",
            subject="Test Subject",
            template_name="reminder_t3.html",
            context={"user_name": "Test"},
        )

        assert result is False


class TestTemplateRendering:
    """Tests for email template rendering."""

    @patch("app.services.email_service.settings")
    def test_template_renders_with_context(self, mock_settings):
        """Test Jinja2 template rendering with context variables."""
        mock_settings.EMAIL_ENABLED = False

        from app.services.email_service import EmailService

        service = EmailService()

        context = {
            "user_name": "John Doe",
            "compliance_name": "GST Return Filing",
            "entity_name": "ABC Pvt Ltd",
            "due_date": "December 28, 2025",
            "days_until_due": 3,
            "dashboard_url": "http://localhost:3000/compliance",
        }

        html = service._render_template("reminder_t3.html", context)

        assert "John Doe" in html
        assert "GST Return Filing" in html
        assert "ABC Pvt Ltd" in html
        assert "December 28, 2025" in html

    @patch("app.services.email_service.settings")
    def test_template_not_found_raises_error(self, mock_settings):
        """Test error when template doesn't exist."""
        mock_settings.EMAIL_ENABLED = False

        from app.services.email_service import EmailService

        service = EmailService()

        with pytest.raises(Exception):
            service._render_template("nonexistent_template.html", {})


class TestEmailHelperFunctions:
    """Tests for email helper functions."""

    @patch("app.services.email_service.get_email_service")
    def test_send_reminder_email(self, mock_get_service):
        """Test send_reminder_email helper function."""
        from app.services.email_service import send_reminder_email
        from app.models import User, ComplianceInstance, ComplianceMaster, Entity

        mock_service = MagicMock()
        mock_service.send_email.return_value = True
        mock_get_service.return_value = mock_service

        # Create mock objects
        user = MagicMock(spec=User)
        user.email = "user@example.com"
        user.full_name = "Test User"

        master = MagicMock(spec=ComplianceMaster)
        master.compliance_name = "GST Return"

        entity = MagicMock(spec=Entity)
        entity.entity_name = "Test Entity"

        instance = MagicMock(spec=ComplianceInstance)
        instance.id = uuid4()
        instance.compliance_master = master
        instance.entity = entity
        instance.due_date = date.today() + timedelta(days=3)
        instance.period = "Dec-2025"

        result = send_reminder_email(user, instance, "t3")

        assert result is True
        mock_service.send_email.assert_called_once()
        call_args = mock_service.send_email.call_args
        assert call_args.kwargs["to_email"] == "user@example.com"
        assert "reminder" in call_args.kwargs["subject"].lower()
        assert call_args.kwargs["template_name"] == "reminder_t3.html"

    @patch("app.services.email_service.get_email_service")
    def test_send_escalation_email(self, mock_get_service):
        """Test send_escalation_email helper function."""
        from app.services.email_service import send_escalation_email
        from app.models import User, ComplianceInstance, ComplianceMaster, Entity

        mock_service = MagicMock()
        mock_service.send_email.return_value = True
        mock_get_service.return_value = mock_service

        user = MagicMock(spec=User)
        user.email = "cfo@example.com"
        user.full_name = "CFO"

        master = MagicMock(spec=ComplianceMaster)
        master.compliance_name = "GST Return"

        entity = MagicMock(spec=Entity)
        entity.entity_name = "Test Entity"

        instance = MagicMock(spec=ComplianceInstance)
        instance.id = uuid4()
        instance.compliance_master = master
        instance.entity = entity
        instance.due_date = date.today() - timedelta(days=5)
        instance.period = "Dec-2025"

        result = send_escalation_email(user, instance, days_overdue=5)

        assert result is True
        call_args = mock_service.send_email.call_args
        assert "ESCALATION" in call_args.kwargs["subject"]
        assert "5 days" in call_args.kwargs["subject"]
        assert call_args.kwargs["template_name"] == "escalation.html"

    @patch("app.services.email_service.get_email_service")
    def test_send_task_assigned_email(self, mock_get_service):
        """Test send_task_assigned_email helper function."""
        from app.services.email_service import send_task_assigned_email
        from app.models import User, WorkflowTask, ComplianceInstance, ComplianceMaster, Entity

        mock_service = MagicMock()
        mock_service.send_email.return_value = True
        mock_get_service.return_value = mock_service

        user = MagicMock(spec=User)
        user.email = "user@example.com"
        user.full_name = "Test User"

        master = MagicMock(spec=ComplianceMaster)
        master.compliance_name = "GST Return"

        entity = MagicMock(spec=Entity)
        entity.entity_name = "Test Entity"

        instance = MagicMock(spec=ComplianceInstance)
        instance.compliance_master = master
        instance.entity = entity

        task = MagicMock(spec=WorkflowTask)
        task.id = uuid4()
        task.task_name = "Upload GST Return"
        task.task_description = "Upload the GST return document"
        task.due_date = date.today() + timedelta(days=7)
        task.compliance_instance = instance
        task.compliance_instance_id = uuid4()

        result = send_task_assigned_email(user, task)

        assert result is True
        call_args = mock_service.send_email.call_args
        assert "New Task Assigned" in call_args.kwargs["subject"]
        assert call_args.kwargs["template_name"] == "task_assigned.html"

    @patch("app.services.email_service.get_email_service")
    def test_send_evidence_status_email_approved(self, mock_get_service):
        """Test send_evidence_status_email for approval."""
        from app.services.email_service import send_evidence_status_email
        from app.models import User, Evidence, ComplianceInstance, ComplianceMaster

        mock_service = MagicMock()
        mock_service.send_email.return_value = True
        mock_get_service.return_value = mock_service

        user = MagicMock(spec=User)
        user.email = "user@example.com"
        user.full_name = "Test User"

        master = MagicMock(spec=ComplianceMaster)
        master.compliance_name = "GST Return"

        instance = MagicMock(spec=ComplianceInstance)
        instance.compliance_master = master

        evidence = MagicMock(spec=Evidence)
        evidence.id = uuid4()
        evidence.evidence_name = "GST_Return_Dec2025.pdf"
        evidence.compliance_instance = instance
        evidence.compliance_instance_id = uuid4()

        result = send_evidence_status_email(user, evidence, approved=True)

        assert result is True
        call_args = mock_service.send_email.call_args
        assert "Approved" in call_args.kwargs["subject"]
        assert call_args.kwargs["template_name"] == "evidence_approved.html"

    @patch("app.services.email_service.get_email_service")
    def test_send_evidence_status_email_rejected(self, mock_get_service):
        """Test send_evidence_status_email for rejection."""
        from app.services.email_service import send_evidence_status_email
        from app.models import User, Evidence, ComplianceInstance, ComplianceMaster

        mock_service = MagicMock()
        mock_service.send_email.return_value = True
        mock_get_service.return_value = mock_service

        user = MagicMock(spec=User)
        user.email = "user@example.com"
        user.full_name = "Test User"

        master = MagicMock(spec=ComplianceMaster)
        master.compliance_name = "GST Return"

        instance = MagicMock(spec=ComplianceInstance)
        instance.compliance_master = master

        evidence = MagicMock(spec=Evidence)
        evidence.id = uuid4()
        evidence.evidence_name = "GST_Return_Dec2025.pdf"
        evidence.compliance_instance = instance
        evidence.compliance_instance_id = uuid4()

        result = send_evidence_status_email(user, evidence, approved=False, rejection_reason="Missing signatures")

        assert result is True
        call_args = mock_service.send_email.call_args
        assert "Rejected" in call_args.kwargs["subject"]
        assert call_args.kwargs["template_name"] == "evidence_rejected.html"
        assert call_args.kwargs["context"]["rejection_reason"] == "Missing signatures"


class TestGetEmailService:
    """Tests for get_email_service singleton."""

    def test_returns_singleton_instance(self):
        """Test that get_email_service returns same instance."""
        from app.services.email_service import get_email_service
        import app.services.email_service as email_module

        # Reset singleton
        email_module._email_service = None

        service1 = get_email_service()
        service2 = get_email_service()

        assert service1 is service2

    def test_creates_new_instance_when_none(self):
        """Test that a new instance is created when none exists."""
        import app.services.email_service as email_module

        # Reset singleton
        email_module._email_service = None

        service = email_module.get_email_service()

        assert service is not None
        assert isinstance(service, email_module.EmailService)
