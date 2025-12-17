"""
Main API v1 router that includes all endpoint routers
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    tenants,
    entities,
    compliance_masters,
    compliance_instances,
    workflow_tasks,
    evidence,
    audit_logs,
    dashboard,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(entities.router, prefix="/entities", tags=["Entities"])
api_router.include_router(
    compliance_masters.router, prefix="/compliance-masters", tags=["Compliance Masters"]
)
api_router.include_router(
    compliance_instances.router,
    prefix="/compliance-instances",
    tags=["Compliance Instances"],
)
api_router.include_router(
    workflow_tasks.router, prefix="/workflow-tasks", tags=["Workflow Tasks"]
)
api_router.include_router(evidence.router, prefix="/evidence", tags=["Evidence"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

