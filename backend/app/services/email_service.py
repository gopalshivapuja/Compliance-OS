"""
Email Service
Handles email sending via SendGrid for notifications, reminders, and escalations.
"""

import logging
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from app.core.config import settings
from app.models import User, ComplianceInstance, WorkflowTask, Evidence

logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "email"

# Initialize Jinja2 environment for templates
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


class EmailService:
    """Service for sending emails via SendGrid."""

    def __init__(self):
        """Initialize email service with SendGrid client."""
        self.enabled = settings.EMAIL_ENABLED
        self.from_email = settings.EMAIL_FROM_ADDRESS
        self.from_name = settings.EMAIL_FROM_NAME
        self.api_key = settings.SENDGRID_API_KEY

        if self.enabled and self.api_key:
            self.client = SendGridAPIClient(self.api_key)
        else:
            self.client = None

    def _render_template(self, template_name: str, context: dict) -> str:
        """
        Render an email template with the given context.

        Args:
            template_name: Name of the template file (e.g., 'reminder_t3.html')
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered HTML string
        """
        try:
            template = jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise

    def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict,
        to_name: Optional[str] = None,
    ) -> bool:
        """
        Send an email using SendGrid.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            template_name: Name of the HTML template to use
            context: Dictionary of variables for template rendering
            to_name: Optional recipient name

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"Email disabled. Would send to {to_email}: {subject}")
            logger.debug(f"Email context: {context}")
            return True

        if not self.client:
            logger.warning("SendGrid client not initialized. Check API key.")
            return False

        try:
            # Render the template
            html_content = self._render_template(template_name, context)

            # Build the email
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email, to_name),
                subject=subject,
                html_content=Content("text/html", html_content),
            )

            # Send via SendGrid
            response = self.client.send(message)

            if response.status_code in (200, 201, 202):
                logger.info(f"Email sent successfully to {to_email}: {subject}")
                return True
            else:
                logger.error(f"SendGrid returned status {response.status_code}: {response.body}")
                return False

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get the singleton EmailService instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def send_reminder_email(
    user: User,
    instance: ComplianceInstance,
    reminder_type: str,
) -> bool:
    """
    Send a compliance reminder email.

    Args:
        user: The user to notify
        instance: The compliance instance
        reminder_type: Type of reminder ('t3', 'due', 'overdue')

    Returns:
        True if email sent successfully
    """
    service = get_email_service()

    # Get compliance and entity names
    compliance_name = instance.compliance_master.compliance_name if instance.compliance_master else "Compliance"
    entity_name = instance.entity.entity_name if instance.entity else "Entity"

    # Choose template based on reminder type
    template_map = {
        "t3": "reminder_t3.html",
        "due": "reminder_due.html",
        "overdue": "escalation.html",
    }
    template_name = template_map.get(reminder_type, "reminder_due.html")

    # Build subject
    subject_map = {
        "t3": f"Reminder: {compliance_name} due in 3 days",
        "due": f"Action Required: {compliance_name} is due today",
        "overdue": f"URGENT: {compliance_name} is overdue",
    }
    subject = subject_map.get(reminder_type, f"Reminder: {compliance_name}")

    context = {
        "user_name": user.full_name or user.email,
        "compliance_name": compliance_name,
        "entity_name": entity_name,
        "due_date": instance.due_date.strftime("%B %d, %Y") if instance.due_date else "N/A",
        "period": instance.period,
        "instance_id": str(instance.id),
        "dashboard_url": f"{settings.CORS_ORIGINS[0]}/compliance-instances/{instance.id}",
        "reminder_type": reminder_type,
    }

    return service.send_email(
        to_email=user.email,
        subject=subject,
        template_name=template_name,
        context=context,
        to_name=user.full_name,
    )


def send_escalation_email(
    user: User,
    instance: ComplianceInstance,
    days_overdue: int,
) -> bool:
    """
    Send an escalation email for overdue compliance.

    Args:
        user: The CFO/Admin to escalate to
        instance: The overdue compliance instance
        days_overdue: Number of days past due

    Returns:
        True if email sent successfully
    """
    service = get_email_service()

    compliance_name = instance.compliance_master.compliance_name if instance.compliance_master else "Compliance"
    entity_name = instance.entity.entity_name if instance.entity else "Entity"

    context = {
        "user_name": user.full_name or user.email,
        "compliance_name": compliance_name,
        "entity_name": entity_name,
        "due_date": instance.due_date.strftime("%B %d, %Y") if instance.due_date else "N/A",
        "days_overdue": days_overdue,
        "period": instance.period,
        "instance_id": str(instance.id),
        "dashboard_url": f"{settings.CORS_ORIGINS[0]}/compliance-instances/{instance.id}",
    }

    return service.send_email(
        to_email=user.email,
        subject=f"ESCALATION: {compliance_name} overdue by {days_overdue} days",
        template_name="escalation.html",
        context=context,
        to_name=user.full_name,
    )


def send_task_assigned_email(
    user: User,
    task: WorkflowTask,
) -> bool:
    """
    Send email notification when a task is assigned.

    Args:
        user: The user assigned to the task
        task: The workflow task

    Returns:
        True if email sent successfully
    """
    service = get_email_service()

    # Get compliance info from instance
    instance = task.compliance_instance
    compliance_name = (
        instance.compliance_master.compliance_name if instance and instance.compliance_master else "Compliance"
    )
    entity_name = instance.entity.entity_name if instance and instance.entity else "Entity"

    context = {
        "user_name": user.full_name or user.email,
        "task_name": task.task_name,
        "task_description": task.task_description or "",
        "compliance_name": compliance_name,
        "entity_name": entity_name,
        "due_date": task.due_date.strftime("%B %d, %Y") if task.due_date else "N/A",
        "task_id": str(task.id),
        "instance_id": str(task.compliance_instance_id) if task.compliance_instance_id else "",
        "dashboard_url": f"{settings.CORS_ORIGINS[0]}/workflow-tasks/{task.id}",
    }

    return service.send_email(
        to_email=user.email,
        subject=f"New Task Assigned: {task.task_name}",
        template_name="task_assigned.html",
        context=context,
        to_name=user.full_name,
    )


def send_evidence_status_email(
    user: User,
    evidence: Evidence,
    approved: bool,
    rejection_reason: Optional[str] = None,
) -> bool:
    """
    Send email notification when evidence is approved or rejected.

    Args:
        user: The user who uploaded the evidence
        evidence: The evidence record
        approved: True if approved, False if rejected
        rejection_reason: Reason for rejection (if rejected)

    Returns:
        True if email sent successfully
    """
    service = get_email_service()

    # Get compliance info
    instance = evidence.compliance_instance
    compliance_name = (
        instance.compliance_master.compliance_name if instance and instance.compliance_master else "Compliance"
    )

    template_name = "evidence_approved.html" if approved else "evidence_rejected.html"
    subject = (
        f"Evidence Approved: {evidence.evidence_name}" if approved else f"Evidence Rejected: {evidence.evidence_name}"
    )

    context = {
        "user_name": user.full_name or user.email,
        "evidence_name": evidence.evidence_name,
        "compliance_name": compliance_name,
        "approved": approved,
        "rejection_reason": rejection_reason or "",
        "evidence_id": str(evidence.id),
        "instance_id": str(evidence.compliance_instance_id) if evidence.compliance_instance_id else "",
        "dashboard_url": f"{settings.CORS_ORIGINS[0]}/evidence/{evidence.id}",
    }

    return service.send_email(
        to_email=user.email,
        subject=subject,
        template_name=template_name,
        context=context,
        to_name=user.full_name,
    )


def send_task_reminder_email(
    user: User,
    task: WorkflowTask,
    days_until_due: int,
) -> bool:
    """
    Send email reminder for upcoming task.

    Args:
        user: The user assigned to the task
        task: The workflow task
        days_until_due: Number of days until due

    Returns:
        True if email sent successfully
    """
    service = get_email_service()

    context = {
        "user_name": user.full_name or user.email,
        "task_name": task.task_name,
        "task_description": task.task_description or "",
        "due_date": task.due_date.strftime("%B %d, %Y") if task.due_date else "N/A",
        "days_until_due": days_until_due,
        "task_id": str(task.id),
        "dashboard_url": f"{settings.CORS_ORIGINS[0]}/workflow-tasks/{task.id}",
    }

    subject = (
        f"Task Due Today: {task.task_name}"
        if days_until_due == 0
        else f"Task Reminder: {task.task_name} due in {days_until_due} days"
    )

    return service.send_email(
        to_email=user.email,
        subject=subject,
        template_name="reminder_due.html",
        context=context,
        to_name=user.full_name,
    )
