"""
Dashboard endpoints for aggregated views
"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_tenant_id
from app.models import ComplianceInstance, ComplianceMaster, Entity, User
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    RAGCounts,
    CategoryBreakdown,
    ComplianceInstanceSummary,
)

router = APIRouter()


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Get executive control tower overview with RAG status and counts.

    Returns:
    - Total compliance instances
    - RAG status distribution (Green, Amber, Red)
    - Overdue count
    - Upcoming count (next 7 days)
    - Category breakdown with RAG distribution
    """
    today = date.today()
    upcoming_threshold = today + timedelta(days=7)

    # Get total count
    total_compliances = (
        db.query(func.count(ComplianceInstance.id))
        .filter(ComplianceInstance.tenant_id == tenant_id)
        .scalar()
    )

    # Get RAG counts
    rag_counts_raw = (
        db.query(
            ComplianceInstance.rag_status,
            func.count(ComplianceInstance.id).label("count"),
        )
        .filter(ComplianceInstance.tenant_id == tenant_id)
        .group_by(ComplianceInstance.rag_status)
        .all()
    )

    rag_dict = {"green": 0, "amber": 0, "red": 0}
    for rag_status, count in rag_counts_raw:
        rag_dict[rag_status.lower()] = count

    # Get overdue count (due_date < today AND status NOT IN completed states)
    overdue_count = (
        db.query(func.count(ComplianceInstance.id))
        .filter(
            ComplianceInstance.tenant_id == tenant_id,
            ComplianceInstance.due_date < today,
            ComplianceInstance.status.notin_(["Completed", "Filed"]),
        )
        .scalar()
    )

    # Get upcoming count (due_date between today and today+7)
    upcoming_count = (
        db.query(func.count(ComplianceInstance.id))
        .filter(
            ComplianceInstance.tenant_id == tenant_id,
            ComplianceInstance.due_date >= today,
            ComplianceInstance.due_date <= upcoming_threshold,
            ComplianceInstance.status.notin_(["Completed", "Filed"]),
        )
        .scalar()
    )

    # Get category breakdown with RAG distribution
    category_breakdown_raw = (
        db.query(
            ComplianceMaster.category,
            ComplianceInstance.rag_status,
            func.count(ComplianceInstance.id).label("count"),
        )
        .join(
            ComplianceMaster,
            ComplianceInstance.compliance_master_id == ComplianceMaster.id,
        )
        .filter(ComplianceInstance.tenant_id == tenant_id)
        .group_by(ComplianceMaster.category, ComplianceInstance.rag_status)
        .all()
    )

    # Transform into CategoryBreakdown objects
    category_dict = {}
    for category, rag_status, count in category_breakdown_raw:
        if category not in category_dict:
            category_dict[category] = {"green": 0, "amber": 0, "red": 0, "total": 0}
        category_dict[category][rag_status.lower()] = count
        category_dict[category]["total"] += count

    category_breakdown = [
        CategoryBreakdown(
            category=category,
            green=data["green"],
            amber=data["amber"],
            red=data["red"],
            total=data["total"],
        )
        for category, data in category_dict.items()
    ]

    return DashboardOverviewResponse(
        total_compliances=total_compliances or 0,
        rag_counts=RAGCounts(**rag_dict),
        overdue_count=overdue_count or 0,
        upcoming_count=upcoming_count or 0,
        category_breakdown=category_breakdown,
    )


@router.get("/overdue", response_model=list[ComplianceInstanceSummary])
async def get_overdue_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Get overdue compliance instances (due_date < today, status not completed).
    Ordered by due_date ASC (most overdue first).
    """
    today = date.today()

    instances = (
        db.query(
            ComplianceInstance.id.label("compliance_instance_id"),
            ComplianceMaster.compliance_name,
            ComplianceMaster.compliance_code,
            Entity.entity_name,
            Entity.entity_code,
            ComplianceMaster.category,
            ComplianceMaster.sub_category,
            ComplianceMaster.frequency,
            ComplianceInstance.due_date,
            ComplianceInstance.rag_status,
            ComplianceInstance.status,
            ComplianceInstance.period_start,
            ComplianceInstance.period_end,
            User.first_name.label("owner_first_name"),
            User.last_name.label("owner_last_name"),
        )
        .join(
            ComplianceMaster,
            ComplianceInstance.compliance_master_id == ComplianceMaster.id,
        )
        .join(Entity, ComplianceInstance.entity_id == Entity.id)
        .outerjoin(User, ComplianceInstance.owner_user_id == User.id)
        .filter(
            ComplianceInstance.tenant_id == tenant_id,
            ComplianceInstance.due_date < today,
            ComplianceInstance.status.notin_(["Completed", "Filed"]),
        )
        .order_by(ComplianceInstance.due_date.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for inst in instances:
        owner_name = None
        if inst.owner_first_name and inst.owner_last_name:
            owner_name = f"{inst.owner_first_name} {inst.owner_last_name}"

        days_overdue = (today - inst.due_date).days

        result.append(
            ComplianceInstanceSummary(
                compliance_instance_id=str(inst.compliance_instance_id),
                compliance_name=inst.compliance_name,
                compliance_code=inst.compliance_code,
                entity_name=inst.entity_name,
                entity_code=inst.entity_code,
                category=inst.category,
                sub_category=inst.sub_category,
                frequency=inst.frequency,
                due_date=inst.due_date,
                rag_status=inst.rag_status,
                status=inst.status,
                period_start=inst.period_start,
                period_end=inst.period_end,
                owner_name=owner_name,
                days_overdue=days_overdue,
            )
        )

    return result


@router.get("/upcoming", response_model=list[ComplianceInstanceSummary])
async def get_upcoming_items(
    days: int = Query(7, ge=1, le=30, description="Number of days ahead"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Get upcoming compliance instances due in the next N days.
    Ordered by due_date ASC (soonest first).
    """
    today = date.today()
    upcoming_threshold = today + timedelta(days=days)

    instances = (
        db.query(
            ComplianceInstance.id.label("compliance_instance_id"),
            ComplianceMaster.compliance_name,
            ComplianceMaster.compliance_code,
            Entity.entity_name,
            Entity.entity_code,
            ComplianceMaster.category,
            ComplianceMaster.sub_category,
            ComplianceMaster.frequency,
            ComplianceInstance.due_date,
            ComplianceInstance.rag_status,
            ComplianceInstance.status,
            ComplianceInstance.period_start,
            ComplianceInstance.period_end,
            User.first_name.label("owner_first_name"),
            User.last_name.label("owner_last_name"),
        )
        .join(
            ComplianceMaster,
            ComplianceInstance.compliance_master_id == ComplianceMaster.id,
        )
        .join(Entity, ComplianceInstance.entity_id == Entity.id)
        .outerjoin(User, ComplianceInstance.owner_user_id == User.id)
        .filter(
            ComplianceInstance.tenant_id == tenant_id,
            ComplianceInstance.due_date >= today,
            ComplianceInstance.due_date <= upcoming_threshold,
            ComplianceInstance.status.notin_(["Completed", "Filed"]),
        )
        .order_by(ComplianceInstance.due_date.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for inst in instances:
        owner_name = None
        if inst.owner_first_name and inst.owner_last_name:
            owner_name = f"{inst.owner_first_name} {inst.owner_last_name}"

        days_until_due = (inst.due_date - today).days

        result.append(
            ComplianceInstanceSummary(
                compliance_instance_id=str(inst.compliance_instance_id),
                compliance_name=inst.compliance_name,
                compliance_code=inst.compliance_code,
                entity_name=inst.entity_name,
                entity_code=inst.entity_code,
                category=inst.category,
                sub_category=inst.sub_category,
                frequency=inst.frequency,
                due_date=inst.due_date,
                rag_status=inst.rag_status,
                status=inst.status,
                period_start=inst.period_start,
                period_end=inst.period_end,
                owner_name=owner_name,
                days_overdue=-days_until_due,  # Negative means not overdue yet
            )
        )

    return result


@router.get("/owner-heatmap")
async def get_owner_heatmap(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Get compliance load by owner (heatmap data).

    TODO: Implement owner heatmap logic
    """
    return {
        "message": "Owner heatmap endpoint - TODO: Implement",
        "tenant_id": tenant_id,
    }


@router.get("/category-breakdown", response_model=list[CategoryBreakdown])
async def get_category_breakdown(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Get RAG status breakdown by category with counts.
    Returns list of categories with Green, Amber, Red counts.
    """
    category_breakdown_raw = (
        db.query(
            ComplianceMaster.category,
            ComplianceInstance.rag_status,
            func.count(ComplianceInstance.id).label("count"),
        )
        .join(
            ComplianceMaster,
            ComplianceInstance.compliance_master_id == ComplianceMaster.id,
        )
        .filter(ComplianceInstance.tenant_id == tenant_id)
        .group_by(ComplianceMaster.category, ComplianceInstance.rag_status)
        .all()
    )

    # Transform into CategoryBreakdown objects
    category_dict = {}
    for category, rag_status, count in category_breakdown_raw:
        if category not in category_dict:
            category_dict[category] = {"green": 0, "amber": 0, "red": 0, "total": 0}
        category_dict[category][rag_status.lower()] = count
        category_dict[category]["total"] += count

    result = [
        CategoryBreakdown(
            category=category,
            green=data["green"],
            amber=data["amber"],
            red=data["red"],
            total=data["total"],
        )
        for category, data in category_dict.items()
    ]

    return result
