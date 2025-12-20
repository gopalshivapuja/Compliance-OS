"""
Workflow Task Pydantic schemas for request/response validation
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class WorkflowTaskBase(BaseModel):
    """Base schema for workflow task"""

    task_type: str = Field(..., description="Task type (Prepare, Review, Approve, File, Archive)")
    task_name: str = Field(..., description="Task name")
    task_description: Optional[str] = Field(None, description="Task description")
    sequence_order: int = Field(1, ge=1, description="Order in workflow sequence")
    due_date: Optional[date] = Field(None, description="Task due date")

    class Config:
        from_attributes = True


class WorkflowTaskCreate(BaseModel):
    """Schema for creating a workflow task"""

    compliance_instance_id: str = Field(..., description="Compliance instance ID")
    task_type: str = Field(..., description="Task type (Prepare, Review, Approve, File, Archive)")
    task_name: str = Field(..., description="Task name")
    task_description: Optional[str] = Field(None, description="Task description")
    assigned_to_user_id: Optional[str] = Field(None, description="Assigned user ID")
    assigned_to_role_id: Optional[str] = Field(None, description="Assigned role ID")
    sequence_order: int = Field(1, ge=1, description="Order in workflow sequence")
    parent_task_id: Optional[str] = Field(None, description="Parent task ID for sub-tasks")
    due_date: Optional[date] = Field(None, description="Task due date")
    meta_data: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "compliance_instance_id": "123e4567-e89b-12d3-a456-426614174000",
                "task_type": "Prepare",
                "task_name": "Prepare GSTR-3B return data",
                "task_description": "Collect all sales and purchase data for the month",
                "assigned_to_user_id": "789e4567-e89b-12d3-a456-426614174000",
                "sequence_order": 1,
                "due_date": "2025-01-15",
            }
        }


class WorkflowTaskUpdate(BaseModel):
    """Schema for updating a workflow task"""

    task_name: Optional[str] = None
    task_description: Optional[str] = None
    assigned_to_user_id: Optional[str] = None
    assigned_to_role_id: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[date] = None
    sequence_order: Optional[int] = Field(None, ge=1)
    meta_data: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "assigned_to_user_id": "789e4567-e89b-12d3-a456-426614174000",
                "due_date": "2025-01-20",
            }
        }


class WorkflowTaskActionRequest(BaseModel):
    """Schema for task actions (start, complete, reject)"""

    remarks: Optional[str] = Field(None, description="Action remarks")

    class Config:
        json_schema_extra = {
            "example": {
                "remarks": "Data prepared and verified",
            }
        }


class WorkflowTaskRejectRequest(BaseModel):
    """Schema for rejecting a task"""

    rejection_reason: str = Field(..., description="Reason for rejection")

    class Config:
        json_schema_extra = {
            "example": {
                "rejection_reason": "Incomplete data, missing purchase invoices",
            }
        }


class WorkflowTaskResponse(BaseModel):
    """Full workflow task response with all fields"""

    id: str
    tenant_id: str
    compliance_instance_id: str
    compliance_code: Optional[str] = None
    compliance_name: Optional[str] = None
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    task_type: str
    task_name: str
    task_description: Optional[str] = None
    assigned_to_user_id: Optional[str] = None
    assigned_user_name: Optional[str] = None
    assigned_to_role_id: Optional[str] = None
    assigned_role_name: Optional[str] = None
    status: str
    due_date: Optional[date] = None
    started_at: Optional[date] = None
    completed_at: Optional[date] = None
    sequence_order: int
    parent_task_id: Optional[str] = None
    completion_remarks: Optional[str] = None
    rejection_reason: Optional[str] = None
    meta_data: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "tenant_id": "987fcdeb-51d3-12e8-b456-426614174000",
                "compliance_instance_id": "456e7890-e89b-12d3-a456-426614174000",
                "compliance_code": "GST_GSTR3B",
                "compliance_name": "GSTR-3B Return",
                "entity_id": "789e4567-e89b-12d3-a456-426614174000",
                "entity_name": "GCC India Pvt Ltd",
                "task_type": "Prepare",
                "task_name": "Prepare GSTR-3B return data",
                "task_description": "Collect all sales and purchase data",
                "assigned_to_user_id": "321e4567-e89b-12d3-a456-426614174000",
                "assigned_user_name": "John Doe",
                "status": "In Progress",
                "due_date": "2025-01-15",
                "started_at": "2025-01-10",
                "sequence_order": 1,
                "created_at": "2025-01-01T10:00:00",
                "updated_at": "2025-01-10T14:30:00",
            }
        }


class WorkflowTaskListResponse(BaseModel):
    """Paginated list of workflow tasks"""

    items: list[WorkflowTaskResponse]
    total: int = Field(..., ge=0, description="Total number of items matching the filters")
    skip: int = Field(..., ge=0, description="Number of items skipped (offset)")
    limit: int = Field(..., ge=1, description="Maximum number of items returned")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 15,
                "skip": 0,
                "limit": 50,
            }
        }
