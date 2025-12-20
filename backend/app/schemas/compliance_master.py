"""
Compliance Master schemas for request/response validation
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class ComplianceMasterBase(BaseModel):
    """Base compliance master schema with common fields"""

    compliance_code: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Unique compliance code (e.g., GSTR-1, TDS-24Q)",
    )
    compliance_name: str = Field(..., min_length=3, max_length=255, description="Compliance name")
    description: Optional[str] = Field(None, description="Detailed description")

    # Categorization
    category: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Category: GST, Direct Tax, Payroll, MCA, FEMA, FP&A",
    )
    sub_category: Optional[str] = Field(None, max_length=100, description="Sub-category")

    # Frequency and timing
    frequency: str = Field(
        ...,
        description="Frequency: Monthly, Quarterly, Annual, Event-based",
    )
    due_date_rule: Dict[str, Any] = Field(..., description="JSONB rule for due date calculation")

    # Ownership and approval
    owner_role_code: Optional[str] = Field(None, max_length=50, description="Default owner role")
    approver_role_code: Optional[str] = Field(
        None, max_length=50, description="Default approver role"
    )

    # Dependencies and workflow
    dependencies: Optional[List[str]] = Field(
        None, description="Array of compliance codes this depends on"
    )
    workflow_config: Optional[List[Dict[str, Any]]] = Field(
        None, description="Custom workflow steps configuration"
    )

    # Metadata
    authority: Optional[str] = Field(
        None, max_length=255, description="Regulatory authority (CBIC, Income Tax Dept, etc.)"
    )
    penalty_details: Optional[str] = Field(None, description="Penalty information")
    reference_links: Optional[List[str]] = Field(None, description="Reference URLs")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category is one of the allowed values"""
        allowed = ["GST", "Direct Tax", "Payroll", "MCA", "FEMA", "FP&A"]
        if v not in allowed:
            raise ValueError(f"Invalid category. Must be one of: {', '.join(allowed)}")
        return v

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        """Validate frequency is one of the allowed values"""
        allowed = ["Monthly", "Quarterly", "Annual", "Event-based"]
        if v not in allowed:
            raise ValueError(f"Invalid frequency. Must be one of: {', '.join(allowed)}")
        return v

    @field_validator("due_date_rule")
    @classmethod
    def validate_due_date_rule(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate due_date_rule has required structure"""
        if not isinstance(v, dict):
            raise ValueError("due_date_rule must be a dictionary")
        if "type" not in v:
            raise ValueError("due_date_rule must contain 'type' field")
        return v


class ComplianceMasterCreate(ComplianceMasterBase):
    """Schema for creating a new compliance master"""

    is_template: Optional[bool] = Field(False, description="Whether this is a system-wide template")

    class Config:
        json_schema_extra = {
            "example": {
                "compliance_code": "GSTR-1",
                "compliance_name": "GSTR-1 Monthly Return",
                "description": "Monthly return for outward supplies",
                "category": "GST",
                "sub_category": "Returns",
                "frequency": "Monthly",
                "due_date_rule": {"type": "monthly", "day": 11, "offset_days": 0},
                "owner_role_code": "tax_lead",
                "approver_role_code": "tax_manager",
                "dependencies": [],
                "authority": "CBIC",
                "penalty_details": "Late fee Rs. 50/day (max Rs. 5000)",
                "reference_links": ["https://tutorial.gst.gov.in/"],
                "is_template": False,
            }
        }


class ComplianceMasterUpdate(BaseModel):
    """Schema for updating compliance master (all fields optional)"""

    compliance_name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, min_length=2, max_length=50)
    sub_category: Optional[str] = Field(None, max_length=100)
    frequency: Optional[str] = None
    due_date_rule: Optional[Dict[str, Any]] = None
    owner_role_code: Optional[str] = Field(None, max_length=50)
    approver_role_code: Optional[str] = Field(None, max_length=50)
    dependencies: Optional[List[str]] = None
    workflow_config: Optional[List[Dict[str, Any]]] = None
    authority: Optional[str] = Field(None, max_length=255)
    penalty_details: Optional[str] = None
    reference_links: Optional[List[str]] = None
    meta_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        """Validate category"""
        if v is None:
            return v
        allowed = ["GST", "Direct Tax", "Payroll", "MCA", "FEMA", "FP&A"]
        if v not in allowed:
            raise ValueError(f"Invalid category. Must be one of: {', '.join(allowed)}")
        return v

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: Optional[str]) -> Optional[str]:
        """Validate frequency"""
        if v is None:
            return v
        allowed = ["Monthly", "Quarterly", "Annual", "Event-based"]
        if v not in allowed:
            raise ValueError(f"Invalid frequency. Must be one of: {', '.join(allowed)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "compliance_name": "Updated Compliance Name",
                "description": "Updated description",
                "is_active": True,
            }
        }


class ComplianceMasterResponse(BaseModel):
    """Schema for compliance master response"""

    id: str = Field(..., description="Compliance master UUID")
    tenant_id: Optional[str] = Field(None, description="Tenant UUID (NULL for system templates)")
    compliance_code: str = Field(..., description="Compliance code")
    compliance_name: str = Field(..., description="Compliance name")
    description: Optional[str] = None
    category: str = Field(..., description="Category")
    sub_category: Optional[str] = None
    frequency: str = Field(..., description="Frequency")
    due_date_rule: Dict[str, Any] = Field(..., description="Due date rule")
    owner_role_code: Optional[str] = None
    approver_role_code: Optional[str] = None
    dependencies: Optional[List[str]] = None
    workflow_config: Optional[List[Dict[str, Any]]] = None
    is_active: bool = Field(..., description="Active status")
    is_template: bool = Field(..., description="Is system template")
    authority: Optional[str] = None
    penalty_details: Optional[str] = None
    reference_links: Optional[List[str]] = None
    meta_data: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    updated_by: Optional[str] = Field(None, description="Last updater user ID")

    # Count of instances (populated separately)
    instances_count: Optional[int] = Field(0, description="Number of instances created")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "tenant_id": "123e4567-e89b-12d3-a456-426614174001",
                "compliance_code": "GSTR-1",
                "compliance_name": "GSTR-1 Monthly Return",
                "category": "GST",
                "frequency": "Monthly",
                "due_date_rule": {"type": "monthly", "day": 11, "offset_days": 0},
                "is_active": True,
                "is_template": False,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "instances_count": 12,
            }
        }


class ComplianceMasterListResponse(BaseModel):
    """Paginated list of compliance masters"""

    items: List[ComplianceMasterResponse] = Field(..., description="List of compliance masters")
    total: int = Field(..., description="Total count of compliance masters")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Number of items per page")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 10,
                "skip": 0,
                "limit": 50,
            }
        }


class ComplianceMasterBulkImportRequest(BaseModel):
    """Schema for bulk importing compliance masters"""

    masters: List[ComplianceMasterCreate] = Field(
        ..., description="List of compliance masters to import"
    )
    overwrite_existing: bool = Field(
        False, description="Whether to overwrite existing masters with same code"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "masters": [
                    {
                        "compliance_code": "GSTR-1",
                        "compliance_name": "GSTR-1 Monthly Return",
                        "category": "GST",
                        "frequency": "Monthly",
                        "due_date_rule": {"type": "monthly", "day": 11, "offset_days": 0},
                    }
                ],
                "overwrite_existing": False,
            }
        }


class ComplianceMasterBulkImportResponse(BaseModel):
    """Response for bulk import operation"""

    created_count: int = Field(..., description="Number of masters created")
    updated_count: int = Field(..., description="Number of masters updated")
    skipped_count: int = Field(..., description="Number of masters skipped")
    errors: List[Dict[str, Any]] = Field(..., description="List of errors encountered")

    class Config:
        json_schema_extra = {
            "example": {
                "created_count": 10,
                "updated_count": 2,
                "skipped_count": 1,
                "errors": [],
            }
        }
