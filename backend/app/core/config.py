"""
Application configuration using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Compliance OS"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300

    # JWT Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # File Storage (Render Persistent Disk)
    EVIDENCE_STORAGE_PATH: str = "./uploads/evidence"  # Local dev; production: /var/data/evidence
    EVIDENCE_MAX_FILE_SIZE: int = 25 * 1024 * 1024  # 25MB
    EVIDENCE_ALLOWED_TYPES: List[str] = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
        "application/vnd.ms-excel",  # xls
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
        "application/msword",  # doc
    ]

    # AWS S3 (optional, for future cloud storage)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-south-1"
    AWS_S3_BUCKET_NAME: str = ""
    AWS_S3_ENDPOINT_URL: str = ""  # For MinIO or local S3

    # Email
    EMAIL_ENABLED: bool = False  # Toggle for email sending (disable in dev)
    SENDGRID_API_KEY: str = ""
    EMAIL_FROM_ADDRESS: str = "noreply@complianceos.com"
    EMAIL_FROM_NAME: str = "Compliance OS"

    # Slack
    SLACK_WEBHOOK_URL: str = ""

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
