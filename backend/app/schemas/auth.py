"""
Authentication schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional


class LoginRequest(BaseModel):
    """Request schema for user login"""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
            }
        }


class UserResponse(BaseModel):
    """User information in token response"""

    user_id: str = Field(..., description="User UUID")
    tenant_id: str = Field(..., description="Tenant UUID")
    email: EmailStr = Field(..., description="User email")
    first_name: str = Field(..., description="User first name")
    last_name: str = Field(..., description="User last name")
    full_name: str = Field(..., description="User full name")
    roles: List[str] = Field(default_factory=list, description="User role codes")
    is_system_admin: bool = Field(default=False, description="System admin flag")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "tenant_id": "123e4567-e89b-12d3-a456-426614174001",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "roles": ["CFO", "TAX_LEAD"],
                "is_system_admin": False,
            }
        }


class TokenResponse(BaseModel):
    """Response schema for authentication endpoints"""

    access_token: str = Field(..., description="JWT access token (30min TTL)")
    refresh_token: str = Field(..., description="Refresh token (7-day TTL)")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="Authenticated user information")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "def50200abc...",
                "token_type": "bearer",
                "user": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "tenant_id": "123e4567-e89b-12d3-a456-426614174001",
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "full_name": "John Doe",
                    "roles": ["CFO"],
                    "is_system_admin": False,
                },
            }
        }


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh"""

    refresh_token: str = Field(..., description="Valid refresh token")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "def50200abc...",
            }
        }


class LogoutRequest(BaseModel):
    """Request schema for logout (optional body)"""

    refresh_token: Optional[str] = Field(None, description="Refresh token to invalidate")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "def50200abc...",
            }
        }
