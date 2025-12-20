"""
Audit Log Pydantic schemas for request/response validation
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Audit log response schema"""

    audit_log_id: str
    tenant_id: str
    user_id: str
    user_name: Optional[str] = None  # Denormalized user name for display
    user_email: Optional[str] = None  # Denormalized user email
    action_type: str  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, APPROVE, REJECT
    resource_type: str  # user, compliance_instance, evidence, workflow_task, etc.
    resource_id: str
    old_values: Optional[Dict[str, Any]] = None  # JSONB before state
    new_values: Optional[Dict[str, Any]] = None  # JSONB after state
    change_summary: str  # Human-readable summary
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "audit_log_id": "123e4567-e89b-12d3-a456-426614174000",
                "tenant_id": "987fcdeb-51d3-12e8-b456-426614174000",
                "user_id": "456e7890-e89b-12d3-a456-426614174000",
                "user_name": "Test Admin",
                "user_email": "admin@testgcc.com",
                "action_type": "UPDATE",
                "resource_type": "compliance_instance",
                "resource_id": "789e4567-e89b-12d3-a456-426614174000",
                "old_values": {"status": "Not Started"},
                "new_values": {"status": "In Progress"},
                "change_summary": "Updated status from Not Started to In Progress",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 ...",
                "created_at": "2024-12-18T10:30:00",
            }
        }


class AuditLogListResponse(BaseModel):
    """Paginated list of audit logs"""

    items: list[AuditLogResponse]
    total: int = Field(..., ge=0, description="Total number of items matching the filters")
    skip: int = Field(..., ge=0, description="Number of items skipped (offset)")
    limit: int = Field(..., ge=1, description="Maximum number of items returned")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 150,
                "skip": 0,
                "limit": 50,
            }
        }


class ResourceAuditTrailResponse(BaseModel):
    """Complete audit trail for a specific resource"""

    resource_type: str
    resource_id: str
    audit_logs: list[AuditLogResponse]
    total_changes: int

    class Config:
        json_schema_extra = {
            "example": {
                "resource_type": "compliance_instance",
                "resource_id": "789e4567-e89b-12d3-a456-426614174000",
                "audit_logs": [],
                "total_changes": 5,
            }
        }
