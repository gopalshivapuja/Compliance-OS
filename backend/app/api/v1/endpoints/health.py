"""
Health check endpoints for monitoring and uptime checks
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.redis import get_redis_client
from app.core.config import settings

router = APIRouter()


def check_database(db: Session) -> str:
    """Check database connectivity"""
    try:
        # Execute simple query to verify connection
        db.execute(text("SELECT 1"))
        return "connected"
    except Exception as e:
        return f"error: {str(e)[:50]}"


def check_redis() -> str:
    """Check Redis connectivity"""
    try:
        redis_client = get_redis_client()
        # Test Redis connection
        redis_client.ping()
        return "connected"
    except Exception as e:
        return f"error: {str(e)[:50]}"


def check_celery() -> str:
    """Check Celery worker status"""
    try:
        # Import here to avoid circular dependency
        from app.celery_app import celery_app

        # Get active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()

        if active_workers and len(active_workers) > 0:
            return "running"
        else:
            return "no_workers"
    except Exception as e:
        return f"error: {str(e)[:50]}"


def check_s3() -> str:
    """Check S3 connectivity (optional for V1)"""
    try:
        import boto3
        from botocore.exceptions import ClientError

        # Only check if S3 is configured
        if not settings.AWS_S3_BUCKET_NAME:
            return "not_configured"

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )

        # Test bucket access
        s3_client.head_bucket(Bucket=settings.AWS_S3_BUCKET_NAME)
        return "accessible"
    except ClientError:
        return "bucket_not_found"
    except Exception as e:
        return f"error: {str(e)[:50]}"


@router.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint

    Returns status of all critical services:
    - API server
    - Database (PostgreSQL)
    - Cache (Redis)
    - Background jobs (Celery)
    - File storage (S3)

    Returns:
        dict: Health status of all services

    Raises:
        HTTPException: 503 Service Unavailable if any critical service is down
    """
    # Get current timestamp
    current_time = datetime.utcnow().isoformat()

    # Check all services
    db_status = check_database(db)
    redis_status = check_redis()
    celery_status = check_celery()
    s3_status = check_s3()

    # Build response
    health_status = {
        "status": "healthy",
        "timestamp": current_time,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "database": db_status,
            "redis": redis_status,
            "celery": celery_status,
            "s3": s3_status,
        },
    }

    # Define critical services (must be healthy)
    critical_services = {
        "database": db_status,
        "redis": redis_status,
    }

    # Check if any critical service is down
    critical_down = any(
        status.startswith("error") or status == "disconnected"
        for status in critical_services.values()
    )

    if critical_down:
        health_status["status"] = "unhealthy"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=health_status)

    return health_status


@router.get("/health/live", tags=["Health"])
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes liveness probe endpoint

    Returns 200 if application is alive (can accept requests)
    Does not check dependencies - just verifies process is running

    Returns:
        dict: Simple status message
    """
    return {"status": "alive"}


@router.get("/health/ready", tags=["Health"])
async def readiness_probe(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Kubernetes readiness probe endpoint

    Returns 200 if application is ready to serve traffic
    Checks critical dependencies (database, redis)

    Returns:
        dict: Readiness status

    Raises:
        HTTPException: 503 if not ready
    """
    db_status = check_database(db)
    redis_status = check_redis()

    ready = not db_status.startswith("error") and not redis_status.startswith("error")

    if not ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "database": db_status,
                "redis": redis_status,
            },
        )

    return {
        "status": "ready",
        "database": db_status,
        "redis": redis_status,
    }
