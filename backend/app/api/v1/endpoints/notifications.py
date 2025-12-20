"""
Notification management endpoints
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_tenant_id
from app.models import Notification
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationCountResponse,
    NotificationMarkReadRequest,
    NotificationMarkReadResponse,
    NotificationDeleteResponse,
)
from app.services.notification_service import (
    get_user_notifications,
    get_unread_count,
    mark_notification_read,
    mark_all_read,
    delete_notification,
)

router = APIRouter()


def _build_notification_response(notification: Notification) -> dict:
    """Build notification response."""
    return {
        "id": str(notification.id),
        "user_id": str(notification.user_id),
        "tenant_id": str(notification.tenant_id),
        "notification_type": notification.notification_type,
        "title": notification.title,
        "message": notification.message,
        "link": notification.link,
        "is_read": notification.is_read,
        "read_at": notification.read_at,
        "created_at": notification.created_at,
    }


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    List notifications for the current user.
    Returns notifications ordered by created_at desc.
    """
    tenant_uuid = UUID(tenant_id)
    user_id = UUID(current_user["user_id"])

    # Get notifications
    notifications = get_user_notifications(
        db=db,
        user_id=user_id,
        tenant_id=tenant_uuid,
        unread_only=unread_only,
        limit=limit,
        offset=skip,
    )

    # Get total count
    total_query = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.tenant_id == tenant_uuid,
    )
    if unread_only:
        total_query = total_query.filter(Notification.is_read == False)  # noqa: E712
    total = total_query.count()

    # Get unread count
    unread = get_unread_count(db, user_id, tenant_uuid)

    return {
        "items": [_build_notification_response(n) for n in notifications],
        "total": total,
        "unread_count": unread,
        "skip": skip,
        "limit": limit,
    }


@router.get("/count", response_model=NotificationCountResponse)
async def get_notification_count(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Get count of unread notifications for the current user.
    Useful for notification badge in UI.
    """
    tenant_uuid = UUID(tenant_id)
    user_id = UUID(current_user["user_id"])

    unread = get_unread_count(db, user_id, tenant_uuid)

    return {"unread_count": unread}


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Get a specific notification by ID.
    """
    tenant_uuid = UUID(tenant_id)
    user_id = UUID(current_user["user_id"])
    notification_uuid = UUID(notification_id)

    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_uuid,
            Notification.user_id == user_id,
            Notification.tenant_id == tenant_uuid,
        )
        .first()
    )

    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    return _build_notification_response(notification)


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_single_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Mark a single notification as read.
    """
    tenant_uuid = UUID(tenant_id)
    user_id = UUID(current_user["user_id"])
    notification_uuid = UUID(notification_id)

    notification = mark_notification_read(
        db=db,
        notification_id=notification_uuid,
        user_id=user_id,
        tenant_id=tenant_uuid,
    )

    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    return _build_notification_response(notification)


@router.post("/mark-read", response_model=NotificationMarkReadResponse)
async def mark_notifications_read(
    request: NotificationMarkReadRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Mark multiple notifications as read.
    If notification_ids is empty or None, marks all notifications as read.
    """
    tenant_uuid = UUID(tenant_id)
    user_id = UUID(current_user["user_id"])

    if not request.notification_ids:
        # Mark all as read
        count = mark_all_read(db, user_id, tenant_uuid)
        return {"marked_count": count}

    # Mark specific notifications as read
    marked_count = 0
    for notification_id in request.notification_ids:
        try:
            notification_uuid = UUID(notification_id)
            result = mark_notification_read(
                db=db,
                notification_id=notification_uuid,
                user_id=user_id,
                tenant_id=tenant_uuid,
            )
            if result:
                marked_count += 1
        except ValueError:
            continue  # Skip invalid UUIDs

    return {"marked_count": marked_count}


@router.post("/mark-all-read", response_model=NotificationMarkReadResponse)
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Mark all notifications as read for the current user.
    """
    tenant_uuid = UUID(tenant_id)
    user_id = UUID(current_user["user_id"])

    count = mark_all_read(db, user_id, tenant_uuid)

    return {"marked_count": count}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_single_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Delete a notification.
    """
    tenant_uuid = UUID(tenant_id)
    user_id = UUID(current_user["user_id"])
    notification_uuid = UUID(notification_id)

    deleted = delete_notification(
        db=db,
        notification_id=notification_uuid,
        user_id=user_id,
        tenant_id=tenant_uuid,
    )

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    return None


@router.delete("/", response_model=NotificationDeleteResponse)
async def delete_notifications(
    notification_ids: str = Query(..., description="Comma-separated list of notification IDs to delete"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Delete multiple notifications.
    Pass notification IDs as a comma-separated string.
    """
    tenant_uuid = UUID(tenant_id)
    user_id = UUID(current_user["user_id"])

    id_list = [id.strip() for id in notification_ids.split(",") if id.strip()]

    if not id_list:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No notification IDs provided")

    deleted_count = 0
    for notification_id in id_list:
        try:
            notification_uuid = UUID(notification_id)
            if delete_notification(db, notification_uuid, user_id, tenant_uuid):
                deleted_count += 1
        except ValueError:
            continue  # Skip invalid UUIDs

    return {"deleted_count": deleted_count}
