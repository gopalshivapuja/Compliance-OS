"""Celery background tasks"""

from app.tasks.compliance_tasks import (
    generate_compliance_instances_daily,
    recalculate_rag_status_hourly,
    generate_quarterly_instances,
    generate_annual_instances,
    update_overdue_status,
)
from app.tasks.reminder_tasks import (
    send_t3_reminders,
    send_due_date_reminders,
    escalate_overdue_items,
    send_task_reminders,
    cleanup_old_notifications,
)
from app.tasks.notification_tasks import (
    send_email_task,
    send_reminder_email_task,
    send_escalation_email_task,
    send_task_assigned_email_task,
    send_evidence_status_email_task,
    send_task_reminder_email_task,
)

__all__ = [
    # Compliance tasks
    "generate_compliance_instances_daily",
    "recalculate_rag_status_hourly",
    "generate_quarterly_instances",
    "generate_annual_instances",
    "update_overdue_status",
    # Reminder tasks
    "send_t3_reminders",
    "send_due_date_reminders",
    "escalate_overdue_items",
    "send_task_reminders",
    "cleanup_old_notifications",
    # Notification (email) tasks
    "send_email_task",
    "send_reminder_email_task",
    "send_escalation_email_task",
    "send_task_assigned_email_task",
    "send_evidence_status_email_task",
    "send_task_reminder_email_task",
]
