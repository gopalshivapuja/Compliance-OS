"""
Compliance Instance Pydantic schemas for request/response validation
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class ComplianceInstanceBase(BaseModel):
    """Base schema for compliance instance"""

    compliance_instance_id: str
    compliance_master_id: str
    compliance_code: str = Field(..., description="Denormalized compliance code for performance")
    compliance_name: str = Field(..., description="Denormalized compliance name")
    entity_id: str
    entity_name: str = Field(..., description="Denormalized entity name")
    entity_code: str = Field(..., description="Denormalized entity code")
    category: str
    sub_category: Optional[str] = None
    frequency: str
    due_date: date
    status: str
    rag_status: str
    period_start: date
    period_end: date

    class Config:
        from_attributes = True


class ComplianceInstanceResponse(ComplianceInstanceBase):
    """Full compliance instance response with all fields"""

    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    approver_id: Optional[str] = None
    approver_name: Optional[str] = None
    filed_date: Optional[date] = None
    completion_date: Optional[date] = None
    completion_remarks: Optional[str] = None
    remarks: Optional[str] = None
    meta_data: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "compliance_instance_id": "123e4567-e89b-12d3-a456-426614174000",
                "compliance_master_id": "987fcdeb-51d3-12e8-b456-426614174000",
                "compliance_code": "GST_GSTR3B",
                "compliance_name": "GSTR-3B Return",
                "entity_id": "456e7890-e89b-12d3-a456-426614174000",
                "entity_name": "GCC India Pvt Ltd",
                "entity_code": "GCCINDIA01",
                "category": "GST",
                "sub_category": "Monthly Returns",
                "frequency": "monthly",
                "due_date": "2025-01-20",
                "status": "In Progress",
                "rag_status": "Green",
                "period_start": "2024-12-01",
                "period_end": "2024-12-31",
                "owner_id": "789e4567-e89b-12d3-a456-426614174000",
                "owner_name": "Test Admin",
                "created_at": "2024-12-01T10:00:00",
                "updated_at": "2024-12-15T14:30:00",
            }
        }


class ComplianceInstanceListResponse(BaseModel):
    """Paginated list of compliance instances"""

    items: list[ComplianceInstanceResponse]
    total: int = Field(..., ge=0, description="Total number of items matching the filters")
    skip: int = Field(..., ge=0, description="Number of items skipped (offset)")
    limit: int = Field(..., ge=1, description="Maximum number of items returned")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 24,
                "skip": 0,
                "limit": 50,
            }
        }


class ComplianceInstanceCreate(BaseModel):
    """Schema for creating a compliance instance"""

    compliance_master_id: str = Field(..., description="ID of the compliance master")
    entity_id: str = Field(..., description="ID of the entity")
    period_start: date = Field(..., description="Start of the compliance period")
    period_end: date = Field(..., description="End of the compliance period")
    due_date: date = Field(..., description="Due date for compliance")
    status: Optional[str] = Field(default="Not Started", description="Instance status")
    rag_status: Optional[str] = Field(default="Green", description="RAG status")
    owner_user_id: Optional[str] = Field(None, description="Owner user ID")
    approver_user_id: Optional[str] = Field(None, description="Approver user ID")
    remarks: Optional[str] = Field(None, description="Additional remarks")

    class Config:
        json_schema_extra = {
            "example": {
                "compliance_master_id": "123e4567-e89b-12d3-a456-426614174000",
                "entity_id": "456e7890-e89b-12d3-a456-426614174000",
                "period_start": "2024-12-01",
                "period_end": "2024-12-31",
                "due_date": "2025-01-20",
                "status": "Not Started",
                "rag_status": "Green",
            }
        }


class ComplianceInstanceUpdate(BaseModel):
    """Schema for updating a compliance instance"""

    status: Optional[str] = None
    rag_status: Optional[str] = None
    owner_user_id: Optional[str] = None
    approver_user_id: Optional[str] = None
    filed_date: Optional[date] = None
    completion_date: Optional[date] = None
    completion_remarks: Optional[str] = None
    remarks: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "Filed",
                "completion_date": "2024-12-20",
                "completion_remarks": "Filed successfully through GST portal",
            }
        }
