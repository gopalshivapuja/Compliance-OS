"""
Entity management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_tenant_id
from app.schemas import (
    EntityCreate,
    EntityUpdate,
    EntityResponse,
    EntityListResponse,
)
from app.models import Entity, ComplianceInstance
from app.models.entity import entity_access
from app.services import (
    log_action,
    check_entity_access,
    get_user_accessible_entities,
    check_role_permission,
    grant_entity_access,
)

router = APIRouter()


def require_entity_admin(current_user: dict) -> dict:
    """
    Require user to have entity management permissions.

    Args:
        current_user: Current authenticated user from JWT

    Returns:
        dict: User data if authorized

    Raises:
        HTTPException 403: If user is not authorized
    """
    user_roles = current_user.get("roles", [])
    is_system_admin = current_user.get("is_system_admin", False)

    # System admins and tenant admins can manage entities
    admin_roles = ["System Admin", "Tenant Admin", "admin"]
    if is_system_admin or check_role_permission(user_roles, admin_roles):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only administrators can manage entities",
    )


@router.post("/", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity_data: EntityCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new entity.

    Only tenant admins and system admins can create entities.

    Args:
        entity_data: Entity creation data
        db: Database session
        tenant_id: Current tenant ID from JWT
        current_user: Current authenticated user

    Returns:
        EntityResponse: Created entity details

    Raises:
        HTTPException 403: If user is not authorized
        HTTPException 400: If entity code already exists
    """
    # Enforce authorization
    require_entity_admin(current_user)

    # Check for duplicate entity code within tenant
    existing_entity = (
        db.query(Entity)
        .filter(
            Entity.tenant_id == UUID(tenant_id),
            Entity.entity_code == entity_data.entity_code,
        )
        .first()
    )
    if existing_entity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Entity with code '{entity_data.entity_code}' already exists in this tenant",
        )

    # Create new entity
    entity = Entity(
        tenant_id=UUID(tenant_id),
        entity_code=entity_data.entity_code,
        entity_name=entity_data.entity_name,
        entity_type=entity_data.entity_type,
        pan=entity_data.pan,
        gstin=entity_data.gstin,
        cin=entity_data.cin,
        tan=entity_data.tan,
        address=entity_data.address,
        city=entity_data.city,
        state=entity_data.state,
        pincode=entity_data.pincode,
        contact_person=entity_data.contact_person,
        contact_email=entity_data.contact_email,
        contact_phone=entity_data.contact_phone,
        status="active",
        created_by=UUID(current_user["user_id"]),
        updated_by=UUID(current_user["user_id"]),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(entity)
    db.flush()

    # Grant access to the creating user
    grant_entity_access(
        db=db,
        user_id=UUID(current_user["user_id"]),
        entity_id=entity.id,
        tenant_id=UUID(tenant_id),
    )

    # Log action
    await log_action(
        db=db,
        user_id=current_user["user_id"],
        tenant_id=tenant_id,
        action_type="CREATE",
        resource_type="entity",
        resource_id=str(entity.id),
        new_values={
            "entity_code": entity.entity_code,
            "entity_name": entity.entity_name,
            "entity_type": entity.entity_type,
            "pan": entity.pan,
            "gstin": entity.gstin,
        },
    )

    db.commit()
    db.refresh(entity)

    # Get user count with access
    users_count = (
        db.query(func.count(entity_access.c.user_id))
        .filter(entity_access.c.entity_id == entity.id)
        .scalar()
    )

    return EntityResponse(
        id=str(entity.id),
        tenant_id=str(entity.tenant_id),
        entity_code=entity.entity_code,
        entity_name=entity.entity_name,
        entity_type=entity.entity_type,
        pan=entity.pan,
        gstin=entity.gstin,
        cin=entity.cin,
        tan=entity.tan,
        address=entity.address,
        city=entity.city,
        state=entity.state,
        pincode=entity.pincode,
        contact_person=entity.contact_person,
        contact_email=entity.contact_email,
        contact_phone=entity.contact_phone,
        status=entity.status,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        created_by=str(entity.created_by) if entity.created_by else None,
        updated_by=str(entity.updated_by) if entity.updated_by else None,
        users_with_access_count=users_count or 0,
    )


@router.get("/", response_model=EntityListResponse, status_code=status.HTTP_200_OK)
async def list_entities(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    entity_status: Optional[str] = Query(None, description="Filter by status (active, inactive)"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    search: Optional[str] = Query(None, description="Search in name or code"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    List entities with pagination.

    Admins can see all entities in their tenant.
    Regular users can only see entities they have access to.

    Args:
        skip: Number of records to skip (for pagination)
        limit: Number of records to return (max 100)
        entity_status: Filter by entity status
        entity_type: Filter by entity type
        search: Search query for entity name or code
        db: Database session
        tenant_id: Current tenant ID from JWT
        current_user: Current authenticated user

    Returns:
        EntityListResponse: Paginated list of entities
    """
    user_roles = current_user.get("roles", [])
    is_system_admin = current_user.get("is_system_admin", False)
    admin_roles = ["System Admin", "Tenant Admin", "admin"]

    # Build query
    query = db.query(Entity).filter(Entity.tenant_id == UUID(tenant_id))

    # Apply entity access filtering for non-admins
    if not is_system_admin and not check_role_permission(user_roles, admin_roles):
        accessible_entities = get_user_accessible_entities(
            db=db,
            user_id=UUID(current_user["user_id"]),
            tenant_id=UUID(tenant_id),
        )
        if accessible_entities:
            query = query.filter(Entity.id.in_(accessible_entities))
        else:
            # No access to any entities
            return EntityListResponse(items=[], total=0, skip=skip, limit=limit)

    # Apply filters
    if entity_status:
        query = query.filter(Entity.status == entity_status)

    if entity_type:
        query = query.filter(Entity.entity_type == entity_type)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Entity.entity_name.ilike(search_term)) | (Entity.entity_code.ilike(search_term))
        )

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    entities = query.order_by(Entity.entity_name.asc()).offset(skip).limit(limit).all()

    # Build response
    entity_list = []
    for entity in entities:
        users_count = (
            db.query(func.count(entity_access.c.user_id))
            .filter(entity_access.c.entity_id == entity.id)
            .scalar()
        )

        entity_list.append(
            EntityResponse(
                id=str(entity.id),
                tenant_id=str(entity.tenant_id),
                entity_code=entity.entity_code,
                entity_name=entity.entity_name,
                entity_type=entity.entity_type,
                pan=entity.pan,
                gstin=entity.gstin,
                cin=entity.cin,
                tan=entity.tan,
                address=entity.address,
                city=entity.city,
                state=entity.state,
                pincode=entity.pincode,
                contact_person=entity.contact_person,
                contact_email=entity.contact_email,
                contact_phone=entity.contact_phone,
                status=entity.status,
                created_at=entity.created_at,
                updated_at=entity.updated_at,
                created_by=str(entity.created_by) if entity.created_by else None,
                updated_by=str(entity.updated_by) if entity.updated_by else None,
                users_with_access_count=users_count or 0,
            )
        )

    return EntityListResponse(items=entity_list, total=total, skip=skip, limit=limit)


@router.get("/{entity_id}", response_model=EntityResponse, status_code=status.HTTP_200_OK)
async def get_entity(
    entity_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    Get entity by ID.

    Admins can view any entity in their tenant.
    Regular users can only view entities they have access to.

    Args:
        entity_id: Entity UUID
        db: Database session
        tenant_id: Current tenant ID from JWT
        current_user: Current authenticated user

    Returns:
        EntityResponse: Entity details

    Raises:
        HTTPException 403: If user is not authorized
        HTTPException 404: If entity not found
    """
    # Find entity
    entity = (
        db.query(Entity)
        .filter(Entity.id == UUID(entity_id), Entity.tenant_id == UUID(tenant_id))
        .first()
    )

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity with ID '{entity_id}' not found",
        )

    # Authorization check
    user_roles = current_user.get("roles", [])
    is_system_admin = current_user.get("is_system_admin", False)
    admin_roles = ["System Admin", "Tenant Admin", "admin"]

    # Admins can access any entity in their tenant
    if not is_system_admin and not check_role_permission(user_roles, admin_roles):
        # Check if user has access to this entity
        has_access = check_entity_access(
            db=db,
            user_id=UUID(current_user["user_id"]),
            entity_id=UUID(entity_id),
            tenant_id=UUID(tenant_id),
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this entity",
            )

    # Get user count with access
    users_count = (
        db.query(func.count(entity_access.c.user_id))
        .filter(entity_access.c.entity_id == entity.id)
        .scalar()
    )

    return EntityResponse(
        id=str(entity.id),
        tenant_id=str(entity.tenant_id),
        entity_code=entity.entity_code,
        entity_name=entity.entity_name,
        entity_type=entity.entity_type,
        pan=entity.pan,
        gstin=entity.gstin,
        cin=entity.cin,
        tan=entity.tan,
        address=entity.address,
        city=entity.city,
        state=entity.state,
        pincode=entity.pincode,
        contact_person=entity.contact_person,
        contact_email=entity.contact_email,
        contact_phone=entity.contact_phone,
        status=entity.status,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        created_by=str(entity.created_by) if entity.created_by else None,
        updated_by=str(entity.updated_by) if entity.updated_by else None,
        users_with_access_count=users_count or 0,
    )


@router.put("/{entity_id}", response_model=EntityResponse, status_code=status.HTTP_200_OK)
async def update_entity(
    entity_id: str,
    entity_data: EntityUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    Update entity.

    Only tenant admins and system admins can update entities.

    Args:
        entity_id: Entity UUID
        entity_data: Entity update data (all fields optional)
        db: Database session
        tenant_id: Current tenant ID from JWT
        current_user: Current authenticated user

    Returns:
        EntityResponse: Updated entity details

    Raises:
        HTTPException 403: If user is not authorized
        HTTPException 404: If entity not found
    """
    # Enforce authorization
    require_entity_admin(current_user)

    # Find entity
    entity = (
        db.query(Entity)
        .filter(Entity.id == UUID(entity_id), Entity.tenant_id == UUID(tenant_id))
        .first()
    )

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity with ID '{entity_id}' not found",
        )

    # Capture old values for audit log
    old_values = {}
    new_values = {}
    update_data = entity_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None and hasattr(entity, field):
            old_values[field] = getattr(entity, field)
            setattr(entity, field, value)
            new_values[field] = value

    # Update audit fields
    entity.updated_by = UUID(current_user["user_id"])
    entity.updated_at = datetime.utcnow()

    # Log action
    if new_values:
        await log_action(
            db=db,
            user_id=current_user["user_id"],
            tenant_id=tenant_id,
            action_type="UPDATE",
            resource_type="entity",
            resource_id=str(entity.id),
            old_values=old_values,
            new_values=new_values,
        )

    db.commit()
    db.refresh(entity)

    # Get user count with access
    users_count = (
        db.query(func.count(entity_access.c.user_id))
        .filter(entity_access.c.entity_id == entity.id)
        .scalar()
    )

    return EntityResponse(
        id=str(entity.id),
        tenant_id=str(entity.tenant_id),
        entity_code=entity.entity_code,
        entity_name=entity.entity_name,
        entity_type=entity.entity_type,
        pan=entity.pan,
        gstin=entity.gstin,
        cin=entity.cin,
        tan=entity.tan,
        address=entity.address,
        city=entity.city,
        state=entity.state,
        pincode=entity.pincode,
        contact_person=entity.contact_person,
        contact_email=entity.contact_email,
        contact_phone=entity.contact_phone,
        status=entity.status,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        created_by=str(entity.created_by) if entity.created_by else None,
        updated_by=str(entity.updated_by) if entity.updated_by else None,
        users_with_access_count=users_count or 0,
    )


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    entity_id: str,
    force: bool = Query(False, description="Force delete even with active compliance instances"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    Soft delete an entity (admin only).

    Sets entity status to 'inactive' instead of hard deletion to preserve audit trail.
    Cannot delete entity with active compliance instances unless force=True.

    Args:
        entity_id: Entity UUID
        force: Force delete even with active instances
        db: Database session
        tenant_id: Current tenant ID from JWT
        current_user: Current authenticated user

    Raises:
        HTTPException 403: If user is not authorized
        HTTPException 404: If entity not found
        HTTPException 400: If entity has active compliance instances
    """
    # Enforce authorization
    require_entity_admin(current_user)

    # Find entity
    entity = (
        db.query(Entity)
        .filter(Entity.id == UUID(entity_id), Entity.tenant_id == UUID(tenant_id))
        .first()
    )

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity with ID '{entity_id}' not found",
        )

    # Check for active compliance instances
    if not force:
        active_instances = (
            db.query(ComplianceInstance)
            .filter(
                ComplianceInstance.entity_id == UUID(entity_id),
                ComplianceInstance.status.in_(["pending", "in_progress"]),
            )
            .count()
        )

        if active_instances > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete entity with {active_instances} active compliance instances. "
                f"Use force=True to override.",
            )

    # Soft delete: set status to inactive
    old_status = entity.status
    entity.status = "inactive"
    entity.updated_by = UUID(current_user["user_id"])
    entity.updated_at = datetime.utcnow()

    # Log action
    await log_action(
        db=db,
        user_id=current_user["user_id"],
        tenant_id=tenant_id,
        action_type="DELETE",
        resource_type="entity",
        resource_id=str(entity.id),
        old_values={"status": old_status},
        new_values={"status": "inactive"},
    )

    db.commit()
