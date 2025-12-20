"""
Compliance Engine Service
Handles compliance instance generation, status calculation, and RAG scoring
"""

from datetime import date, timedelta
from calendar import monthrange
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ComplianceMaster, ComplianceInstance, Entity, Evidence


# India Financial Year quarters (Apr-Mar)
INDIA_FY_QUARTERS = {
    1: {"start_month": 4, "end_month": 6},  # Q1: Apr-Jun
    2: {"start_month": 7, "end_month": 9},  # Q2: Jul-Sep
    3: {"start_month": 10, "end_month": 12},  # Q3: Oct-Dec
    4: {"start_month": 1, "end_month": 3},  # Q4: Jan-Mar
}


def get_india_fy_quarter(target_date: date) -> int:
    """Get India FY quarter (1-4) for a given date"""
    month = target_date.month
    if 4 <= month <= 6:
        return 1
    elif 7 <= month <= 9:
        return 2
    elif 10 <= month <= 12:
        return 3
    else:  # 1-3
        return 4


def get_india_fy_year(target_date: date) -> int:
    """
    Get India FY year for a date.
    FY 2024-25 starts Apr 1, 2024 and ends Mar 31, 2025.
    Returns the starting year (2024 for FY 2024-25).
    """
    if target_date.month >= 4:
        return target_date.year
    else:
        return target_date.year - 1


def get_quarter_end_date(target_date: date) -> date:
    """Get the quarter end date for India FY"""
    quarter = get_india_fy_quarter(target_date)
    quarter_info = INDIA_FY_QUARTERS[quarter]
    end_month = quarter_info["end_month"]

    # Determine the year for the quarter end
    if quarter == 4:  # Q4 is Jan-Mar
        year = target_date.year if target_date.month <= 3 else target_date.year + 1
    else:
        year = target_date.year if target_date.month >= 4 else target_date.year

    # Get last day of the end month
    _, last_day = monthrange(year, end_month)
    return date(year, end_month, last_day)


def calculate_due_date(due_date_rule: dict, period_end: date) -> date:
    """
    Parse due_date_rule JSONB and calculate actual due date.

    Supported rule types:
    - monthly: {"type": "monthly", "day": 11, "offset_days": 0}
    - quarterly: {"type": "quarterly", "offset_days": 31}
    - annual: {"type": "annual", "month": 9, "day": 30, "offset_days": 0}
    - fixed_date: {"type": "fixed_date", "month": 6, "day": 15}
    - event_based: {"type": "event_based", "offset_days": 30}

    Args:
        due_date_rule: JSONB rule configuration
        period_end: The end date of the compliance period

    Returns:
        Calculated due date
    """
    rule_type = due_date_rule.get("type", "monthly")
    offset_days = due_date_rule.get("offset_days", 0)

    if rule_type == "monthly":
        # Due on specific day of next month after period_end
        day = due_date_rule.get("day", 1)
        next_month = period_end.month + 1
        year = period_end.year
        if next_month > 12:
            next_month = 1
            year += 1
        # Handle edge case: day doesn't exist in month (e.g., day 31 in Feb)
        _, max_day = monthrange(year, next_month)
        actual_day = min(day, max_day)
        due = date(year, next_month, actual_day)
        return due + timedelta(days=offset_days)

    elif rule_type == "quarterly":
        # Due X days after quarter end
        quarter_end = get_quarter_end_date(period_end)
        return quarter_end + timedelta(days=offset_days)

    elif rule_type == "annual":
        # Due on specific month/day
        month = due_date_rule.get("month", 12)
        day = due_date_rule.get("day", 31)
        fy_year = get_india_fy_year(period_end)

        # Annual returns are typically due in the next FY
        # If month is Apr-Dec, use fy_year; if Jan-Mar, use fy_year + 1
        if month >= 4:
            year = fy_year
        else:
            year = fy_year + 1

        _, max_day = monthrange(year, month)
        actual_day = min(day, max_day)
        return date(year, month, actual_day) + timedelta(days=offset_days)

    elif rule_type == "fixed_date":
        # Same date every year
        month = due_date_rule.get("month", 12)
        day = due_date_rule.get("day", 31)
        year = period_end.year

        # If fixed date is before period_end in the year, use next year
        target = date(year, month, min(day, monthrange(year, month)[1]))
        if target <= period_end:
            year += 1
            target = date(year, month, min(day, monthrange(year, month)[1]))

        return target

    elif rule_type == "event_based":
        # Event-based: due X days after the event (period_end represents event date)
        return period_end + timedelta(days=offset_days)

    else:
        # Default: period end + offset
        return period_end + timedelta(days=offset_days)


def calculate_period_for_frequency(frequency: str, target_date: date) -> tuple[date, date]:
    """
    Calculate period_start and period_end for a given frequency.
    Uses India FY (Apr-Mar) for quarterly and annual.

    Args:
        frequency: Monthly, Quarterly, Annual, Event-based
        target_date: Reference date to calculate period for

    Returns:
        Tuple of (period_start, period_end)
    """
    if frequency == "Monthly":
        # First to last day of the month
        period_start = date(target_date.year, target_date.month, 1)
        _, last_day = monthrange(target_date.year, target_date.month)
        period_end = date(target_date.year, target_date.month, last_day)

    elif frequency == "Quarterly":
        # India FY quarters
        quarter = get_india_fy_quarter(target_date)
        quarter_info = INDIA_FY_QUARTERS[quarter]

        start_month = quarter_info["start_month"]
        end_month = quarter_info["end_month"]

        # Handle year transitions
        if quarter == 4:  # Q4 is Jan-Mar
            year = target_date.year if target_date.month <= 3 else target_date.year + 1
        else:
            year = target_date.year if target_date.month >= 4 else target_date.year

        period_start = date(year, start_month, 1)
        _, last_day = monthrange(year, end_month)
        period_end = date(year, end_month, last_day)

    elif frequency == "Annual":
        # India FY: Apr 1 to Mar 31
        fy_year = get_india_fy_year(target_date)
        period_start = date(fy_year, 4, 1)
        period_end = date(fy_year + 1, 3, 31)

    elif frequency == "Event-based":
        # For event-based, period is the event date itself
        period_start = target_date
        period_end = target_date

    else:
        # Default to monthly
        period_start = date(target_date.year, target_date.month, 1)
        _, last_day = monthrange(target_date.year, target_date.month)
        period_end = date(target_date.year, target_date.month, last_day)

    return period_start, period_end


def generate_instances_for_period(
    db: Session, tenant_id: UUID, period_start: date, period_end: date, created_by: Optional[UUID] = None
) -> list[ComplianceInstance]:
    """
    Generate compliance instances from active masters for all entities.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        period_start: Start of period to generate instances for
        period_end: End of period to generate instances for
        created_by: User UUID who triggered generation (for audit)

    Returns:
        List of created ComplianceInstance objects
    """
    created_instances = []

    # Get all active entities for tenant
    entities = db.query(Entity).filter(Entity.tenant_id == tenant_id, Entity.status == "active").all()

    if not entities:
        return created_instances

    # Get all active compliance masters (system templates + tenant-specific)
    masters = (
        db.query(ComplianceMaster)
        .filter(
            ComplianceMaster.is_active is True,
            or_(
                ComplianceMaster.tenant_id is None,  # System templates
                ComplianceMaster.tenant_id == tenant_id,  # Tenant-specific
            ),
        )
        .all()
    )

    for master in masters:
        # Skip event-based - those are created manually
        if master.frequency == "Event-based":
            continue

        # Calculate the period for this frequency
        master_period_start, master_period_end = calculate_period_for_frequency(master.frequency, period_end)

        # Check if this period falls within our target range
        if master_period_end < period_start or master_period_start > period_end:
            continue

        # Calculate due date
        due_date = calculate_due_date(master.due_date_rule, master_period_end)

        for entity in entities:
            # Check if instance already exists (unique constraint)
            existing = (
                db.query(ComplianceInstance)
                .filter(
                    ComplianceInstance.compliance_master_id == master.id,
                    ComplianceInstance.entity_id == entity.id,
                    ComplianceInstance.period_start == master_period_start,
                    ComplianceInstance.period_end == master_period_end,
                )
                .first()
            )

            if existing:
                continue

            # Create new instance
            instance = ComplianceInstance(
                tenant_id=tenant_id,
                compliance_master_id=master.id,
                entity_id=entity.id,
                period_start=master_period_start,
                period_end=master_period_end,
                due_date=due_date,
                status="Not Started",
                rag_status="Green",
                created_by=created_by,
                updated_by=created_by,
            )

            db.add(instance)
            created_instances.append(instance)

    db.commit()

    # Refresh to get IDs
    for instance in created_instances:
        db.refresh(instance)

    return created_instances


def calculate_rag_status(instance: ComplianceInstance, today: Optional[date] = None) -> str:
    """
    Calculate RAG status for a compliance instance.

    Rules:
    - GREEN: due_date > 7 days away AND status not blocked/overdue AND no blockers
    - AMBER: due_date <= 7 days OR dependencies pending OR evidence rejected
    - RED: overdue (due_date < today and not completed) OR critical blockers

    Args:
        instance: ComplianceInstance to calculate status for
        today: Reference date (defaults to today)

    Returns:
        "Green", "Amber", or "Red"
    """
    if today is None:
        today = date.today()

    # If completed, keep as green
    if instance.status == "Completed":
        return "Green"

    # Calculate days until due
    days_until_due = (instance.due_date - today).days

    # RED conditions
    if days_until_due < 0:  # Overdue
        return "Red"

    if instance.status in ["Blocked", "Overdue"]:
        return "Red"

    if instance.blocking_compliance_instance_id:
        # Check if blocking instance is still not completed
        if instance.blocking_instance and instance.blocking_instance.status != "Completed":
            return "Red"

    # AMBER conditions
    if days_until_due <= 7:
        return "Amber"

    # Check for pending dependencies (blocking instance not completed)
    if instance.blocking_compliance_instance_id:
        return "Amber"

    # GREEN - on track
    return "Green"


def calculate_rag_status_with_evidence(db: Session, instance: ComplianceInstance, today: Optional[date] = None) -> str:
    """
    Calculate RAG status including evidence rejection check.

    Args:
        db: Database session
        instance: ComplianceInstance to calculate status for
        today: Reference date (defaults to today)

    Returns:
        "Green", "Amber", or "Red"
    """
    # Get base RAG status
    base_status = calculate_rag_status(instance, today)

    if base_status == "Red":
        return "Red"

    # Check for rejected evidence (makes it Amber)
    rejected_evidence = (
        db.query(Evidence)
        .filter(Evidence.compliance_instance_id == instance.id, Evidence.approval_status == "Rejected")
        .first()
    )

    if rejected_evidence:
        return "Amber" if base_status == "Green" else base_status

    return base_status


def recalculate_rag_for_tenant(db: Session, tenant_id: UUID, today: Optional[date] = None) -> int:
    """
    Recalculate RAG status for all non-completed instances in a tenant.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        today: Reference date (defaults to today)

    Returns:
        Count of updated instances
    """
    if today is None:
        today = date.today()

    # Get all non-completed instances
    instances = (
        db.query(ComplianceInstance)
        .filter(ComplianceInstance.tenant_id == tenant_id, ComplianceInstance.status != "Completed")
        .all()
    )

    updated_count = 0

    for instance in instances:
        new_rag = calculate_rag_status_with_evidence(db, instance, today)

        if instance.rag_status != new_rag:
            instance.rag_status = new_rag
            updated_count += 1

    if updated_count > 0:
        db.commit()

    return updated_count


def check_dependencies_met(db: Session, instance: ComplianceInstance) -> tuple[bool, list[str]]:
    """
    Check if all dependencies for a compliance instance are met.

    Args:
        db: Database session
        instance: ComplianceInstance to check

    Returns:
        Tuple of (all_met: bool, blocking_codes: list of blocking compliance codes)
    """
    blocking_codes = []

    # Check direct blocking instance
    if instance.blocking_compliance_instance_id:
        blocking = instance.blocking_instance
        if blocking and blocking.status != "Completed":
            master = blocking.compliance_master
            if master:
                blocking_codes.append(master.compliance_code)

    # Check dependencies defined in master
    if instance.compliance_master and instance.compliance_master.dependencies:
        dependencies = instance.compliance_master.dependencies
        if isinstance(dependencies, list):
            for dep_code in dependencies:
                # Find instance of this dependency for same entity and overlapping period
                dep_instance = (
                    db.query(ComplianceInstance)
                    .join(ComplianceMaster)
                    .filter(
                        ComplianceMaster.compliance_code == dep_code,
                        ComplianceInstance.entity_id == instance.entity_id,
                        ComplianceInstance.status != "Completed",
                        # Period overlap check
                        ComplianceInstance.period_start <= instance.period_end,
                        ComplianceInstance.period_end >= instance.period_start,
                    )
                    .first()
                )

                if dep_instance:
                    blocking_codes.append(dep_code)

    return (len(blocking_codes) == 0, blocking_codes)


def get_pending_instances_for_entity(
    db: Session, entity_id: UUID, include_completed: bool = False
) -> list[ComplianceInstance]:
    """
    Get all pending (non-completed) instances for an entity.

    Args:
        db: Database session
        entity_id: Entity UUID
        include_completed: Whether to include completed instances

    Returns:
        List of ComplianceInstance objects
    """
    query = db.query(ComplianceInstance).filter(ComplianceInstance.entity_id == entity_id)

    if not include_completed:
        query = query.filter(ComplianceInstance.status != "Completed")

    return query.order_by(ComplianceInstance.due_date).all()


def get_overdue_instances(db: Session, tenant_id: UUID, today: Optional[date] = None) -> list[ComplianceInstance]:
    """
    Get all overdue instances for a tenant.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        today: Reference date (defaults to today)

    Returns:
        List of overdue ComplianceInstance objects
    """
    if today is None:
        today = date.today()

    return (
        db.query(ComplianceInstance)
        .filter(
            ComplianceInstance.tenant_id == tenant_id,
            ComplianceInstance.status != "Completed",
            ComplianceInstance.due_date < today,
        )
        .order_by(ComplianceInstance.due_date)
        .all()
    )


def get_upcoming_instances(
    db: Session, tenant_id: UUID, days: int = 7, today: Optional[date] = None
) -> list[ComplianceInstance]:
    """
    Get instances due within the next X days.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        days: Number of days to look ahead
        today: Reference date (defaults to today)

    Returns:
        List of upcoming ComplianceInstance objects
    """
    if today is None:
        today = date.today()

    end_date = today + timedelta(days=days)

    return (
        db.query(ComplianceInstance)
        .filter(
            ComplianceInstance.tenant_id == tenant_id,
            ComplianceInstance.status != "Completed",
            ComplianceInstance.due_date >= today,
            ComplianceInstance.due_date <= end_date,
        )
        .order_by(ComplianceInstance.due_date)
        .all()
    )


def mark_instance_overdue(db: Session, tenant_id: UUID, today: Optional[date] = None) -> int:
    """
    Mark overdue instances with 'Overdue' status.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        today: Reference date (defaults to today)

    Returns:
        Count of instances marked as overdue
    """
    if today is None:
        today = date.today()

    # Get overdue instances that aren't already marked
    instances = (
        db.query(ComplianceInstance)
        .filter(
            ComplianceInstance.tenant_id == tenant_id,
            ComplianceInstance.status.notin_(["Completed", "Overdue"]),
            ComplianceInstance.due_date < today,
        )
        .all()
    )

    for instance in instances:
        instance.status = "Overdue"
        instance.rag_status = "Red"

    if instances:
        db.commit()

    return len(instances)
