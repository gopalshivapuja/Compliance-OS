"""
User schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields"""

    email: EmailStr = Field(..., description="User email address")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")


class UserCreate(UserBase):
    """Schema for creating a new user"""

    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    tenant_id: str = Field(..., description="Tenant UUID")
    is_system_admin: bool = Field(default=False, description="System admin flag")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "first_name": "Jane",
                "last_name": "Smith",
                "phone": "+1-555-0100",
                "password": "SecurePass123!",
                "tenant_id": "123e4567-e89b-12d3-a456-426614174001",
                "is_system_admin": False,
            }
        }


class UserUpdate(BaseModel):
    """Schema for updating user information (all fields optional)"""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, pattern="^(active|inactive|suspended)$")

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Jane",
                "last_name": "Smith",
                "phone": "+1-555-0100",
                "status": "active",
            }
        }


class UserInDB(UserBase):
    """User schema with database fields (for internal use)"""

    user_id: str = Field(..., description="User UUID")
    tenant_id: str = Field(..., description="Tenant UUID")
    status: str = Field(..., description="User status (active, inactive, suspended)")
    is_system_admin: bool = Field(..., description="System admin flag")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    roles: List[str] = Field(default_factory=list, description="User role codes")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "tenant_id": "123e4567-e89b-12d3-a456-426614174001",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1-555-0100",
                "status": "active",
                "is_system_admin": False,
                "last_login_at": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "roles": ["CFO", "TAX_LEAD"],
            }
        }


class UserListResponse(BaseModel):
    """Paginated list of users"""

    items: List[UserInDB] = Field(..., description="List of users")
    total: int = Field(..., description="Total count of users")
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
