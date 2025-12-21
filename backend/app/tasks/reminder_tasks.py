"""
Background tasks for reminders and notifications
Runs scheduled jobs for T-3 reminders, due date alerts, and escalations
"""

import logging
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.models import (
    Tenant,
    ComplianceInstance,
    User,
    Role,
    WorkflowTask,
)
from app.models.entity import entity_access
from app.models.role import user_roles
from app.services.notification_service import (
    notify_reminder_t3,
    notify_reminder_due,
    notify_overdue_escalation,
)
from app.tasks.notification_tasks import (
    send_reminder_email_task,
    send_escalation_email_task,
    send_task_reminder_email_task,
)

logger = logging.getLogger(__name__)


def get_instance_owner(db, instance: ComplianceInstance) -> Optional[User]:
    """
    Get the owner user for a compliance instance.

    Priority:
    1. User with owner_role_code and entity access
    2. Any user with entity access
    """
    if not instance.compliance_master:
        return None

    owner_role_code = instance.compliance_master.owner_role_code

    if owner_role_code:
        # Find user with this role who has access to the entity
        role = db.query(Role).filter(Role.role_code == owner_role_code).first()
        if role:
            user = (
                db.query(User)
                .join(user_roles, User.id == user_roles.c.user_id)
                .join(entity_access, User.id == entity_access.c.user_id)
                .filter(
                    user_roles.c.role_id == role.id,
                    entity_access.c.entity_id == instance.entity_id,
                    User.status == "active",
                )
                .first()
            )

            if user:
                return user

    # Fallback: any active user with entity access
    user = (
        db.query(User)
        .join(entity_access, User.id == entity_access.c.user_id)
        .filter(entity_access.c.entity_id == instance.entity_id, User.status == "active")
        .first()
    )

    return user


def get_escalation_user(db, tenant_id: UUID) -> Optional[User]:
    """
    Get the user to escalate to (CFO or Admin).

    Priority:
    1. User with CFO role
    2. User with ADMIN role
    """
    # Try CFO first
    cfo_role = db.query(Role).filter(Role.role_code == "CFO").first()
    if cfo_role:
        cfo = (
            db.query(User)
            .join(user_roles, User.id == user_roles.c.user_id)
            .filter(user_roles.c.role_id == cfo_role.id, User.tenant_id == tenant_id, User.status == "active")
            .first()
        )
        if cfo:
            return cfo

    # Fallback to Admin
    admin_role = db.query(Role).filter(Role.role_code == "ADMIN").first()
    if admin_role:
        admin = (
            db.query(User)
            .join(user_roles, User.id == user_roles.c.user_id)
            .filter(user_roles.c.role_id == admin_role.id, User.tenant_id == tenant_id, User.status == "active")
            .first()
        )
        if admin:
            return admin

    return None


@celery_app.task(bind=True, max_retries=3)
def send_t3_reminders(self):
    """
    Send reminders for compliance items due in 3 days.

    Runs daily at 9 AM IST.

    Process:
    1. Find all non-completed instances with due_date = today + 3 days
    2. Get owner for each instance
    3. Create in-app notification

    Returns:
        dict: Summary of reminders sent
    """
    logger.info("Starting T-3 day reminder task")

    db = SessionLocal()
    reminders_sent = 0
    errors = []

    try:
        today = date.today()
        t3_date = today + timedelta(days=3)

        # Find instances due in 3 days
        instances = (
            db.query(ComplianceInstance)
            .filter(ComplianceInstance.due_date == t3_date, ComplianceInstance.status.notin_(["Completed", "Overdue"]))
            .all()
        )

        logger.info(f"Found {len(instances)} instances due in 3 days")

        for instance in instances:
            try:
                owner = get_instance_owner(db, instance)
                if owner:
                    notification = notify_reminder_t3(db, instance, owner)
                    if notification:
                        reminders_sent += 1
                        logger.debug(f"Sent T-3 reminder for instance {instance.id} " f"to user {owner.email}")
                        # Queue email notification
                        send_reminder_email_task.delay(
                            user_id=str(owner.id),
                            instance_id=str(instance.id),
                            reminder_type="t3",
                        )
                else:
                    logger.warning(f"No owner found for instance {instance.id}, " f"skipping T-3 reminder")

            except Exception as e:
                error_msg = f"Error sending T-3 reminder for instance {instance.id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        logger.info(f"T-3 reminder task complete. Sent: {reminders_sent}")

        return {
            "status": "success",
            "reminders_sent": reminders_sent,
            "instances_found": len(instances),
            "errors": errors if errors else None,
        }

    except Exception as e:
        logger.error(f"Critical error in send_t3_reminders: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def send_due_date_reminders(self):
    """
    Send reminders for compliance items due today.

    Runs daily at 9:30 AM IST.

    Process:
    1. Find all non-completed instances with due_date = today
    2. Get owner for each instance
    3. Create in-app notification for owner

    Returns:
        dict: Summary of reminders sent
    """
    logger.info("Starting due date reminder task")

    db = SessionLocal()
    reminders_sent = 0
    errors = []

    try:
        today = date.today()

        # Find instances due today
        instances = (
            db.query(ComplianceInstance)
            .filter(ComplianceInstance.due_date == today, ComplianceInstance.status.notin_(["Completed"]))
            .all()
        )

        logger.info(f"Found {len(instances)} instances due today")

        for instance in instances:
            try:
                owner = get_instance_owner(db, instance)
                if owner:
                    notification = notify_reminder_due(db, instance, owner)
                    if notification:
                        reminders_sent += 1
                        logger.debug(f"Sent due date reminder for instance {instance.id} " f"to user {owner.email}")
                        # Queue email notification
                        send_reminder_email_task.delay(
                            user_id=str(owner.id),
                            instance_id=str(instance.id),
                            reminder_type="due",
                        )
                else:
                    logger.warning(f"No owner found for instance {instance.id}, " f"skipping due date reminder")

            except Exception as e:
                error_msg = f"Error sending due date reminder for instance {instance.id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        logger.info(f"Due date reminder task complete. Sent: {reminders_sent}")

        return {
            "status": "success",
            "reminders_sent": reminders_sent,
            "instances_found": len(instances),
            "errors": errors if errors else None,
        }

    except Exception as e:
        logger.error(f"Critical error in send_due_date_reminders: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def escalate_overdue_items(self):
    """
    Escalate items overdue by 3+ days to CFO.

    Runs daily at 10 AM IST.

    Process:
    1. Find instances overdue by 3+ days that haven't been escalated
    2. Get CFO/Admin user for tenant
    3. Create escalation notification
    4. Mark instance as escalated to prevent duplicate notifications

    Returns:
        dict: Summary of escalations sent
    """
    logger.info("Starting overdue escalation task")

    db = SessionLocal()
    escalations_sent = 0
    errors = []

    try:
        today = date.today()
        escalation_threshold = today - timedelta(days=3)

        # Find instances overdue by 3+ days
        # Use metadata to track escalation status
        overdue_instances = (
            db.query(ComplianceInstance)
            .filter(
                ComplianceInstance.due_date <= escalation_threshold, ComplianceInstance.status.notin_(["Completed"])
            )
            .all()
        )

        logger.info(f"Found {len(overdue_instances)} instances overdue by 3+ days")

        # Group by tenant for escalation user lookup
        tenant_escalation_users = {}

        for instance in overdue_instances:
            try:
                # Check if already escalated (using metadata field)
                metadata = instance.metadata or {}
                if metadata.get("escalated"):
                    continue

                # Calculate days overdue
                days_overdue = (today - instance.due_date).days

                # Get escalation user for tenant
                tenant_id = instance.tenant_id
                if tenant_id not in tenant_escalation_users:
                    tenant_escalation_users[tenant_id] = get_escalation_user(db, tenant_id)

                escalate_to = tenant_escalation_users.get(tenant_id)

                if escalate_to:
                    notification = notify_overdue_escalation(db, instance, escalate_to, days_overdue)
                    if notification:
                        # Mark as escalated
                        instance.metadata = {
                            **(instance.metadata or {}),
                            "escalated": True,
                            "escalated_at": str(today),
                            "escalated_to": str(escalate_to.id),
                        }
                        db.commit()

                        escalations_sent += 1
                        logger.debug(
                            f"Escalated instance {instance.id} " f"({days_overdue} days overdue) to {escalate_to.email}"
                        )
                        # Queue escalation email
                        send_escalation_email_task.delay(
                            user_id=str(escalate_to.id),
                            instance_id=str(instance.id),
                            days_overdue=days_overdue,
                        )
                else:
                    logger.warning(
                        f"No escalation user found for tenant {tenant_id}, "
                        f"skipping escalation for instance {instance.id}"
                    )

            except Exception as e:
                error_msg = f"Error escalating instance {instance.id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                db.rollback()

        logger.info(f"Escalation task complete. Escalated: {escalations_sent}")

        return {
            "status": "success",
            "escalations_sent": escalations_sent,
            "overdue_instances_found": len(overdue_instances),
            "errors": errors if errors else None,
        }

    except Exception as e:
        logger.error(f"Critical error in escalate_overdue_items: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def send_task_reminders(self):
    """
    Send reminders for workflow tasks due soon.

    Runs daily at 9:15 AM IST.

    Process:
    1. Find pending/in-progress tasks due within 2 days
    2. Notify assigned user
    3. Create in-app notification

    Returns:
        dict: Summary of task reminders sent
    """
    logger.info("Starting workflow task reminder task")

    db = SessionLocal()
    reminders_sent = 0
    errors = []

    try:
        today = date.today()
        reminder_date = today + timedelta(days=2)

        # Find tasks due soon
        tasks = (
            db.query(WorkflowTask)
            .filter(
                WorkflowTask.due_date <= reminder_date,
                WorkflowTask.due_date >= today,
                WorkflowTask.status.in_(["Pending", "In Progress"]),
            )
            .all()
        )

        logger.info(f"Found {len(tasks)} tasks due within 2 days")

        from app.services.notification_service import create_notification, NotificationType

        for task in tasks:
            try:
                # Get assigned user
                if task.assigned_to_user_id:
                    user = db.query(User).filter(User.id == task.assigned_to_user_id).first()

                    if user:
                        days_until_due = (task.due_date - today).days
                        message = (
                            f"Task '{task.task_name}' is due "
                            f"{'today' if days_until_due == 0 else f'in {days_until_due} day(s)'}. "
                            f"Please complete it before the deadline."
                        )

                        notification = create_notification(
                            db=db,
                            user_id=user.id,
                            tenant_id=task.tenant_id,
                            notification_type=NotificationType.REMINDER_DUE,
                            title=f"Task due soon: {task.task_name}",
                            message=message,
                            link=f"/compliance-instances/{task.compliance_instance_id}",
                        )

                        if notification:
                            reminders_sent += 1
                            # Queue email notification
                            send_task_reminder_email_task.delay(
                                user_id=str(user.id),
                                task_id=str(task.id),
                                days_until_due=days_until_due,
                            )

            except Exception as e:
                error_msg = f"Error sending task reminder for task {task.id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        logger.info(f"Task reminder task complete. Sent: {reminders_sent}")

        return {
            "status": "success",
            "reminders_sent": reminders_sent,
            "tasks_found": len(tasks),
            "errors": errors if errors else None,
        }

    except Exception as e:
        logger.error(f"Critical error in send_task_reminders: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()


@celery_app.task
def cleanup_old_notifications():
    """
    Clean up notifications older than 90 days.

    Runs weekly on Sunday at 3 AM IST.

    Returns:
        dict: Count of notifications deleted
    """
    logger.info("Starting notification cleanup task")

    db = SessionLocal()

    try:
        from app.services.notification_service import delete_old_notifications

        tenants = db.query(Tenant).filter(Tenant.status == "active").all()
        total_deleted = 0

        for tenant in tenants:
            try:
                deleted = delete_old_notifications(db, tenant.id, days_old=90)
                total_deleted += deleted
                logger.debug(f"Deleted {deleted} old notifications for tenant {tenant.id}")

            except Exception as e:
                logger.error(f"Error cleaning up notifications for tenant {tenant.id}: {str(e)}")

        logger.info(f"Notification cleanup complete. Deleted: {total_deleted}")

        return {"status": "success", "notifications_deleted": total_deleted}

    except Exception as e:
        logger.error(f"Error in cleanup_old_notifications: {str(e)}")
        return {"status": "error", "message": str(e)}

    finally:
        db.close()
