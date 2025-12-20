"""
Evidence Pydantic schemas for request/response validation
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class EvidenceBase(BaseModel):
    """Base schema for evidence"""

    evidence_name: str = Field(..., description="Evidence file name")
    description: Optional[str] = Field(None, description="Evidence description")

    class Config:
        from_attributes = True


class EvidenceUploadRequest(BaseModel):
    """Schema for evidence upload metadata"""

    compliance_instance_id: str = Field(..., description="Compliance instance ID")
    evidence_name: Optional[str] = Field(None, description="Custom evidence name")
    description: Optional[str] = Field(None, description="Evidence description")
    meta_data: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "compliance_instance_id": "123e4567-e89b-12d3-a456-426614174000",
                "evidence_name": "GSTR-3B Jan 2025",
                "description": "GST return for January 2025",
            }
        }


class EvidenceApprovalRequest(BaseModel):
    """Schema for approving evidence"""

    remarks: Optional[str] = Field(None, description="Approval remarks")

    class Config:
        json_schema_extra = {
            "example": {
                "remarks": "Verified and approved",
            }
        }


class EvidenceRejectionRequest(BaseModel):
    """Schema for rejecting evidence"""

    rejection_reason: str = Field(..., description="Reason for rejection")

    class Config:
        json_schema_extra = {
            "example": {
                "rejection_reason": "Missing required signatures",
            }
        }


class EvidenceResponse(BaseModel):
    """Full evidence response with all fields"""

    id: str
    tenant_id: str
    compliance_instance_id: str
    compliance_code: Optional[str] = None
    compliance_name: Optional[str] = None
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    evidence_name: str
    file_path: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: str
    version: int
    parent_evidence_id: Optional[str] = None
    approval_status: str
    approved_by_user_id: Optional[str] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_remarks: Optional[str] = None
    rejection_reason: Optional[str] = None
    is_immutable: bool
    description: Optional[str] = None
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
                "evidence_name": "GSTR-3B_Jan2025.pdf",
                "file_path": "evidence/2025/01/GSTR-3B_Jan2025.pdf",
                "file_type": "application/pdf",
                "file_size": 245678,
                "file_hash": "a1b2c3d4e5f6...",
                "version": 1,
                "approval_status": "Approved",
                "approved_by_user_id": "321e4567-e89b-12d3-a456-426614174000",
                "approved_by_name": "CFO Name",
                "is_immutable": True,
                "created_at": "2025-01-15T10:00:00",
                "updated_at": "2025-01-15T14:30:00",
            }
        }


class EvidenceListResponse(BaseModel):
    """Paginated list of evidence"""

    items: list[EvidenceResponse]
    total: int = Field(..., ge=0, description="Total number of items matching the filters")
    skip: int = Field(..., ge=0, description="Number of items skipped (offset)")
    limit: int = Field(..., ge=1, description="Maximum number of items returned")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 42,
                "skip": 0,
                "limit": 50,
            }
        }


class EvidenceDownloadResponse(BaseModel):
    """Response for evidence download with signed URL"""

    evidence_id: str
    evidence_name: str
    download_url: str
    expires_in_seconds: int

    class Config:
        json_schema_extra = {
            "example": {
                "evidence_id": "123e4567-e89b-12d3-a456-426614174000",
                "evidence_name": "GSTR-3B_Jan2025.pdf",
                "download_url": "https://s3.amazonaws.com/bucket/...",
                "expires_in_seconds": 300,
            }
        }
