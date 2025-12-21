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
    ComplianceInstanceCreate,
    ComplianceInstanceResponse,
    ComplianceInstanceListResponse,
    ComplianceInstanceUpdate,
)
from app.schemas.audit import (
    AuditLogResponse,
    AuditLogListResponse,
    ResourceAuditTrailResponse,
)
from app.schemas.tenant import (
    TenantBase,
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantListResponse,
)
from app.schemas.entity import (
    EntityBase,
    EntityCreate,
    EntityUpdate,
    EntityResponse,
    EntityListResponse,
)
from app.schemas.compliance_master import (
    ComplianceMasterBase,
    ComplianceMasterCreate,
    ComplianceMasterUpdate,
    ComplianceMasterResponse,
    ComplianceMasterListResponse,
    ComplianceMasterBulkImportRequest,
    ComplianceMasterBulkImportResponse,
)
from app.schemas.workflow_task import (
    WorkflowTaskBase,
    WorkflowTaskCreate,
    WorkflowTaskUpdate,
    WorkflowTaskActionRequest,
    WorkflowTaskRejectRequest,
    WorkflowTaskResponse,
    WorkflowTaskListResponse,
)
from app.schemas.evidence import (
    EvidenceBase,
    EvidenceUploadRequest,
    EvidenceApprovalRequest,
    EvidenceRejectionRequest,
    EvidenceResponse,
    EvidenceListResponse,
    EvidenceDownloadResponse,
)
from app.schemas.notification import (
    NotificationBase,
    NotificationResponse,
    NotificationListResponse,
    NotificationCountResponse,
    NotificationMarkReadRequest,
    NotificationMarkReadResponse,
    NotificationDeleteRequest,
    NotificationDeleteResponse,
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
    "ComplianceInstanceCreate",
    "ComplianceInstanceResponse",
    "ComplianceInstanceListResponse",
    "ComplianceInstanceUpdate",
    # Audit Log schemas
    "AuditLogResponse",
    "AuditLogListResponse",
    "ResourceAuditTrailResponse",
    # Tenant schemas
    "TenantBase",
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    "TenantListResponse",
    # Entity schemas
    "EntityBase",
    "EntityCreate",
    "EntityUpdate",
    "EntityResponse",
    "EntityListResponse",
    # Compliance Master schemas
    "ComplianceMasterBase",
    "ComplianceMasterCreate",
    "ComplianceMasterUpdate",
    "ComplianceMasterResponse",
    "ComplianceMasterListResponse",
    "ComplianceMasterBulkImportRequest",
    "ComplianceMasterBulkImportResponse",
    # Workflow Task schemas
    "WorkflowTaskBase",
    "WorkflowTaskCreate",
    "WorkflowTaskUpdate",
    "WorkflowTaskActionRequest",
    "WorkflowTaskRejectRequest",
    "WorkflowTaskResponse",
    "WorkflowTaskListResponse",
    # Evidence schemas
    "EvidenceBase",
    "EvidenceUploadRequest",
    "EvidenceApprovalRequest",
    "EvidenceRejectionRequest",
    "EvidenceResponse",
    "EvidenceListResponse",
    "EvidenceDownloadResponse",
    # Notification schemas
    "NotificationBase",
    "NotificationResponse",
    "NotificationListResponse",
    "NotificationCountResponse",
    "NotificationMarkReadRequest",
    "NotificationMarkReadResponse",
    "NotificationDeleteRequest",
    "NotificationDeleteResponse",
]
