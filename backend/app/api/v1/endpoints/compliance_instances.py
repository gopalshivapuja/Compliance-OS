"""
Compliance Instance management endpoints
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_tenant_id, get_current_user
from app.models import ComplianceInstance, ComplianceMaster, Entity, User
from app.schemas import (
    ComplianceInstanceResponse,
    ComplianceInstanceListResponse,
    ComplianceInstanceUpdate,
)
from app.services import check_entity_access, get_user_accessible_entities, log_action

router = APIRouter()


@router.get("/", response_model=ComplianceInstanceListResponse)
async def list_compliance_instances(
    entity_id: Optional[str] = Query(None, description="Filter by entity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    rag_status: Optional[str] = Query(None, description="Filter by RAG status"),
    owner_id: Optional[str] = Query(None, description="Filter by owner"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    List compliance instances for current tenant.
    User can only see instances for entities they have access to (RBAC).
    """
    # Get user's accessible entities (RBAC enforcement)
    accessible_entities = get_user_accessible_entities(
        db,
        user_id=UUID(current_user["user_id"]),
        tenant_id=UUID(tenant_id),
    )

    # Build base query
    query = (
        db.query(ComplianceInstance)
        .join(ComplianceMaster, ComplianceInstance.compliance_master_id == ComplianceMaster.id)
        .join(Entity, ComplianceInstance.entity_id == Entity.id)
        .outerjoin(User, ComplianceInstance.owner_user_id == User.id)
        .filter(
            ComplianceInstance.tenant_id == UUID(tenant_id),
            ComplianceInstance.entity_id.in_(accessible_entities),  # RBAC filter
        )
    )

    # Apply optional filters
    if entity_id:
        query = query.filter(ComplianceInstance.entity_id == UUID(entity_id))

    if status:
        query = query.filter(ComplianceInstance.status == status)

    if category:
        query = query.filter(ComplianceMaster.category == category)

    if rag_status:
        query = query.filter(ComplianceInstance.rag_status == rag_status)

    if owner_id:
        query = query.filter(ComplianceInstance.owner_user_id == UUID(owner_id))

    # Get total count
    total = query.count()

    # Apply pagination and get results
    instances = query.order_by(ComplianceInstance.due_date.desc()).offset(skip).limit(limit).all()

    # Convert to response models
    items = []
    for instance in instances:
        items.append(
            ComplianceInstanceResponse(
                compliance_instance_id=str(instance.id),
                compliance_master_id=str(instance.compliance_master_id),
                compliance_code=instance.compliance_master.compliance_code,
                compliance_name=instance.compliance_master.compliance_name,
                entity_id=str(instance.entity_id),
                entity_name=instance.entity.entity_name,
                entity_code=instance.entity.entity_code,
                category=instance.compliance_master.category,
                sub_category=instance.compliance_master.sub_category,
                frequency=instance.compliance_master.frequency,
                due_date=instance.due_date,
                status=instance.status,
                rag_status=instance.rag_status,
                period_start=instance.period_start,
                period_end=instance.period_end,
                owner_id=str(instance.owner_user_id) if instance.owner_user_id else None,
                owner_name=instance.owner.full_name if instance.owner else None,
                approver_id=str(instance.approver_user_id) if instance.approver_user_id else None,
                approver_name=instance.approver.full_name if instance.approver else None,
                filed_date=instance.filed_date,
                completion_date=instance.completion_date,
                completion_remarks=instance.completion_remarks,
                remarks=instance.remarks,
                meta_data=instance.meta_data,
                created_at=instance.created_at,
                updated_at=instance.updated_at,
                created_by=str(instance.created_by) if instance.created_by else None,
                updated_by=str(instance.updated_by) if instance.updated_by else None,
            )
        )

    return ComplianceInstanceListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{compliance_instance_id}", response_model=ComplianceInstanceResponse)
async def get_compliance_instance(
    compliance_instance_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    Get compliance instance by ID.
    Enforces RBAC - user must have access to the entity.
    """
    # Get instance
    instance = (
        db.query(ComplianceInstance)
        .join(ComplianceMaster, ComplianceInstance.compliance_master_id == ComplianceMaster.id)
        .join(Entity, ComplianceInstance.entity_id == Entity.id)
        .outerjoin(User, ComplianceInstance.owner_user_id == User.id)
        .filter(
            ComplianceInstance.id == UUID(compliance_instance_id),
            ComplianceInstance.tenant_id == UUID(tenant_id),
        )
        .first()
    )

    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance instance not found",
        )

    # Check entity access (RBAC)
    has_access = check_entity_access(
        db,
        user_id=UUID(current_user["user_id"]),
        entity_id=instance.entity_id,
        tenant_id=UUID(tenant_id),
    )

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this entity",
        )

    # Return response
    return ComplianceInstanceResponse(
        compliance_instance_id=str(instance.id),
        compliance_master_id=str(instance.compliance_master_id),
        compliance_code=instance.compliance_master.compliance_code,
        compliance_name=instance.compliance_master.compliance_name,
        entity_id=str(instance.entity_id),
        entity_name=instance.entity.entity_name,
        entity_code=instance.entity.entity_code,
        category=instance.compliance_master.category,
        sub_category=instance.compliance_master.sub_category,
        frequency=instance.compliance_master.frequency,
        due_date=instance.due_date,
        status=instance.status,
        rag_status=instance.rag_status,
        period_start=instance.period_start,
        period_end=instance.period_end,
        owner_id=str(instance.owner_user_id) if instance.owner_user_id else None,
        owner_name=instance.owner.full_name if instance.owner else None,
        approver_id=str(instance.approver_user_id) if instance.approver_user_id else None,
        approver_name=instance.approver.full_name if instance.approver else None,
        filed_date=instance.filed_date,
        completion_date=instance.completion_date,
        completion_remarks=instance.completion_remarks,
        remarks=instance.remarks,
        meta_data=instance.meta_data,
        created_at=instance.created_at,
        updated_at=instance.updated_at,
        created_by=str(instance.created_by) if instance.created_by else None,
        updated_by=str(instance.updated_by) if instance.updated_by else None,
    )


@router.post("/")
async def create_compliance_instance(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Create a new compliance instance (usually auto-generated).

    TODO: Implement creation logic
    """
    return {
        "message": "Create compliance instance endpoint - TODO: Implement",
        "tenant_id": tenant_id,
    }


@router.put("/{compliance_instance_id}", response_model=ComplianceInstanceResponse)
async def update_compliance_instance(
    compliance_instance_id: str,
    update_data: ComplianceInstanceUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    Update compliance instance (e.g., status, RAG, owner).
    Enforces RBAC and logs all changes to audit trail.
    """
    # Get instance
    instance = (
        db.query(ComplianceInstance)
        .join(ComplianceMaster, ComplianceInstance.compliance_master_id == ComplianceMaster.id)
        .join(Entity, ComplianceInstance.entity_id == Entity.id)
        .outerjoin(User, ComplianceInstance.owner_user_id == User.id)
        .filter(
            ComplianceInstance.id == UUID(compliance_instance_id),
            ComplianceInstance.tenant_id == UUID(tenant_id),
        )
        .first()
    )

    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance instance not found",
        )

    # Check entity access (RBAC)
    has_access = check_entity_access(
        db,
        user_id=UUID(current_user["user_id"]),
        entity_id=instance.entity_id,
        tenant_id=UUID(tenant_id),
    )

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this entity",
        )

    # Capture old values for audit log
    old_values = {
        "status": instance.status,
        "rag_status": instance.rag_status,
        "owner_user_id": str(instance.owner_user_id) if instance.owner_user_id else None,
        "approver_user_id": str(instance.approver_user_id) if instance.approver_user_id else None,
        "filed_date": str(instance.filed_date) if instance.filed_date else None,
        "completion_date": str(instance.completion_date) if instance.completion_date else None,
        "completion_remarks": instance.completion_remarks,
        "remarks": instance.remarks,
    }

    # Update fields if provided
    changes = []
    if update_data.status is not None:
        instance.status = update_data.status
        changes.append(f"status: {old_values['status']} → {update_data.status}")

    if update_data.rag_status is not None:
        instance.rag_status = update_data.rag_status
        changes.append(f"rag_status: {old_values['rag_status']} → {update_data.rag_status}")

    if update_data.owner_user_id is not None:
        instance.owner_user_id = UUID(update_data.owner_user_id)
        changes.append("owner changed")

    if update_data.approver_user_id is not None:
        instance.approver_user_id = UUID(update_data.approver_user_id)
        changes.append("approver changed")

    if update_data.filed_date is not None:
        instance.filed_date = update_data.filed_date
        changes.append(f"filed_date set to {update_data.filed_date}")

    if update_data.completion_date is not None:
        instance.completion_date = update_data.completion_date
        changes.append(f"completed on {update_data.completion_date}")

    if update_data.completion_remarks is not None:
        instance.completion_remarks = update_data.completion_remarks

    if update_data.remarks is not None:
        instance.remarks = update_data.remarks

    # Update audit fields
    instance.updated_by = UUID(current_user["user_id"])

    # Capture new values
    new_values = {
        "status": instance.status,
        "rag_status": instance.rag_status,
        "owner_user_id": str(instance.owner_user_id) if instance.owner_user_id else None,
        "approver_user_id": str(instance.approver_user_id) if instance.approver_user_id else None,
        "filed_date": str(instance.filed_date) if instance.filed_date else None,
        "completion_date": str(instance.completion_date) if instance.completion_date else None,
        "completion_remarks": instance.completion_remarks,
        "remarks": instance.remarks,
    }

    # Commit changes
    db.commit()
    db.refresh(instance)

    # Log to audit trail
    await log_action(
        db=db,
        tenant_id=UUID(tenant_id),
        user_id=UUID(current_user["user_id"]),
        action_type="UPDATE",
        resource_type="compliance_instance",
        resource_id=instance.id,
        old_values=old_values,
        new_values=new_values,
        change_summary=(
            f"Updated compliance instance: {', '.join(changes)}" if changes else "Updated compliance instance"
        ),
    )

    # Return updated instance
    return ComplianceInstanceResponse(
        compliance_instance_id=str(instance.id),
        compliance_master_id=str(instance.compliance_master_id),
        compliance_code=instance.compliance_master.compliance_code,
        compliance_name=instance.compliance_master.compliance_name,
        entity_id=str(instance.entity_id),
        entity_name=instance.entity.entity_name,
        entity_code=instance.entity.entity_code,
        category=instance.compliance_master.category,
        sub_category=instance.compliance_master.sub_category,
        frequency=instance.compliance_master.frequency,
        due_date=instance.due_date,
        status=instance.status,
        rag_status=instance.rag_status,
        period_start=instance.period_start,
        period_end=instance.period_end,
        owner_id=str(instance.owner_user_id) if instance.owner_user_id else None,
        owner_name=instance.owner.full_name if instance.owner else None,
        approver_id=str(instance.approver_user_id) if instance.approver_user_id else None,
        approver_name=instance.approver.full_name if instance.approver else None,
        filed_date=instance.filed_date,
        completion_date=instance.completion_date,
        completion_remarks=instance.completion_remarks,
        remarks=instance.remarks,
        meta_data=instance.meta_data,
        created_at=instance.created_at,
        updated_at=instance.updated_at,
        created_by=str(instance.created_by) if instance.created_by else None,
        updated_by=str(instance.updated_by) if instance.updated_by else None,
    )


@router.post("/{compliance_instance_id}/recalculate-status")
async def recalculate_status(
    compliance_instance_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Manually trigger status recalculation (Overdue, Blocked, etc.).

    TODO: Implement recalculation logic
    """
    return {
        "message": f"Recalculate status for {compliance_instance_id} - TODO: Implement",
        "tenant_id": tenant_id,
    }
