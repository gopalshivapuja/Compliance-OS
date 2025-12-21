"""
Tenant management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantListResponse,
)
from app.models import Tenant
from app.services import log_action

router = APIRouter()


def require_system_admin(current_user: dict) -> dict:
    """
    Dependency to enforce system admin access.

    Args:
        current_user: Current authenticated user from JWT

    Returns:
        dict: User data if authorized

    Raises:
        HTTPException 403: If user is not a system admin
    """
    # Check if user has SYSTEM_ADMIN role
    user_roles = current_user.get("roles", [])
    if "SYSTEM_ADMIN" not in user_roles and not current_user.get("is_system_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only system administrators can manage tenants",
        )
    return current_user


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new tenant (system admin only).

    Only system administrators can create new tenants. The tenant_code must be unique.

    Args:
        tenant_data: Tenant creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        TenantResponse: Created tenant details

    Raises:
        HTTPException 403: If user is not system admin
        HTTPException 400: If tenant_code already exists
    """
    # Enforce system admin access
    require_system_admin(current_user)

    # Check if tenant_code already exists
    existing_tenant = db.query(Tenant).filter(Tenant.tenant_code == tenant_data.tenant_code).first()
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant with code '{tenant_data.tenant_code}' already exists",
        )

    # Create new tenant
    tenant = Tenant(
        tenant_code=tenant_data.tenant_code,
        tenant_name=tenant_data.tenant_name,
        contact_email=tenant_data.contact_email,
        contact_phone=tenant_data.contact_phone,
        address=tenant_data.address,
        status=tenant_data.status or "active",
        meta_data=tenant_data.meta_data,
        created_by=current_user["user_id"],
        updated_by=current_user["user_id"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(tenant)
    db.flush()  # Get the ID before commit

    # Log action (using system tenant context for tenant creation)
    await log_action(
        db=db,
        user_id=current_user["user_id"],
        tenant_id=str(tenant.id),  # New tenant's ID
        action_type="CREATE",
        resource_type="tenant",
        resource_id=str(tenant.id),
        new_values={
            "tenant_code": tenant_data.tenant_code,
            "tenant_name": tenant_data.tenant_name,
            "status": tenant_data.status or "active",
        },
    )

    db.commit()
    db.refresh(tenant)

    return tenant


@router.get("/", response_model=TenantListResponse, status_code=status.HTTP_200_OK)
async def list_tenants(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in name or code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List all tenants with pagination (system admin only).

    Only system administrators can view all tenants.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        status: Filter by tenant status (active, suspended, inactive)
        search: Search query for tenant name or code
        db: Database session
        current_user: Current authenticated user

    Returns:
        TenantListResponse: Paginated list of tenants

    Raises:
        HTTPException 403: If user is not system admin
    """
    # Enforce system admin access
    require_system_admin(current_user)

    # Build query
    query = db.query(Tenant)

    # Apply filters
    if status:
        query = query.filter(Tenant.status == status)

    if search:
        search_term = f"%{search}%"
        query = query.filter((Tenant.tenant_name.ilike(search_term)) | (Tenant.tenant_code.ilike(search_term)))

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    tenants = query.order_by(Tenant.created_at.desc()).offset(offset).limit(page_size).all()

    return TenantListResponse(
        tenants=tenants,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{tenant_id}", response_model=TenantResponse, status_code=status.HTTP_200_OK)
async def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get tenant by ID.

    Users can view their own tenant or system admins can view any tenant.

    Args:
        tenant_id: Tenant UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        TenantResponse: Tenant details

    Raises:
        HTTPException 403: If user is not authorized to view this tenant
        HTTPException 404: If tenant not found
    """
    # Find tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found",
        )

    # Authorization check: user's own tenant or system admin
    user_roles = current_user.get("roles", [])
    is_admin = "SYSTEM_ADMIN" in user_roles or current_user.get("is_system_admin", False)

    if str(tenant.id) != current_user["tenant_id"] and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own tenant details",
        )

    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse, status_code=status.HTTP_200_OK)
async def update_tenant(
    tenant_id: str,
    tenant_data: TenantUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update tenant (system admin only).

    Only system administrators can update tenant information.
    tenant_code cannot be updated.

    Args:
        tenant_id: Tenant UUID
        tenant_data: Tenant update data (all fields optional)
        db: Database session
        current_user: Current authenticated user

    Returns:
        TenantResponse: Updated tenant details

    Raises:
        HTTPException 403: If user is not system admin
        HTTPException 404: If tenant not found
    """
    # Enforce system admin access
    require_system_admin(current_user)

    # Find tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found",
        )

    # Capture old values for audit log
    old_values = {
        "tenant_name": tenant.tenant_name,
        "contact_email": tenant.contact_email,
        "contact_phone": tenant.contact_phone,
        "address": tenant.address,
        "status": tenant.status,
    }

    # Update fields (only if provided)
    update_data = tenant_data.model_dump(exclude_unset=True)
    new_values = {}

    for field, value in update_data.items():
        if value is not None:
            setattr(tenant, field, value)
            new_values[field] = value

    # Update audit fields
    tenant.updated_by = current_user["user_id"]
    tenant.updated_at = datetime.utcnow()

    # Log action
    await log_action(
        db=db,
        user_id=current_user["user_id"],
        tenant_id=str(tenant.id),
        action_type="UPDATE",
        resource_type="tenant",
        resource_id=str(tenant.id),
        old_values=old_values,
        new_values=new_values,
    )

    db.commit()
    db.refresh(tenant)

    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Soft delete a tenant (system admin only).

    Sets tenant status to 'inactive' instead of hard deletion to preserve audit trail.

    Args:
        tenant_id: Tenant UUID
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException 403: If user is not system admin
        HTTPException 404: If tenant not found
        HTTPException 400: If tenant has active users or entities
    """
    # Enforce system admin access
    require_system_admin(current_user)

    # Find tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found",
        )

    # Check for active dependencies (users, entities)
    if tenant.users and any(u.status == "active" for u in tenant.users):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete tenant with active users. Deactivate users first.",
        )

    # Soft delete: set status to inactive
    old_status = tenant.status
    tenant.status = "inactive"
    tenant.updated_by = current_user["user_id"]
    tenant.updated_at = datetime.utcnow()

    # Log action
    await log_action(
        db=db,
        user_id=current_user["user_id"],
        tenant_id=str(tenant.id),
        action_type="DELETE",
        resource_type="tenant",
        resource_id=str(tenant.id),
        old_values={"status": old_status},
        new_values={"status": "inactive"},
    )

    db.commit()
