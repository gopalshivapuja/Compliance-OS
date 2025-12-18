"""
Entity management endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_tenant_id

router = APIRouter()


@router.get("/")
async def list_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    List entities for current tenant.

    TODO: Implement listing logic with pagination
    """
    return {
        "message": "List entities endpoint - TODO: Implement",
        "tenant_id": tenant_id,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{entity_id}")
async def get_entity(
    entity_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Get entity by ID.

    TODO: Implement get logic with access control
    """
    return {
        "message": f"Get entity {entity_id} - TODO: Implement",
        "tenant_id": tenant_id,
    }


@router.post("/")
async def create_entity(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Create a new entity.

    TODO: Implement creation logic
    """
    return {
        "message": "Create entity endpoint - TODO: Implement",
        "tenant_id": tenant_id,
    }


@router.put("/{entity_id}")
async def update_entity(
    entity_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Update entity.

    TODO: Implement update logic
    """
    return {
        "message": f"Update entity {entity_id} - TODO: Implement",
        "tenant_id": tenant_id,
    }


@router.delete("/{entity_id}")
async def delete_entity(
    entity_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Delete entity (soft delete recommended).

    TODO: Implement deletion logic
    """
    return {
        "message": f"Delete entity {entity_id} - TODO: Implement",
        "tenant_id": tenant_id,
    }
