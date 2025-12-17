"""
Celery configuration for background jobs
"""
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "compliance_os",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",  # IST
    enable_utc=True,
)

