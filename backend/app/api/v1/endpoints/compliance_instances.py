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
    ComplianceInstanceCreate,
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


@router.post("/", response_model=ComplianceInstanceResponse, status_code=status.HTTP_201_CREATED)
async def create_compliance_instance(
    instance_data: ComplianceInstanceCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new compliance instance.

    Args:
        instance_data: Compliance instance creation data
        db: Database session
        tenant_id: Current tenant ID
        current_user: Current authenticated user

    Returns:
        ComplianceInstanceResponse: Created compliance instance

    Raises:
        HTTPException 404: If compliance master or entity not found
        HTTPException 403: If user doesn't have access to entity
        HTTPException 400: If duplicate period exists
    """
    tenant_uuid = UUID(tenant_id)
    user_id = UUID(current_user["user_id"])

    # Validate compliance master exists
    master = (
        db.query(ComplianceMaster)
        .filter(
            ComplianceMaster.id == UUID(instance_data.compliance_master_id),
        )
        .first()
    )
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance master '{instance_data.compliance_master_id}' not found",
        )

    # Validate entity exists and belongs to tenant
    entity = (
        db.query(Entity)
        .filter(
            Entity.id == UUID(instance_data.entity_id),
            Entity.tenant_id == tenant_uuid,
        )
        .first()
    )
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Entity '{instance_data.entity_id}' not found"
        )

    # Check entity access (admins can access all, others need explicit access)
    user_roles = current_user.get("roles", [])
    is_admin = "SYSTEM_ADMIN" in user_roles or "TENANT_ADMIN" in user_roles
    if not is_admin:
        has_access = check_entity_access(
            db=db,
            user_id=user_id,
            entity_id=UUID(instance_data.entity_id),
            tenant_id=tenant_uuid,
        )
        if not has_access:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this entity")

    # Check for duplicate period
    existing = (
        db.query(ComplianceInstance)
        .filter(
            ComplianceInstance.compliance_master_id == UUID(instance_data.compliance_master_id),
            ComplianceInstance.entity_id == UUID(instance_data.entity_id),
            ComplianceInstance.period_start == instance_data.period_start,
            ComplianceInstance.period_end == instance_data.period_end,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="A compliance instance for this period already exists"
        )

    # Create instance
    instance = ComplianceInstance(
        tenant_id=tenant_uuid,
        compliance_master_id=UUID(instance_data.compliance_master_id),
        entity_id=UUID(instance_data.entity_id),
        period_start=instance_data.period_start,
        period_end=instance_data.period_end,
        due_date=instance_data.due_date,
        status=instance_data.status or "Not Started",
        rag_status=instance_data.rag_status or "Green",
        owner_user_id=UUID(instance_data.owner_user_id) if instance_data.owner_user_id else None,
        approver_user_id=UUID(instance_data.approver_user_id) if instance_data.approver_user_id else None,
        remarks=instance_data.remarks,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(instance)
    db.flush()

    # Log action
    await log_action(
        db=db,
        user_id=str(user_id),
        tenant_id=tenant_id,
        action_type="CREATE",
        resource_type="compliance_instance",
        resource_id=str(instance.id),
        new_values={
            "compliance_master_id": instance_data.compliance_master_id,
            "entity_id": instance_data.entity_id,
            "period_start": str(instance_data.period_start),
            "period_end": str(instance_data.period_end),
            "due_date": str(instance_data.due_date),
            "status": instance.status,
        },
    )

    db.commit()
    db.refresh(instance)

    # Get owner and approver names
    owner_name = None
    approver_name = None
    if instance.owner_user_id:
        owner = db.query(User).filter(User.id == instance.owner_user_id).first()
        if owner:
            owner_name = f"{owner.first_name} {owner.last_name}"
    if instance.approver_user_id:
        approver = db.query(User).filter(User.id == instance.approver_user_id).first()
        if approver:
            approver_name = f"{approver.first_name} {approver.last_name}"

    # Return response
    return ComplianceInstanceResponse(
        compliance_instance_id=str(instance.id),
        compliance_master_id=str(instance.compliance_master_id),
        compliance_code=master.compliance_code,
        compliance_name=master.compliance_name,
        entity_id=str(instance.entity_id),
        entity_name=entity.entity_name,
        entity_code=entity.entity_code,
        category=master.category,
        sub_category=master.sub_category,
        frequency=master.frequency,
        due_date=instance.due_date,
        status=instance.status,
        rag_status=instance.rag_status,
        period_start=instance.period_start,
        period_end=instance.period_end,
        owner_id=str(instance.owner_user_id) if instance.owner_user_id else None,
        owner_name=owner_name,
        approver_id=str(instance.approver_user_id) if instance.approver_user_id else None,
        approver_name=approver_name,
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


@router.post("/{compliance_instance_id}/recalculate-status", response_model=ComplianceInstanceResponse)
async def recalculate_status(
    compliance_instance_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    Manually trigger status recalculation (Overdue, Blocked, etc.).

    Recalculates RAG status based on:
    - Due date proximity
    - Overdue status
    - Blocking dependencies
    - Completion status
    """
    from datetime import date, timedelta

    tenant_uuid = UUID(tenant_id)
    instance_uuid = UUID(compliance_instance_id)
    user_id = UUID(current_user["user_id"])

    # Get instance with related data
    instance = (
        db.query(ComplianceInstance)
        .filter(
            ComplianceInstance.id == instance_uuid,
            ComplianceInstance.tenant_id == tenant_uuid,
        )
        .first()
    )

    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Compliance instance '{compliance_instance_id}' not found"
        )

    # Check entity access
    user_roles = current_user.get("roles", [])
    is_admin = "SYSTEM_ADMIN" in user_roles or "TENANT_ADMIN" in user_roles
    if not is_admin:
        has_access = check_entity_access(
            db=db,
            user_id=user_id,
            entity_id=instance.entity_id,
            tenant_id=tenant_uuid,
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this compliance instance"
            )

    # Get master and entity for response
    master = db.query(ComplianceMaster).filter(ComplianceMaster.id == instance.compliance_master_id).first()
    entity = db.query(Entity).filter(Entity.id == instance.entity_id).first()

    # Calculate new RAG status
    today = date.today()
    old_rag = instance.rag_status
    old_status = instance.status

    # Check for blocking dependencies first (highest priority after completion)
    has_blocking_dependency = False

    # Check direct blocking instance reference
    if instance.blocking_compliance_instance_id:
        blocking_instance = (
            db.query(ComplianceInstance)
            .filter(
                ComplianceInstance.id == instance.blocking_compliance_instance_id,
                ComplianceInstance.status.notin_(["Completed", "Filed"]),
            )
            .first()
        )
        if blocking_instance:
            has_blocking_dependency = True

    # Check master dependencies (compliance codes)
    if not has_blocking_dependency and master and master.dependencies:
        for dep_code in master.dependencies:
            dep_master = db.query(ComplianceMaster).filter(ComplianceMaster.compliance_code == dep_code).first()
            if dep_master:
                # Check if dependency instance exists and is not completed
                dep_instance = (
                    db.query(ComplianceInstance)
                    .filter(
                        ComplianceInstance.compliance_master_id == dep_master.id,
                        ComplianceInstance.entity_id == instance.entity_id,
                        ComplianceInstance.status.notin_(["Completed", "Filed"]),
                    )
                    .first()
                )
                if dep_instance:
                    # Has blocking dependency
                    has_blocking_dependency = True
                    break

    # Completed/Filed instances are always Green
    if instance.status in ["Completed", "Filed"]:
        instance.rag_status = "Green"
    # Blocking dependencies make it Amber and status Blocked
    elif has_blocking_dependency:
        instance.rag_status = "Amber"
        instance.status = "Blocked"
    # Overdue instances are Red
    elif instance.due_date < today:
        instance.rag_status = "Red"
        instance.status = "Overdue"
    # Due within 3 days is Red (critical)
    elif instance.due_date <= today + timedelta(days=3):
        instance.rag_status = "Red"
    # Due within 4-7 days is Amber
    elif instance.due_date <= today + timedelta(days=7):
        instance.rag_status = "Amber"
    # Otherwise Green
    else:
        instance.rag_status = "Green"

    instance.updated_by = user_id
    db.commit()
    db.refresh(instance)

    # Log if status changed
    if old_rag != instance.rag_status or old_status != instance.status:
        await log_action(
            db=db,
            user_id=str(user_id),
            tenant_id=tenant_id,
            action_type="UPDATE",
            resource_type="compliance_instance",
            resource_id=str(instance.id),
            old_values={"rag_status": old_rag, "status": old_status},
            new_values={"rag_status": instance.rag_status, "status": instance.status},
        )

    # Get owner and approver names
    owner_name = None
    approver_name = None
    if instance.owner_user_id:
        owner = db.query(User).filter(User.id == instance.owner_user_id).first()
        if owner:
            owner_name = f"{owner.first_name} {owner.last_name}"
    if instance.approver_user_id:
        approver = db.query(User).filter(User.id == instance.approver_user_id).first()
        if approver:
            approver_name = f"{approver.first_name} {approver.last_name}"

    return ComplianceInstanceResponse(
        compliance_instance_id=str(instance.id),
        compliance_master_id=str(instance.compliance_master_id),
        compliance_code=master.compliance_code if master else "",
        compliance_name=master.compliance_name if master else "",
        entity_id=str(instance.entity_id),
        entity_name=entity.entity_name if entity else "",
        entity_code=entity.entity_code if entity else "",
        category=master.category if master else "",
        sub_category=master.sub_category if master else None,
        frequency=master.frequency if master else "",
        due_date=instance.due_date,
        status=instance.status,
        rag_status=instance.rag_status,
        period_start=instance.period_start,
        period_end=instance.period_end,
        owner_id=str(instance.owner_user_id) if instance.owner_user_id else None,
        owner_name=owner_name,
        approver_id=str(instance.approver_user_id) if instance.approver_user_id else None,
        approver_name=approver_name,
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
