"""
Entity schemas for request/response validation
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re


class EntityBase(BaseModel):
    """Base entity schema with common fields"""

    entity_code: str = Field(..., min_length=2, max_length=50, description="Unique entity code")
    entity_name: str = Field(..., min_length=3, max_length=255, description="Entity name")
    entity_type: Optional[str] = Field(
        None, max_length=50, description="Entity type (Company, Branch, LLP, etc.)"
    )

    # Indian tax identifiers
    pan: Optional[str] = Field(None, max_length=10, description="PAN number")
    gstin: Optional[str] = Field(None, max_length=15, description="GSTIN number")
    cin: Optional[str] = Field(None, max_length=21, description="CIN number")
    tan: Optional[str] = Field(None, max_length=10, description="TAN number")

    # Contact details
    address: Optional[str] = Field(None, description="Full address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State")
    pincode: Optional[str] = Field(None, max_length=10, description="Pincode")
    contact_person: Optional[str] = Field(None, max_length=255, description="Contact person name")
    contact_email: Optional[str] = Field(None, max_length=255, description="Contact email")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Contact phone")

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v: Optional[str]) -> Optional[str]:
        """Validate PAN format (AAAAA9999A)"""
        if v is None:
            return v
        v = v.upper().strip()
        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", v):
            raise ValueError("Invalid PAN format. Expected: AAAAA9999A")
        return v

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v: Optional[str]) -> Optional[str]:
        """Validate GSTIN format (15 characters)"""
        if v is None:
            return v
        v = v.upper().strip()
        if not re.match(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9][Z][0-9A-Z]$", v):
            raise ValueError("Invalid GSTIN format. Expected: 99AAAAA9999A9Z9")
        return v

    @field_validator("cin")
    @classmethod
    def validate_cin(cls, v: Optional[str]) -> Optional[str]:
        """Validate CIN format (21 characters)"""
        if v is None:
            return v
        v = v.upper().strip()
        if not re.match(r"^[A-Z]{1}[0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$", v):
            raise ValueError("Invalid CIN format. Expected: A99999AA9999AAA999999")
        return v


class EntityCreate(EntityBase):
    """Schema for creating a new entity"""

    class Config:
        json_schema_extra = {
            "example": {
                "entity_code": "ACME-MUM",
                "entity_name": "Acme Corporation Mumbai",
                "entity_type": "Company",
                "pan": "AAAPL1234C",
                "gstin": "27AAAPL1234C1Z5",
                "cin": "L17110MH1973PLC019786",
                "address": "123 MG Road, Andheri East",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400069",
                "contact_person": "John Doe",
                "contact_email": "john@acme.com",
                "contact_phone": "+91-22-12345678",
            }
        }


class EntityUpdate(BaseModel):
    """Schema for updating entity (all fields optional)"""

    entity_name: Optional[str] = Field(None, min_length=3, max_length=255)
    entity_type: Optional[str] = Field(None, max_length=50)
    pan: Optional[str] = Field(None, max_length=10)
    gstin: Optional[str] = Field(None, max_length=15)
    cin: Optional[str] = Field(None, max_length=21)
    tan: Optional[str] = Field(None, max_length=10)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)
    contact_person: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, pattern="^(active|inactive)$")

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v: Optional[str]) -> Optional[str]:
        """Validate PAN format"""
        if v is None:
            return v
        v = v.upper().strip()
        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", v):
            raise ValueError("Invalid PAN format")
        return v

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v: Optional[str]) -> Optional[str]:
        """Validate GSTIN format"""
        if v is None:
            return v
        v = v.upper().strip()
        if not re.match(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9][Z][0-9A-Z]$", v):
            raise ValueError("Invalid GSTIN format")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "entity_name": "Updated Entity Name",
                "contact_email": "newemail@acme.com",
                "status": "active",
            }
        }


class EntityResponse(BaseModel):
    """Schema for entity response"""

    id: str = Field(..., description="Entity UUID")
    tenant_id: str = Field(..., description="Tenant UUID")
    entity_code: str = Field(..., description="Entity code")
    entity_name: str = Field(..., description="Entity name")
    entity_type: Optional[str] = Field(None, description="Entity type")
    pan: Optional[str] = None
    gstin: Optional[str] = None
    cin: Optional[str] = None
    tan: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    status: str = Field(..., description="Entity status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    updated_by: Optional[str] = Field(None, description="Last updater user ID")

    # Count of users with access (populated separately)
    users_with_access_count: Optional[int] = Field(0, description="Number of users with access")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "tenant_id": "123e4567-e89b-12d3-a456-426614174001",
                "entity_code": "ACME-MUM",
                "entity_name": "Acme Corporation Mumbai",
                "entity_type": "Company",
                "pan": "AAAPL1234C",
                "gstin": "27AAAPL1234C1Z5",
                "status": "active",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "users_with_access_count": 5,
            }
        }


class EntityListResponse(BaseModel):
    """Paginated list of entities"""

    items: List[EntityResponse] = Field(..., description="List of entities")
    total: int = Field(..., description="Total count of entities")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Number of items per page")

    class Config:
        json_schema_extra = {"example": {"items": [], "total": 10, "skip": 0, "limit": 50}}
