"""
Celery configuration for background jobs
Includes beat schedule for automated compliance tasks
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "compliance_os",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.compliance_tasks",
        "app.tasks.reminder_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",  # IST
    enable_utc=True,
    # Task settings
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes hard limit
    task_acks_late=True,  # Acknowledge after task completes
    task_reject_on_worker_lost=True,
    # Worker settings
    worker_prefetch_multiplier=1,  # Disable prefetching for long tasks
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks to prevent memory leaks
)

# Celery Beat schedule for automated tasks
# All times are in IST (Asia/Kolkata)
celery_app.conf.beat_schedule = {
    # Daily compliance instance generation at 2 AM IST
    "generate-instances-daily": {
        "task": "app.tasks.compliance_tasks.generate_compliance_instances_daily",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "compliance"},
    },
    # Hourly RAG status recalculation at :00
    "recalculate-rag-hourly": {
        "task": "app.tasks.compliance_tasks.recalculate_rag_status_hourly",
        "schedule": crontab(minute=0),
        "options": {"queue": "compliance"},
    },
    # Daily overdue status update at 6 AM IST
    "update-overdue-daily": {
        "task": "app.tasks.compliance_tasks.update_overdue_status",
        "schedule": crontab(hour=6, minute=0),
        "options": {"queue": "compliance"},
    },
    # Quarterly instance generation on 1st of Apr, Jul, Oct, Jan
    "generate-quarterly-instances": {
        "task": "app.tasks.compliance_tasks.generate_quarterly_instances",
        "schedule": crontab(day_of_month=1, month_of_year="1,4,7,10", hour=2, minute=30),
        "options": {"queue": "compliance"},
    },
    # Annual instance generation on April 1st (start of India FY)
    "generate-annual-instances": {
        "task": "app.tasks.compliance_tasks.generate_annual_instances",
        "schedule": crontab(day_of_month=1, month_of_year=4, hour=3, minute=0),
        "options": {"queue": "compliance"},
    },
    # T-3 day reminders at 9 AM IST
    "send-t3-reminders": {
        "task": "app.tasks.reminder_tasks.send_t3_reminders",
        "schedule": crontab(hour=9, minute=0),
        "options": {"queue": "notifications"},
    },
    # Workflow task reminders at 9:15 AM IST
    "send-task-reminders": {
        "task": "app.tasks.reminder_tasks.send_task_reminders",
        "schedule": crontab(hour=9, minute=15),
        "options": {"queue": "notifications"},
    },
    # Due date reminders at 9:30 AM IST
    "send-due-date-reminders": {
        "task": "app.tasks.reminder_tasks.send_due_date_reminders",
        "schedule": crontab(hour=9, minute=30),
        "options": {"queue": "notifications"},
    },
    # Overdue escalation at 10 AM IST
    "escalate-overdue": {
        "task": "app.tasks.reminder_tasks.escalate_overdue_items",
        "schedule": crontab(hour=10, minute=0),
        "options": {"queue": "notifications"},
    },
    # Weekly notification cleanup on Sunday at 3 AM IST
    "cleanup-old-notifications": {
        "task": "app.tasks.reminder_tasks.cleanup_old_notifications",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),
        "options": {"queue": "maintenance"},
    },
}

# Task routing to specific queues
celery_app.conf.task_routes = {
    "app.tasks.compliance_tasks.*": {"queue": "compliance"},
    "app.tasks.reminder_tasks.*": {"queue": "notifications"},
}
