"""
Notification Service
Handles multi-channel notifications (in-app only for Phase 4, email/Slack deferred to Phase 5)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import (
    Notification,
    User,
    WorkflowTask,
    ComplianceInstance,
    Evidence,
)


# Notification types
class NotificationType:
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    TASK_REJECTED = "task_rejected"
    APPROVAL_REQUEST = "approval_request"
    REMINDER_T3 = "reminder_t3"
    REMINDER_DUE = "reminder_due"
    OVERDUE_ALERT = "overdue_alert"
    ESCALATION = "escalation"
    EVIDENCE_UPLOADED = "evidence_uploaded"
    EVIDENCE_APPROVED = "evidence_approved"
    EVIDENCE_REJECTED = "evidence_rejected"
    INSTANCE_CREATED = "instance_created"
    INSTANCE_COMPLETED = "instance_completed"


def create_notification(
    db: Session,
    user_id: UUID,
    tenant_id: UUID,
    notification_type: str,
    title: str,
    message: str,
    link: Optional[str] = None,
    created_by: Optional[UUID] = None,
) -> Notification:
    """
    Create an in-app notification.

    Args:
        db: Database session
        user_id: User UUID who should receive the notification
        tenant_id: Tenant UUID
        notification_type: Type of notification (from NotificationType)
        title: Notification title
        message: Notification body message
        link: Optional link to related resource
        created_by: Optional user who triggered this notification

    Returns:
        Created Notification object
    """
    notification = Notification(
        user_id=user_id,
        tenant_id=tenant_id,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
        is_read=False,
        created_at=datetime.utcnow(),
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


def get_user_notifications(
    db: Session, user_id: UUID, tenant_id: UUID, unread_only: bool = False, limit: int = 50, offset: int = 0
) -> list[Notification]:
    """
    Get notifications for a user.

    Args:
        db: Database session
        user_id: User UUID
        tenant_id: Tenant UUID
        unread_only: If True, only return unread notifications
        limit: Maximum number to return
        offset: Pagination offset

    Returns:
        List of Notification objects, ordered by created_at desc
    """
    query = db.query(Notification).filter(Notification.user_id == user_id, Notification.tenant_id == tenant_id)

    if unread_only:
        query = query.filter(Notification.is_read == False)  # noqa: E712

    return query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()


def get_unread_count(db: Session, user_id: UUID, tenant_id: UUID) -> int:
    """
    Get count of unread notifications for a user.

    Args:
        db: Database session
        user_id: User UUID
        tenant_id: Tenant UUID

    Returns:
        Count of unread notifications
    """
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.tenant_id == tenant_id, Notification.is_read == False)  # noqa: E712
        .count()
    )


def mark_notification_read(
    db: Session, notification_id: UUID, user_id: UUID, tenant_id: UUID
) -> Optional[Notification]:
    """
    Mark a notification as read.

    Args:
        db: Database session
        notification_id: Notification UUID
        user_id: User UUID (must match notification owner)
        tenant_id: Tenant UUID

    Returns:
        Updated Notification or None if not found
    """
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id, Notification.user_id == user_id, Notification.tenant_id == tenant_id
        )
        .first()
    )

    if not notification:
        return None

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        db.commit()
        db.refresh(notification)

    return notification


def mark_all_read(db: Session, user_id: UUID, tenant_id: UUID) -> int:
    """
    Mark all notifications as read for a user.

    Args:
        db: Database session
        user_id: User UUID
        tenant_id: Tenant UUID

    Returns:
        Count of notifications marked as read
    """
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.tenant_id == tenant_id, Notification.is_read == False)  # noqa: E712
        .update({"is_read": True, "read_at": datetime.utcnow()})
    )

    db.commit()
    return count


def delete_notification(db: Session, notification_id: UUID, user_id: UUID, tenant_id: UUID) -> bool:
    """
    Delete a notification.

    Args:
        db: Database session
        notification_id: Notification UUID
        user_id: User UUID (must match notification owner)
        tenant_id: Tenant UUID

    Returns:
        True if deleted, False if not found
    """
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id, Notification.user_id == user_id, Notification.tenant_id == tenant_id
        )
        .first()
    )

    if not notification:
        return False

    db.delete(notification)
    db.commit()
    return True


def delete_old_notifications(db: Session, tenant_id: UUID, days_old: int = 90) -> int:
    """
    Delete notifications older than X days.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        days_old: Age threshold in days

    Returns:
        Count of deleted notifications
    """
    from datetime import timedelta

    cutoff = datetime.utcnow() - timedelta(days=days_old)

    count = (
        db.query(Notification).filter(Notification.tenant_id == tenant_id, Notification.created_at < cutoff).delete()
    )

    db.commit()
    return count


# ============ Specific Notification Helpers ============


def notify_task_assigned(db: Session, task: WorkflowTask, assigned_user: User) -> Optional[Notification]:
    """
    Create notification when a task is assigned to a user.

    Args:
        db: Database session
        task: WorkflowTask that was assigned
        assigned_user: User who was assigned

    Returns:
        Created Notification or None if user not found
    """
    if not assigned_user:
        return None

    instance = task.compliance_instance
    master_name = (
        instance.compliance_master.compliance_name if instance and instance.compliance_master else "Compliance"
    )

    return create_notification(
        db=db,
        user_id=assigned_user.id,
        tenant_id=task.tenant_id,
        notification_type=NotificationType.TASK_ASSIGNED,
        title=f"New task assigned: {task.task_name}",
        message=f"You have been assigned the '{task.task_type}' task for {master_name}. Due: {task.due_date}",
        link=f"/compliance-instances/{task.compliance_instance_id}",
    )


def notify_task_completed(db: Session, task: WorkflowTask, notify_user: User) -> Optional[Notification]:
    """
    Create notification when a task is completed.

    Args:
        db: Database session
        task: WorkflowTask that was completed
        notify_user: User to notify (e.g., instance owner)

    Returns:
        Created Notification
    """
    if not notify_user:
        return None

    instance = task.compliance_instance
    master_name = (
        instance.compliance_master.compliance_name if instance and instance.compliance_master else "Compliance"
    )

    return create_notification(
        db=db,
        user_id=notify_user.id,
        tenant_id=task.tenant_id,
        notification_type=NotificationType.TASK_COMPLETED,
        title=f"Task completed: {task.task_name}",
        message=f"The '{task.task_type}' task for {master_name} has been completed.",
        link=f"/compliance-instances/{task.compliance_instance_id}",
    )


def notify_reminder_t3(db: Session, instance: ComplianceInstance, owner: User) -> Optional[Notification]:
    """
    Create T-3 day reminder notification.

    Args:
        db: Database session
        instance: ComplianceInstance due in 3 days
        owner: Instance owner to notify

    Returns:
        Created Notification
    """
    if not owner:
        return None

    master_name = instance.compliance_master.compliance_name if instance.compliance_master else "Compliance"

    return create_notification(
        db=db,
        user_id=owner.id,
        tenant_id=instance.tenant_id,
        notification_type=NotificationType.REMINDER_T3,
        title=f"Reminder: {master_name} due in 3 days",
        message=f"{master_name} is due on {instance.due_date}. Please ensure all tasks are completed.",
        link=f"/compliance-instances/{instance.id}",
    )


def notify_reminder_due(db: Session, instance: ComplianceInstance, user: User) -> Optional[Notification]:
    """
    Create due date reminder notification.

    Args:
        db: Database session
        instance: ComplianceInstance due today
        user: User to notify

    Returns:
        Created Notification
    """
    if not user:
        return None

    master_name = instance.compliance_master.compliance_name if instance.compliance_master else "Compliance"

    return create_notification(
        db=db,
        user_id=user.id,
        tenant_id=instance.tenant_id,
        notification_type=NotificationType.REMINDER_DUE,
        title=f"Due today: {master_name}",
        message=f"{master_name} is due TODAY ({instance.due_date}). Please complete all pending tasks.",
        link=f"/compliance-instances/{instance.id}",
    )


def notify_overdue_escalation(
    db: Session, instance: ComplianceInstance, escalate_to: User, days_overdue: int
) -> Optional[Notification]:
    """
    Create escalation notification for overdue compliance.

    Args:
        db: Database session
        instance: Overdue ComplianceInstance
        escalate_to: User to escalate to (e.g., CFO)
        days_overdue: Number of days overdue

    Returns:
        Created Notification
    """
    if not escalate_to:
        return None

    master_name = instance.compliance_master.compliance_name if instance.compliance_master else "Compliance"
    entity_name = instance.entity.entity_name if instance.entity else "Entity"

    return create_notification(
        db=db,
        user_id=escalate_to.id,
        tenant_id=instance.tenant_id,
        notification_type=NotificationType.ESCALATION,
        title=f"Escalation: {master_name} overdue by {days_overdue} days",
        message=(
            f"{master_name} for {entity_name} was due on {instance.due_date} "
            f"and is now {days_overdue} days overdue. Immediate attention required."
        ),
        link=f"/compliance-instances/{instance.id}",
    )


def notify_evidence_uploaded(db: Session, evidence: Evidence, approver: User) -> Optional[Notification]:
    """
    Notify approver when new evidence is uploaded.

    Args:
        db: Database session
        evidence: Evidence that was uploaded
        approver: User who should review/approve

    Returns:
        Created Notification
    """
    if not approver:
        return None

    instance = evidence.compliance_instance
    master_name = (
        instance.compliance_master.compliance_name if instance and instance.compliance_master else "Compliance"
    )

    return create_notification(
        db=db,
        user_id=approver.id,
        tenant_id=evidence.tenant_id,
        notification_type=NotificationType.EVIDENCE_UPLOADED,
        title=f"Evidence pending approval: {evidence.evidence_name}",
        message=(
            f"New evidence '{evidence.evidence_name}' has been uploaded for "
            f"{master_name} and requires your approval."
        ),
        link=f"/compliance-instances/{evidence.compliance_instance_id}",
    )


def notify_evidence_approved(db: Session, evidence: Evidence, owner: User) -> Optional[Notification]:
    """
    Notify owner when evidence is approved.

    Args:
        db: Database session
        evidence: Evidence that was approved
        owner: Instance owner to notify

    Returns:
        Created Notification
    """
    if not owner:
        return None

    return create_notification(
        db=db,
        user_id=owner.id,
        tenant_id=evidence.tenant_id,
        notification_type=NotificationType.EVIDENCE_APPROVED,
        title=f"Evidence approved: {evidence.evidence_name}",
        message=f"Your evidence '{evidence.evidence_name}' has been approved.",
        link=f"/compliance-instances/{evidence.compliance_instance_id}",
    )


def notify_evidence_rejected(
    db: Session, evidence: Evidence, owner: User, rejection_reason: str
) -> Optional[Notification]:
    """
    Notify owner when evidence is rejected.

    Args:
        db: Database session
        evidence: Evidence that was rejected
        owner: Instance owner to notify
        rejection_reason: Reason for rejection

    Returns:
        Created Notification
    """
    if not owner:
        return None

    return create_notification(
        db=db,
        user_id=owner.id,
        tenant_id=evidence.tenant_id,
        notification_type=NotificationType.EVIDENCE_REJECTED,
        title=f"Evidence rejected: {evidence.evidence_name}",
        message=(
            f"Your evidence '{evidence.evidence_name}' has been rejected. "
            f"Reason: {rejection_reason}. Please upload a corrected version."
        ),
        link=f"/compliance-instances/{evidence.compliance_instance_id}",
    )


def notify_instance_created(db: Session, instance: ComplianceInstance, owner: User) -> Optional[Notification]:
    """
    Notify owner when a new compliance instance is created/assigned.

    Args:
        db: Database session
        instance: New ComplianceInstance
        owner: Instance owner to notify

    Returns:
        Created Notification
    """
    if not owner:
        return None

    master_name = instance.compliance_master.compliance_name if instance.compliance_master else "Compliance"
    entity_name = instance.entity.entity_name if instance.entity else "Entity"

    return create_notification(
        db=db,
        user_id=owner.id,
        tenant_id=instance.tenant_id,
        notification_type=NotificationType.INSTANCE_CREATED,
        title=f"New compliance assigned: {master_name}",
        message=f"You have been assigned as owner for {master_name} ({entity_name}). Due: {instance.due_date}",
        link=f"/compliance-instances/{instance.id}",
    )


def notify_instance_completed(
    db: Session, instance: ComplianceInstance, notify_users: list[User]
) -> list[Notification]:
    """
    Notify users when a compliance instance is completed.

    Args:
        db: Database session
        instance: Completed ComplianceInstance
        notify_users: List of users to notify

    Returns:
        List of created Notifications
    """
    notifications = []

    master_name = instance.compliance_master.compliance_name if instance.compliance_master else "Compliance"
    entity_name = instance.entity.entity_name if instance.entity else "Entity"

    for user in notify_users:
        if user:
            notification = create_notification(
                db=db,
                user_id=user.id,
                tenant_id=instance.tenant_id,
                notification_type=NotificationType.INSTANCE_COMPLETED,
                title=f"Compliance completed: {master_name}",
                message=f"{master_name} for {entity_name} has been marked as completed.",
                link=f"/compliance-instances/{instance.id}",
            )
            notifications.append(notification)

    return notifications
