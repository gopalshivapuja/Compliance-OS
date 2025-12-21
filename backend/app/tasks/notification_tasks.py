"""
Background tasks for email notifications.
Handles async email sending via Celery with retry logic.
"""

import logging
from typing import Optional
from uuid import UUID

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.models import User, ComplianceInstance, WorkflowTask, Evidence
from app.services.email_service import (
    get_email_service,
    send_reminder_email,
    send_escalation_email,
    send_task_assigned_email,
    send_evidence_status_email,
    send_task_reminder_email,
)

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(
    self,
    to_email: str,
    subject: str,
    template_name: str,
    context: dict,
    to_name: Optional[str] = None,
):
    """
    Generic email sending task with retry logic.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        template_name: Name of the HTML template to use
        context: Dictionary of variables for template rendering
        to_name: Optional recipient name

    Returns:
        dict: Result with status and details
    """
    logger.info(f"Sending email to {to_email}: {subject}")

    try:
        service = get_email_service()
        success = service.send_email(
            to_email=to_email,
            subject=subject,
            template_name=template_name,
            context=context,
            to_name=to_name,
        )

        if success:
            logger.info(f"Email sent successfully to {to_email}")
            return {"status": "success", "to": to_email, "subject": subject}
        else:
            logger.warning(f"Email sending returned False for {to_email}")
            raise Exception("Email service returned failure status")

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_reminder_email_task(
    self,
    user_id: str,
    instance_id: str,
    reminder_type: str,
):
    """
    Send a compliance reminder email.

    Args:
        user_id: UUID of the user to notify
        instance_id: UUID of the compliance instance
        reminder_type: Type of reminder ('t3', 'due', 'overdue')

    Returns:
        dict: Result with status
    """
    logger.info(f"Sending {reminder_type} reminder email for instance {instance_id} to user {user_id}")

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        instance = db.query(ComplianceInstance).filter(ComplianceInstance.id == UUID(instance_id)).first()

        if not user or not instance:
            logger.error(f"User {user_id} or instance {instance_id} not found")
            return {"status": "error", "message": "User or instance not found"}

        success = send_reminder_email(user, instance, reminder_type)

        if success:
            return {"status": "success", "reminder_type": reminder_type}
        else:
            raise Exception("Email sending failed")

    except Exception as e:
        logger.error(f"Failed to send reminder email: {e}")
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_escalation_email_task(
    self,
    user_id: str,
    instance_id: str,
    days_overdue: int,
):
    """
    Send an escalation email for overdue compliance.

    Args:
        user_id: UUID of the CFO/Admin to escalate to
        instance_id: UUID of the overdue compliance instance
        days_overdue: Number of days past due

    Returns:
        dict: Result with status
    """
    logger.info(
        f"Sending escalation email for instance {instance_id} " f"({days_overdue} days overdue) to user {user_id}"
    )

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        instance = db.query(ComplianceInstance).filter(ComplianceInstance.id == UUID(instance_id)).first()

        if not user or not instance:
            logger.error(f"User {user_id} or instance {instance_id} not found")
            return {"status": "error", "message": "User or instance not found"}

        success = send_escalation_email(user, instance, days_overdue)

        if success:
            return {"status": "success", "days_overdue": days_overdue}
        else:
            raise Exception("Email sending failed")

    except Exception as e:
        logger.error(f"Failed to send escalation email: {e}")
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_task_assigned_email_task(
    self,
    user_id: str,
    task_id: str,
):
    """
    Send email notification when a task is assigned.

    Args:
        user_id: UUID of the user assigned to the task
        task_id: UUID of the workflow task

    Returns:
        dict: Result with status
    """
    logger.info(f"Sending task assignment email for task {task_id} to user {user_id}")

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        task = db.query(WorkflowTask).filter(WorkflowTask.id == UUID(task_id)).first()

        if not user or not task:
            logger.error(f"User {user_id} or task {task_id} not found")
            return {"status": "error", "message": "User or task not found"}

        success = send_task_assigned_email(user, task)

        if success:
            return {"status": "success", "task_name": task.task_name}
        else:
            raise Exception("Email sending failed")

    except Exception as e:
        logger.error(f"Failed to send task assignment email: {e}")
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_evidence_status_email_task(
    self,
    user_id: str,
    evidence_id: str,
    approved: bool,
    rejection_reason: Optional[str] = None,
):
    """
    Send email notification when evidence is approved or rejected.

    Args:
        user_id: UUID of the user who uploaded the evidence
        evidence_id: UUID of the evidence record
        approved: True if approved, False if rejected
        rejection_reason: Reason for rejection (if rejected)

    Returns:
        dict: Result with status
    """
    status_text = "approved" if approved else "rejected"
    logger.info(f"Sending evidence {status_text} email for evidence {evidence_id} to user {user_id}")

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        evidence = db.query(Evidence).filter(Evidence.id == UUID(evidence_id)).first()

        if not user or not evidence:
            logger.error(f"User {user_id} or evidence {evidence_id} not found")
            return {"status": "error", "message": "User or evidence not found"}

        success = send_evidence_status_email(user, evidence, approved, rejection_reason)

        if success:
            return {"status": "success", "approved": approved}
        else:
            raise Exception("Email sending failed")

    except Exception as e:
        logger.error(f"Failed to send evidence status email: {e}")
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_task_reminder_email_task(
    self,
    user_id: str,
    task_id: str,
    days_until_due: int,
):
    """
    Send email reminder for upcoming task.

    Args:
        user_id: UUID of the user assigned to the task
        task_id: UUID of the workflow task
        days_until_due: Number of days until due

    Returns:
        dict: Result with status
    """
    logger.info(f"Sending task reminder email for task {task_id} " f"({days_until_due} days left) to user {user_id}")

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        task = db.query(WorkflowTask).filter(WorkflowTask.id == UUID(task_id)).first()

        if not user or not task:
            logger.error(f"User {user_id} or task {task_id} not found")
            return {"status": "error", "message": "User or task not found"}

        success = send_task_reminder_email(user, task, days_until_due)

        if success:
            return {"status": "success", "days_until_due": days_until_due}
        else:
            raise Exception("Email sending failed")

    except Exception as e:
        logger.error(f"Failed to send task reminder email: {e}")
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()
