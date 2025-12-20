"""
Notification Pydantic schemas for request/response validation
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class NotificationBase(BaseModel):
    """Base schema for notification"""

    notification_type: str = Field(..., description="Type of notification")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message content")
    link: Optional[str] = Field(None, description="Link to related resource")

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    """Full notification response with all fields"""

    id: str
    user_id: str
    tenant_id: str
    notification_type: str
    title: str
    message: str
    link: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "456e7890-e89b-12d3-a456-426614174000",
                "tenant_id": "987fcdeb-51d3-12e8-b456-426614174000",
                "notification_type": "task_assigned",
                "title": "New task assigned: Prepare - GSTR-3B Return",
                "message": "You have been assigned the 'Prepare' task for GSTR-3B Return. Due: 2025-01-20",
                "link": "/compliance-instances/789e4567-e89b-12d3-a456-426614174000",
                "is_read": False,
                "read_at": None,
                "created_at": "2025-01-15T10:00:00",
            }
        }


class NotificationListResponse(BaseModel):
    """Paginated list of notifications"""

    items: List[NotificationResponse]
    total: int = Field(..., ge=0, description="Total number of notifications")
    unread_count: int = Field(..., ge=0, description="Count of unread notifications")
    skip: int = Field(..., ge=0, description="Number of items skipped (offset)")
    limit: int = Field(..., ge=1, description="Maximum number of items returned")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 25,
                "unread_count": 5,
                "skip": 0,
                "limit": 50,
            }
        }


class NotificationCountResponse(BaseModel):
    """Response for unread notification count"""

    unread_count: int = Field(..., ge=0, description="Count of unread notifications")

    class Config:
        json_schema_extra = {
            "example": {
                "unread_count": 5,
            }
        }


class NotificationMarkReadRequest(BaseModel):
    """Request to mark notifications as read"""

    notification_ids: Optional[List[str]] = Field(
        None, description="List of notification IDs to mark as read. If empty, marks all as read."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "notification_ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "456e7890-e89b-12d3-a456-426614174000",
                ]
            }
        }


class NotificationMarkReadResponse(BaseModel):
    """Response after marking notifications as read"""

    marked_count: int = Field(..., ge=0, description="Number of notifications marked as read")

    class Config:
        json_schema_extra = {
            "example": {
                "marked_count": 5,
            }
        }


class NotificationDeleteRequest(BaseModel):
    """Request to delete notifications"""

    notification_ids: List[str] = Field(..., description="List of notification IDs to delete", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "notification_ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                ]
            }
        }


class NotificationDeleteResponse(BaseModel):
    """Response after deleting notifications"""

    deleted_count: int = Field(..., ge=0, description="Number of notifications deleted")

    class Config:
        json_schema_extra = {
            "example": {
                "deleted_count": 1,
            }
        }
