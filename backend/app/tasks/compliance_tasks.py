"""
Background tasks for compliance operations
Runs scheduled jobs for instance generation and status recalculation
"""

import logging
from datetime import date

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.models import Tenant
from app.services.compliance_engine import (
    generate_instances_for_period,
    calculate_period_for_frequency,
    recalculate_rag_for_tenant,
)

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def generate_compliance_instances_daily(self):
    """
    Generate compliance instances from masters for all tenants.

    Runs daily at 2 AM IST.

    Process:
    1. Get all active tenants
    2. For each tenant, generate monthly instances for current period
    3. Log counts and any errors

    Returns:
        dict: Summary of instances created per tenant
    """
    logger.info("Starting daily compliance instance generation")

    db = SessionLocal()
    results = {}

    try:
        # Get all active tenants
        tenants = db.query(Tenant).filter(Tenant.status == "active").all()

        if not tenants:
            logger.warning("No active tenants found")
            return {"status": "no_tenants", "created": 0}

        today = date.today()

        for tenant in tenants:
            try:
                # Calculate current monthly period
                period_start, period_end = calculate_period_for_frequency("Monthly", today)

                # Generate instances for this tenant
                instances = generate_instances_for_period(
                    db=db, tenant_id=tenant.id, period_start=period_start, period_end=period_end
                )

                results[str(tenant.id)] = {
                    "tenant_name": tenant.tenant_name,
                    "instances_created": len(instances),
                    "period": f"{period_start} to {period_end}",
                }

                logger.info(f"Generated {len(instances)} instances for tenant {tenant.tenant_name}")

            except Exception as e:
                logger.error(f"Error generating instances for tenant {tenant.id}: {str(e)}")
                results[str(tenant.id)] = {"tenant_name": tenant.tenant_name, "error": str(e)}

        total_created = sum(r.get("instances_created", 0) for r in results.values())

        logger.info(f"Daily instance generation complete. Total created: {total_created}")

        return {"status": "success", "total_created": total_created, "tenants": results}

    except Exception as e:
        logger.error(f"Critical error in generate_compliance_instances_daily: {str(e)}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def recalculate_rag_status_hourly(self):
    """
    Recalculate RAG status for all non-completed instances.

    Runs every hour at :00.

    Process:
    1. Get all active tenants
    2. For each tenant, recalculate RAG status for all instances
    3. Update Redis cache if available

    Returns:
        dict: Summary of instances updated per tenant
    """
    logger.info("Starting hourly RAG status recalculation")

    db = SessionLocal()
    results = {}

    try:
        # Get all active tenants
        tenants = db.query(Tenant).filter(Tenant.status == "active").all()

        if not tenants:
            logger.warning("No active tenants found")
            return {"status": "no_tenants", "updated": 0}

        for tenant in tenants:
            try:
                # Recalculate RAG for this tenant
                updated_count = recalculate_rag_for_tenant(db, tenant.id)

                results[str(tenant.id)] = {"tenant_name": tenant.tenant_name, "instances_updated": updated_count}

                logger.info(f"Updated RAG status for {updated_count} instances " f"for tenant {tenant.tenant_name}")

            except Exception as e:
                logger.error(f"Error recalculating RAG for tenant {tenant.id}: {str(e)}")
                results[str(tenant.id)] = {"tenant_name": tenant.tenant_name, "error": str(e)}

        total_updated = sum(r.get("instances_updated", 0) for r in results.values())

        logger.info(f"Hourly RAG recalculation complete. Total updated: {total_updated}")

        # Invalidate dashboard cache (if Redis is configured)
        try:
            invalidate_dashboard_cache()
        except Exception as e:
            logger.warning(f"Failed to invalidate dashboard cache: {str(e)}")

        return {"status": "success", "total_updated": total_updated, "tenants": results}

    except Exception as e:
        logger.error(f"Critical error in recalculate_rag_status_hourly: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def generate_quarterly_instances(self):
    """
    Generate quarterly compliance instances.

    Runs on the 1st of each quarter (Apr 1, Jul 1, Oct 1, Jan 1).

    Returns:
        dict: Summary of quarterly instances created
    """
    logger.info("Starting quarterly instance generation")

    db = SessionLocal()
    results = {}

    try:
        tenants = db.query(Tenant).filter(Tenant.status == "active").all()
        today = date.today()

        # Calculate quarterly period
        period_start, period_end = calculate_period_for_frequency("Quarterly", today)

        for tenant in tenants:
            try:
                instances = generate_instances_for_period(
                    db=db, tenant_id=tenant.id, period_start=period_start, period_end=period_end
                )

                # Filter for quarterly frequency only
                quarterly_count = len(
                    [i for i in instances if i.compliance_master and i.compliance_master.frequency == "Quarterly"]
                )

                results[str(tenant.id)] = {
                    "tenant_name": tenant.tenant_name,
                    "quarterly_instances": quarterly_count,
                    "period": f"{period_start} to {period_end}",
                }

                logger.info(f"Generated {quarterly_count} quarterly instances " f"for tenant {tenant.tenant_name}")

            except Exception as e:
                logger.error(f"Error generating quarterly instances for tenant {tenant.id}: {str(e)}")
                results[str(tenant.id)] = {"error": str(e)}

        return {"status": "success", "tenants": results}

    except Exception as e:
        logger.error(f"Critical error in generate_quarterly_instances: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def generate_annual_instances(self):
    """
    Generate annual compliance instances.

    Runs on April 1st (start of India Financial Year).

    Returns:
        dict: Summary of annual instances created
    """
    logger.info("Starting annual instance generation")

    db = SessionLocal()
    results = {}

    try:
        tenants = db.query(Tenant).filter(Tenant.status == "active").all()
        today = date.today()

        # Calculate annual period (India FY)
        period_start, period_end = calculate_period_for_frequency("Annual", today)

        for tenant in tenants:
            try:
                instances = generate_instances_for_period(
                    db=db, tenant_id=tenant.id, period_start=period_start, period_end=period_end
                )

                # Filter for annual frequency only
                annual_count = len(
                    [i for i in instances if i.compliance_master and i.compliance_master.frequency == "Annual"]
                )

                results[str(tenant.id)] = {
                    "tenant_name": tenant.tenant_name,
                    "annual_instances": annual_count,
                    "period": f"{period_start} to {period_end}",
                }

                logger.info(f"Generated {annual_count} annual instances " f"for tenant {tenant.tenant_name}")

            except Exception as e:
                logger.error(f"Error generating annual instances for tenant {tenant.id}: {str(e)}")
                results[str(tenant.id)] = {"error": str(e)}

        return {"status": "success", "tenants": results}

    except Exception as e:
        logger.error(f"Critical error in generate_annual_instances: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries))

    finally:
        db.close()


@celery_app.task
def update_overdue_status():
    """
    Update status for overdue compliance instances.

    Runs daily at 6 AM IST.

    Sets status to 'Overdue' for instances past due date that aren't completed.

    Returns:
        dict: Count of instances marked as overdue
    """
    logger.info("Starting overdue status update")

    db = SessionLocal()

    try:
        from app.models import ComplianceInstance

        today = date.today()
        overdue_count = 0

        # Find all non-completed instances that are past due
        overdue_instances = (
            db.query(ComplianceInstance)
            .filter(ComplianceInstance.due_date < today, ComplianceInstance.status.notin_(["Completed", "Overdue"]))
            .all()
        )

        for instance in overdue_instances:
            instance.status = "Overdue"
            instance.rag_status = "Red"
            overdue_count += 1

        db.commit()

        logger.info(f"Marked {overdue_count} instances as overdue")

        return {"status": "success", "overdue_count": overdue_count}

    except Exception as e:
        logger.error(f"Error updating overdue status: {str(e)}")
        db.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


def invalidate_dashboard_cache():
    """
    Invalidate Redis cache for dashboard data.

    Called after RAG recalculation to ensure fresh data on dashboard.
    """
    try:
        from app.core.redis import redis_client

        # Delete all dashboard cache keys
        cursor = 0
        deleted_count = 0

        while True:
            cursor, keys = redis_client.scan(cursor, match="dashboard:*", count=100)
            if keys:
                redis_client.delete(*keys)
                deleted_count += len(keys)
            if cursor == 0:
                break

        logger.info(f"Invalidated {deleted_count} dashboard cache keys")

    except Exception as e:
        logger.warning(f"Redis cache invalidation failed: {str(e)}")
