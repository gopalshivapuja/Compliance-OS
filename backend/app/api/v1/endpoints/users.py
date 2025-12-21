"""
User management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import get_password_hash
from app.schemas import (
    UserCreate,
    UserUpdate,
    UserInDB,
    UserListResponse,
)
from app.models import User, Tenant
from app.services import log_action

router = APIRouter()


def require_user_admin(current_user: dict, target_tenant_id: Optional[str] = None) -> dict:
    """
    Dependency to enforce user management access.

    Args:
        current_user: Current authenticated user from JWT
        target_tenant_id: Optional tenant ID being managed

    Returns:
        dict: User data if authorized

    Raises:
        HTTPException 403: If user is not authorized
    """
    user_roles = current_user.get("roles", [])
    is_system_admin = current_user.get("is_system_admin", False)

    # System admins can manage all users
    if is_system_admin or "SYSTEM_ADMIN" in user_roles:
        return current_user

    # Tenant admins can only manage users in their own tenant
    if target_tenant_id and target_tenant_id != current_user["tenant_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage users in your own tenant",
        )

    # Check if user has admin role in their tenant (SYSTEM_ADMIN or TENANT_ADMIN)
    if "SYSTEM_ADMIN" not in user_roles and "TENANT_ADMIN" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage users",
        )

    return current_user


@router.post("/", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new user.

    System admins can create users in any tenant.
    Tenant admins can only create users in their own tenant.

    Args:
        user_data: User creation data including password
        db: Database session
        current_user: Current authenticated user

    Returns:
        UserInDB: Created user details (without password)

    Raises:
        HTTPException 403: If user is not authorized
        HTTPException 400: If email already exists or tenant not found
    """
    # Enforce authorization
    require_user_admin(current_user, user_data.tenant_id)

    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == user_data.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant with ID '{user_data.tenant_id}' not found",
        )

    # Check if tenant is active
    if tenant.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create user in {tenant.status} tenant",
        )

    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{user_data.email}' already exists",
        )

    # Create new user
    user = User(
        tenant_id=user_data.tenant_id,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        status="active",
        is_system_admin=user_data.is_system_admin if current_user.get("is_system_admin") else False,
        created_by=current_user["user_id"],
        updated_by=current_user["user_id"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Hash password
    user.password_hash = get_password_hash(user_data.password)

    db.add(user)
    db.flush()  # Get the ID before commit

    # Log action
    await log_action(
        db=db,
        user_id=current_user["user_id"],
        tenant_id=user_data.tenant_id,
        action_type="CREATE",
        resource_type="user",
        resource_id=str(user.id),
        new_values={
            "email": user_data.email,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "is_system_admin": user.is_system_admin,
        },
    )

    db.commit()
    db.refresh(user)

    # Convert to UserInDB schema (includes roles)
    user_dict = {
        "user_id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "status": user.status,
        "is_system_admin": user.is_system_admin,
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "roles": [role.role_code for role in user.roles],
    }

    return UserInDB(**user_dict)


@router.get("/", response_model=UserListResponse, status_code=status.HTTP_200_OK)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    user_status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in name or email"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID (system admin only)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List users with pagination.

    System admins can view all users across all tenants.
    Tenant admins can only view users in their own tenant.

    Args:
        skip: Number of records to skip (for pagination)
        limit: Number of records to return (max 100)
        user_status: Filter by user status (active, inactive, suspended)
        search: Search query for user name or email
        tenant_id: Filter by tenant ID (system admin only)
        db: Database session
        current_user: Current authenticated user

    Returns:
        UserListResponse: Paginated list of users

    Raises:
        HTTPException 403: If user is not authorized
    """
    user_roles = current_user.get("roles", [])
    is_system_admin = current_user.get("is_system_admin", False)

    # Build query
    query = db.query(User)

    # Apply tenant filtering
    if tenant_id:
        # Only system admins can filter by tenant
        if not is_system_admin and "SYSTEM_ADMIN" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only system administrators can view users across tenants",
            )
        query = query.filter(User.tenant_id == tenant_id)
    else:
        # Non-system admins can only see their own tenant
        if not is_system_admin:
            query = query.filter(User.tenant_id == current_user["tenant_id"])

    # Apply filters
    if user_status:
        query = query.filter(User.status == user_status)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.first_name.ilike(search_term)) | (User.last_name.ilike(search_term)) | (User.email.ilike(search_term))
        )

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    # Convert to UserInDB schema
    user_list = []
    for user in users:
        user_dict = {
            "user_id": str(user.id),
            "tenant_id": str(user.tenant_id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "status": user.status,
            "is_system_admin": user.is_system_admin,
            "last_login_at": user.last_login_at,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "roles": [role.role_code for role in user.roles],
        }
        user_list.append(UserInDB(**user_dict))

    return UserListResponse(
        items=user_list,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{user_id}", response_model=UserInDB, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get user by ID.

    Users can view their own profile.
    Admins can view users in their tenant.
    System admins can view any user.

    Args:
        user_id: User UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        UserInDB: User details

    Raises:
        HTTPException 403: If user is not authorized
        HTTPException 404: If user not found
    """
    # Find user
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )

    # Authorization check
    user_roles = current_user.get("roles", [])
    is_system_admin = current_user.get("is_system_admin", False)
    is_own_profile = str(user.id) == current_user["user_id"]
    is_same_tenant = str(user.tenant_id) == current_user["tenant_id"]
    is_admin = "SYSTEM_ADMIN" in user_roles or "TENANT_ADMIN" in user_roles

    # Allow if: own profile, OR admin in same tenant, OR system admin
    if not (is_own_profile or (is_admin and is_same_tenant) or is_system_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this user",
        )

    # Convert to UserInDB schema
    user_dict = {
        "user_id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "status": user.status,
        "is_system_admin": user.is_system_admin,
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "roles": [role.role_code for role in user.roles],
    }

    return UserInDB(**user_dict)


@router.put("/{user_id}", response_model=UserInDB, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update user.

    Users can update their own basic profile (name, phone).
    Admins can update users in their tenant (including status).
    System admins can update any user.

    Args:
        user_id: User UUID
        user_data: User update data (all fields optional)
        db: Database session
        current_user: Current authenticated user

    Returns:
        UserInDB: Updated user details

    Raises:
        HTTPException 403: If user is not authorized
        HTTPException 404: If user not found
    """
    # Find user
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )

    # Authorization check
    user_roles = current_user.get("roles", [])
    is_system_admin = current_user.get("is_system_admin", False)
    is_own_profile = str(user.id) == current_user["user_id"]
    is_same_tenant = str(user.tenant_id) == current_user["tenant_id"]
    is_admin = "SYSTEM_ADMIN" in user_roles or "TENANT_ADMIN" in user_roles

    # Determine what can be updated
    can_update_basic = is_own_profile or (is_admin and is_same_tenant) or is_system_admin
    can_update_status = (is_admin and is_same_tenant) or is_system_admin

    if not can_update_basic:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this user",
        )

    # Capture old values for audit log
    old_values = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "status": user.status,
    }

    # Update fields (only if provided)
    update_data = user_data.model_dump(exclude_unset=True)
    new_values = {}

    for field, value in update_data.items():
        if value is not None:
            # Restrict status changes to admins
            if field == "status" and not can_update_status:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only administrators can change user status",
                )

            setattr(user, field, value)
            new_values[field] = value

    # Update audit fields
    user.updated_by = current_user["user_id"]
    user.updated_at = datetime.utcnow()

    # Log action
    await log_action(
        db=db,
        user_id=current_user["user_id"],
        tenant_id=str(user.tenant_id),
        action_type="UPDATE",
        resource_type="user",
        resource_id=str(user.id),
        old_values=old_values,
        new_values=new_values,
    )

    db.commit()
    db.refresh(user)

    # Convert to UserInDB schema
    user_dict = {
        "user_id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "status": user.status,
        "is_system_admin": user.is_system_admin,
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "roles": [role.role_code for role in user.roles],
    }

    return UserInDB(**user_dict)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Soft delete a user (admin only).

    Sets user status to 'inactive' instead of hard deletion to preserve audit trail.
    Users cannot delete themselves.

    Args:
        user_id: User UUID
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException 403: If user is not authorized
        HTTPException 404: If user not found
        HTTPException 400: If trying to delete self or user has active tasks
    """
    # Find user
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )

    # Authorization check - must be admin
    user_roles = current_user.get("roles", [])
    is_system_admin = current_user.get("is_system_admin", False)
    is_same_tenant = str(user.tenant_id) == current_user["tenant_id"]
    is_admin = "SYSTEM_ADMIN" in user_roles or "TENANT_ADMIN" in user_roles

    if not ((is_admin and is_same_tenant) or is_system_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete users",
        )

    # Cannot delete self
    if str(user.id) == current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )

    # Check for active workflow tasks
    active_tasks_count = sum(1 for task in user.assigned_tasks if task.status in ["pending", "in_progress"])
    if active_tasks_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(f"Cannot delete user with {active_tasks_count} active " "workflow tasks. Reassign tasks first."),
        )

    # Soft delete: set status to inactive
    old_status = user.status
    user.status = "inactive"
    user.updated_by = current_user["user_id"]
    user.updated_at = datetime.utcnow()

    # Log action
    await log_action(
        db=db,
        user_id=current_user["user_id"],
        tenant_id=str(user.tenant_id),
        action_type="DELETE",
        resource_type="user",
        resource_id=str(user.id),
        old_values={"status": old_status},
        new_values={"status": "inactive"},
    )

    db.commit()
