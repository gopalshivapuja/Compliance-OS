"""
Compliance Master management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_tenant_id
from app.schemas import (
    ComplianceMasterCreate,
    ComplianceMasterUpdate,
    ComplianceMasterResponse,
    ComplianceMasterListResponse,
    ComplianceMasterBulkImportRequest,
    ComplianceMasterBulkImportResponse,
)
from app.models import ComplianceMaster, ComplianceInstance
from app.services import log_action, check_role_permission

router = APIRouter()


def require_master_admin(current_user: dict, is_template: bool = False) -> dict:
    """
    Require user to have compliance master management permissions.

    Args:
        current_user: Current authenticated user from JWT
        is_template: If True, only system admins can manage

    Returns:
        dict: User data if authorized

    Raises:
        HTTPException 403: If user is not authorized
    """
    user_roles = current_user.get("roles", [])
    is_system_admin = current_user.get("is_system_admin", False)

    # System templates can only be managed by system admins
    if is_template and not is_system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only system administrators can manage system templates",
        )

    # Tenant admins can manage tenant-specific masters
    admin_roles = ["System Admin", "Tenant Admin", "admin"]
    if is_system_admin or check_role_permission(user_roles, admin_roles):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only administrators can manage compliance masters",
    )


@router.post("/", response_model=ComplianceMasterResponse, status_code=status.HTTP_201_CREATED)
async def create_compliance_master(
    master_data: ComplianceMasterCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new compliance master.

    System admins can create system templates (is_template=True).
    Tenant admins can create tenant-specific masters.

    Args:
        master_data: Compliance master creation data
        db: Database session
        tenant_id: Current tenant ID from JWT
        current_user: Current authenticated user

    Returns:
        ComplianceMasterResponse: Created compliance master details

    Raises:
        HTTPException 403: If user is not authorized
        HTTPException 400: If compliance code already exists
    """
    is_template = master_data.is_template or False
    require_master_admin(current_user, is_template)

    # Determine tenant_id based on template flag
    target_tenant_id = None if is_template else UUID(tenant_id)

    # Check for duplicate compliance code within scope
    existing = (
        db.query(ComplianceMaster)
        .filter(
            ComplianceMaster.compliance_code == master_data.compliance_code,
            ComplianceMaster.tenant_id == target_tenant_id,
        )
        .first()
    )

    if existing:
        scope = "system templates" if is_template else "this tenant"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Compliance code '{master_data.compliance_code}' already exists in {scope}",
        )

    # Create new compliance master
    master = ComplianceMaster(
        tenant_id=target_tenant_id,
        compliance_code=master_data.compliance_code,
        compliance_name=master_data.compliance_name,
        description=master_data.description,
        category=master_data.category,
        sub_category=master_data.sub_category,
        frequency=master_data.frequency,
        due_date_rule=master_data.due_date_rule,
        owner_role_code=master_data.owner_role_code,
        approver_role_code=master_data.approver_role_code,
        dependencies=master_data.dependencies,
        workflow_config=master_data.workflow_config,
        authority=master_data.authority,
        penalty_details=master_data.penalty_details,
        reference_links=master_data.reference_links,
        meta_data=master_data.meta_data,
        is_active=True,
        is_template=is_template,
        created_by=UUID(current_user["user_id"]),
        updated_by=UUID(current_user["user_id"]),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(master)
    db.flush()

    # Log action
    await log_action(
        db=db,
        user_id=current_user["user_id"],
        tenant_id=tenant_id,
        action_type="CREATE",
        resource_type="compliance_master",
        resource_id=str(master.id),
        new_values={
            "compliance_code": master.compliance_code,
            "compliance_name": master.compliance_name,
            "category": master.category,
            "frequency": master.frequency,
            "is_template": master.is_template,
        },
    )

    db.commit()
    db.refresh(master)

    return ComplianceMasterResponse(
        id=str(master.id),
        tenant_id=str(master.tenant_id) if master.tenant_id else None,
        compliance_code=master.compliance_code,
        compliance_name=master.compliance_name,
        description=master.description,
        category=master.category,
        sub_category=master.sub_category,
        frequency=master.frequency,
        due_date_rule=master.due_date_rule,
        owner_role_code=master.owner_role_code,
        approver_role_code=master.approver_role_code,
        dependencies=master.dependencies,
        workflow_config=master.workflow_config,
        is_active=master.is_active,
        is_template=master.is_template,
        authority=master.authority,
        penalty_details=master.penalty_details,
        reference_links=master.reference_links,
        meta_data=master.meta_data,
        created_at=master.created_at,
        updated_at=master.updated_at,
        created_by=str(master.created_by) if master.created_by else None,
        updated_by=str(master.updated_by) if master.updated_by else None,
        instances_count=0,
    )


@router.get("/", response_model=ComplianceMasterListResponse, status_code=status.HTTP_200_OK)
async def list_compliance_masters(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    frequency: Optional[str] = Query(None, description="Filter by frequency"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_template: Optional[bool] = Query(None, description="Filter by template status"),
    search: Optional[str] = Query(None, description="Search in name or code"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    List compliance masters with pagination.

    Returns both system templates (tenant_id=NULL) and tenant-specific masters.

    Args:
        skip: Number of records to skip (for pagination)
        limit: Number of records to return (max 100)
        category: Filter by category
        frequency: Filter by frequency
        is_active: Filter by active status
        is_template: Filter by template status
        search: Search query for name or code
        db: Database session
        tenant_id: Current tenant ID from JWT
        current_user: Current authenticated user

    Returns:
        ComplianceMasterListResponse: Paginated list of compliance masters
    """
    # Build query - include system templates (NULL tenant_id) and tenant-specific
    query = db.query(ComplianceMaster).filter(
        or_(
            ComplianceMaster.tenant_id == None,  # noqa: E711
            ComplianceMaster.tenant_id == UUID(tenant_id),
        )
    )

    # Apply filters
    if category:
        query = query.filter(ComplianceMaster.category == category)

    if frequency:
        query = query.filter(ComplianceMaster.frequency == frequency)

    if is_active is not None:
        query = query.filter(ComplianceMaster.is_active == is_active)

    if is_template is not None:
        query = query.filter(ComplianceMaster.is_template == is_template)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                ComplianceMaster.compliance_name.ilike(search_term),
                ComplianceMaster.compliance_code.ilike(search_term),
            )
        )

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    masters = (
        query.order_by(ComplianceMaster.category, ComplianceMaster.compliance_code)
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Build response
    master_list = []
    for master in masters:
        instances_count = (
            db.query(func.count(ComplianceInstance.id))
            .filter(ComplianceInstance.compliance_master_id == master.id)
            .scalar()
        )

        master_list.append(
            ComplianceMasterResponse(
                id=str(master.id),
                tenant_id=str(master.tenant_id) if master.tenant_id else None,
                compliance_code=master.compliance_code,
                compliance_name=master.compliance_name,
                description=master.description,
                category=master.category,
                sub_category=master.sub_category,
                frequency=master.frequency,
                due_date_rule=master.due_date_rule,
                owner_role_code=master.owner_role_code,
                approver_role_code=master.approver_role_code,
                dependencies=master.dependencies,
                workflow_config=master.workflow_config,
                is_active=master.is_active,
                is_template=master.is_template,
                authority=master.authority,
                penalty_details=master.penalty_details,
                reference_links=master.reference_links,
                meta_data=master.meta_data,
                created_at=master.created_at,
                updated_at=master.updated_at,
                created_by=str(master.created_by) if master.created_by else None,
                updated_by=str(master.updated_by) if master.updated_by else None,
                instances_count=instances_count or 0,
            )
        )

    return ComplianceMasterListResponse(items=master_list, total=total, skip=skip, limit=limit)


@router.get("/{master_id}", response_model=ComplianceMasterResponse, status_code=status.HTTP_200_OK)
async def get_compliance_master(
    master_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    Get compliance master by ID.

    Can access system templates (NULL tenant_id) or tenant-specific masters.

    Args:
        master_id: Compliance master UUID
        db: Database session
        tenant_id: Current tenant ID from JWT
        current_user: Current authenticated user

    Returns:
        ComplianceMasterResponse: Compliance master details

    Raises:
        HTTPException 404: If master not found
        HTTPException 403: If accessing another tenant's master
    """
    master = db.query(ComplianceMaster).filter(ComplianceMaster.id == UUID(master_id)).first()

    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance master with ID '{master_id}' not found",
        )

    # Check access - can access templates or own tenant's masters
    if master.tenant_id is not None and str(master.tenant_id) != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access compliance masters from other tenants",
        )

    instances_count = (
        db.query(func.count(ComplianceInstance.id))
        .filter(ComplianceInstance.compliance_master_id == master.id)
        .scalar()
    )

    return ComplianceMasterResponse(
        id=str(master.id),
        tenant_id=str(master.tenant_id) if master.tenant_id else None,
        compliance_code=master.compliance_code,
        compliance_name=master.compliance_name,
        description=master.description,
        category=master.category,
        sub_category=master.sub_category,
        frequency=master.frequency,
        due_date_rule=master.due_date_rule,
        owner_role_code=master.owner_role_code,
        approver_role_code=master.approver_role_code,
        dependencies=master.dependencies,
        workflow_config=master.workflow_config,
        is_active=master.is_active,
        is_template=master.is_template,
        authority=master.authority,
        penalty_details=master.penalty_details,
        reference_links=master.reference_links,
        meta_data=master.meta_data,
        created_at=master.created_at,
        updated_at=master.updated_at,
        created_by=str(master.created_by) if master.created_by else None,
        updated_by=str(master.updated_by) if master.updated_by else None,
        instances_count=instances_count or 0,
    )


@router.put("/{master_id}", response_model=ComplianceMasterResponse, status_code=status.HTTP_200_OK)
async def update_compliance_master(
    master_id: str,
    master_data: ComplianceMasterUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    Update compliance master.

    System templates can only be updated by system admins.
    Tenant masters can be updated by tenant admins.

    Args:
        master_id: Compliance master UUID
        master_data: Compliance master update data
        db: Database session
        tenant_id: Current tenant ID from JWT
        current_user: Current authenticated user

    Returns:
        ComplianceMasterResponse: Updated compliance master details

    Raises:
        HTTPException 403: If user is not authorized
        HTTPException 404: If master not found
    """
    master = db.query(ComplianceMaster).filter(ComplianceMaster.id == UUID(master_id)).first()

    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance master with ID '{master_id}' not found",
        )

    # Check access
    if master.tenant_id is not None and str(master.tenant_id) != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot update compliance masters from other tenants",
        )

    # Enforce authorization
    require_master_admin(current_user, master.is_template)

    # Capture old values for audit log
    old_values = {}
    new_values = {}
    update_data = master_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None and hasattr(master, field):
            old_values[field] = getattr(master, field)
            setattr(master, field, value)
            new_values[field] = value

    # Update audit fields
    master.updated_by = UUID(current_user["user_id"])
    master.updated_at = datetime.utcnow()

    # Log action
    if new_values:
        await log_action(
            db=db,
            user_id=current_user["user_id"],
            tenant_id=tenant_id,
            action_type="UPDATE",
            resource_type="compliance_master",
            resource_id=str(master.id),
            old_values=old_values,
            new_values=new_values,
        )

    db.commit()
    db.refresh(master)

    instances_count = (
        db.query(func.count(ComplianceInstance.id))
        .filter(ComplianceInstance.compliance_master_id == master.id)
        .scalar()
    )

    return ComplianceMasterResponse(
        id=str(master.id),
        tenant_id=str(master.tenant_id) if master.tenant_id else None,
        compliance_code=master.compliance_code,
        compliance_name=master.compliance_name,
        description=master.description,
        category=master.category,
        sub_category=master.sub_category,
        frequency=master.frequency,
        due_date_rule=master.due_date_rule,
        owner_role_code=master.owner_role_code,
        approver_role_code=master.approver_role_code,
        dependencies=master.dependencies,
        workflow_config=master.workflow_config,
        is_active=master.is_active,
        is_template=master.is_template,
        authority=master.authority,
        penalty_details=master.penalty_details,
        reference_links=master.reference_links,
        meta_data=master.meta_data,
        created_at=master.created_at,
        updated_at=master.updated_at,
        created_by=str(master.created_by) if master.created_by else None,
        updated_by=str(master.updated_by) if master.updated_by else None,
        instances_count=instances_count or 0,
    )


@router.delete("/{master_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_compliance_master(
    master_id: str,
    force: bool = Query(False, description="Force delete even with existing instances"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete compliance master (soft delete by setting is_active=False).

    System templates can only be deleted by system admins.
    Cannot delete masters with active instances unless force=True.

    Args:
        master_id: Compliance master UUID
        force: Force delete even with active instances
        db: Database session
        tenant_id: Current tenant ID from JWT
        current_user: Current authenticated user

    Raises:
        HTTPException 403: If user is not authorized
        HTTPException 404: If master not found
        HTTPException 400: If master has active instances
    """
    master = db.query(ComplianceMaster).filter(ComplianceMaster.id == UUID(master_id)).first()

    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance master with ID '{master_id}' not found",
        )

    # Check access
    if master.tenant_id is not None and str(master.tenant_id) != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot delete compliance masters from other tenants",
        )

    # Enforce authorization
    require_master_admin(current_user, master.is_template)

    # Check for active instances
    if not force:
        active_instances = (
            db.query(ComplianceInstance)
            .filter(
                ComplianceInstance.compliance_master_id == UUID(master_id),
                ComplianceInstance.status.in_(["Pending", "In Progress"]),
            )
            .count()
        )

        if active_instances > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete compliance master with {active_instances} active instances. "
                f"Use force=True to override.",
            )

    # Soft delete
    old_status = master.is_active
    master.is_active = False
    master.updated_by = UUID(current_user["user_id"])
    master.updated_at = datetime.utcnow()

    # Log action
    await log_action(
        db=db,
        user_id=current_user["user_id"],
        tenant_id=tenant_id,
        action_type="DELETE",
        resource_type="compliance_master",
        resource_id=str(master.id),
        old_values={"is_active": old_status},
        new_values={"is_active": False},
    )

    db.commit()


@router.post("/bulk-import", response_model=ComplianceMasterBulkImportResponse)
async def bulk_import_compliance_masters(
    import_data: ComplianceMasterBulkImportRequest,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    Bulk import compliance masters.

    Args:
        import_data: List of compliance masters to import
        db: Database session
        tenant_id: Current tenant ID from JWT
        current_user: Current authenticated user

    Returns:
        ComplianceMasterBulkImportResponse: Import results
    """
    # Check if any masters are templates
    has_templates = any(m.is_template for m in import_data.masters)
    if has_templates:
        require_master_admin(current_user, is_template=True)
    else:
        require_master_admin(current_user, is_template=False)

    created_count = 0
    updated_count = 0
    skipped_count = 0
    errors: List[dict] = []

    for master_data in import_data.masters:
        try:
            is_template = master_data.is_template or False
            target_tenant_id = None if is_template else UUID(tenant_id)

            # Check for existing
            existing = (
                db.query(ComplianceMaster)
                .filter(
                    ComplianceMaster.compliance_code == master_data.compliance_code,
                    ComplianceMaster.tenant_id == target_tenant_id,
                )
                .first()
            )

            if existing:
                if import_data.overwrite_existing:
                    # Update existing
                    for field, value in master_data.model_dump(exclude={"is_template"}).items():
                        if value is not None and hasattr(existing, field):
                            setattr(existing, field, value)
                    existing.updated_by = UUID(current_user["user_id"])
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    skipped_count += 1
                    continue
            else:
                # Create new
                master = ComplianceMaster(
                    tenant_id=target_tenant_id,
                    compliance_code=master_data.compliance_code,
                    compliance_name=master_data.compliance_name,
                    description=master_data.description,
                    category=master_data.category,
                    sub_category=master_data.sub_category,
                    frequency=master_data.frequency,
                    due_date_rule=master_data.due_date_rule,
                    owner_role_code=master_data.owner_role_code,
                    approver_role_code=master_data.approver_role_code,
                    dependencies=master_data.dependencies,
                    workflow_config=master_data.workflow_config,
                    authority=master_data.authority,
                    penalty_details=master_data.penalty_details,
                    reference_links=master_data.reference_links,
                    meta_data=master_data.meta_data,
                    is_active=True,
                    is_template=is_template,
                    created_by=UUID(current_user["user_id"]),
                    updated_by=UUID(current_user["user_id"]),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(master)
                created_count += 1

        except Exception as e:
            errors.append(
                {
                    "compliance_code": master_data.compliance_code,
                    "error": str(e),
                }
            )

    db.commit()

    return ComplianceMasterBulkImportResponse(
        created_count=created_count,
        updated_count=updated_count,
        skipped_count=skipped_count,
        errors=errors,
    )
