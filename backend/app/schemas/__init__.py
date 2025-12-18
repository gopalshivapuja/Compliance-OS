"""
Pydantic schemas for request/response validation
"""
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
    LogoutRequest,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserInDB,
    UserListResponse,
)
from app.schemas.dashboard import (
    RAGCounts,
    CategoryBreakdown,
    DashboardOverviewResponse,
    ComplianceInstanceSummary,
)
from app.schemas.compliance_instance import (
    ComplianceInstanceBase,
    ComplianceInstanceResponse,
    ComplianceInstanceListResponse,
    ComplianceInstanceUpdate,
)
from app.schemas.audit import (
    AuditLogResponse,
    AuditLogListResponse,
    ResourceAuditTrailResponse,
)

__all__ = [
    # Auth schemas
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "RefreshTokenRequest",
    "LogoutRequest",
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserListResponse",
    # Dashboard schemas
    "RAGCounts",
    "CategoryBreakdown",
    "DashboardOverviewResponse",
    "ComplianceInstanceSummary",
    # Compliance Instance schemas
    "ComplianceInstanceBase",
    "ComplianceInstanceResponse",
    "ComplianceInstanceListResponse",
    "ComplianceInstanceUpdate",
    # Audit Log schemas
    "AuditLogResponse",
    "AuditLogListResponse",
    "ResourceAuditTrailResponse",
]
