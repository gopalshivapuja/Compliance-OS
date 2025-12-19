"""
Tenant schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class TenantBase(BaseModel):
    """Base tenant schema with common fields"""

    tenant_code: str = Field(..., min_length=2, max_length=50, description="Unique tenant code")
    tenant_name: str = Field(
        ..., min_length=2, max_length=255, description="Tenant organization name"
    )
    contact_email: Optional[EmailStr] = Field(None, description="Primary contact email")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Contact phone")
    address: Optional[str] = Field(None, description="Organization address")


class TenantCreate(TenantBase):
    """Schema for creating a new tenant"""

    status: Optional[str] = Field(
        default="active",
        pattern="^(active|suspended|inactive)$",
        description="Tenant status",
    )
    meta_data: Optional[Dict[str, Any]] = Field(
        None, description="Tenant-specific metadata (JSONB)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_code": "ACME001",
                "tenant_name": "Acme Corporation India Pvt Ltd",
                "contact_email": "admin@acme.com",
                "contact_phone": "+91-80-12345678",
                "address": "123 MG Road, Bangalore, Karnataka 560001",
                "status": "active",
                "meta_data": {
                    "industry": "Technology",
                    "employee_count": 500,
                    "subscription_tier": "enterprise",
                },
            }
        }


class TenantUpdate(BaseModel):
    """Schema for updating tenant (all fields optional)"""

    tenant_name: Optional[str] = Field(None, min_length=2, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|suspended|inactive)$")
    meta_data: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_name": "Acme Corporation India Pvt Ltd",
                "contact_email": "newadmin@acme.com",
                "contact_phone": "+91-80-98765432",
                "status": "active",
            }
        }


class TenantResponse(TenantBase):
    """Tenant response schema with all fields"""

    id: str = Field(..., description="Tenant UUID")
    status: str = Field(..., description="Tenant status")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Metadata (JSONB)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    updated_by: Optional[str] = Field(None, description="Last updater user ID")

    @classmethod
    def model_validate(cls, obj):
        """Convert UUID fields to strings"""
        if hasattr(obj, "id"):
            obj_dict = {
                "id": str(obj.id),
                "tenant_code": obj.tenant_code,
                "tenant_name": obj.tenant_name,
                "contact_email": obj.contact_email,
                "contact_phone": obj.contact_phone,
                "address": obj.address,
                "status": obj.status,
                "meta_data": obj.meta_data,
                "created_at": obj.created_at,
                "updated_at": obj.updated_at,
                "created_by": str(obj.created_by) if obj.created_by else None,
                "updated_by": str(obj.updated_by) if obj.updated_by else None,
            }
            return super().model_validate(obj_dict)
        return super().model_validate(obj)

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "tenant_code": "ACME001",
                "tenant_name": "Acme Corporation India Pvt Ltd",
                "contact_email": "admin@acme.com",
                "contact_phone": "+91-80-12345678",
                "address": "123 MG Road, Bangalore, Karnataka 560001",
                "status": "active",
                "meta_data": {"industry": "Technology", "employee_count": 500},
                "created_at": "2024-12-01T10:00:00Z",
                "updated_at": "2024-12-15T14:30:00Z",
                "created_by": "123e4567-e89b-12d3-a456-426614174001",
                "updated_by": "123e4567-e89b-12d3-a456-426614174001",
            }
        }


class TenantListResponse(BaseModel):
    """Response schema for paginated tenant list"""

    tenants: List[TenantResponse] = Field(..., description="List of tenants")
    total: int = Field(..., description="Total number of tenants")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")

    class Config:
        json_schema_extra = {
            "example": {
                "tenants": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "tenant_code": "ACME001",
                        "tenant_name": "Acme Corporation",
                        "status": "active",
                        "created_at": "2024-12-01T10:00:00Z",
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 50,
            }
        }
