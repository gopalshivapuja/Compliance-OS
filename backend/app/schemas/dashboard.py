"""
Dashboard Pydantic schemas for request/response validation
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RAGCounts(BaseModel):
    """RAG status counts (Red, Amber, Green)"""

    green: int = Field(..., ge=0, description="Number of Green (on track) items")
    amber: int = Field(..., ge=0, description="Number of Amber (at risk) items")
    red: int = Field(..., ge=0, description="Number of Red (overdue/critical) items")

    class Config:
        json_schema_extra = {
            "example": {
                "green": 10,
                "amber": 8,
                "red": 6,
            }
        }


class CategoryBreakdown(BaseModel):
    """Breakdown of compliance items by category with RAG distribution"""

    category: str = Field(..., description="Compliance category (GST, Direct Tax, etc.)")
    green: int = Field(..., ge=0)
    amber: int = Field(..., ge=0)
    red: int = Field(..., ge=0)
    total: int = Field(..., ge=0, description="Total items in this category")

    class Config:
        json_schema_extra = {
            "example": {
                "category": "GST",
                "green": 3,
                "amber": 2,
                "red": 1,
                "total": 6,
            }
        }


class DashboardOverviewResponse(BaseModel):
    """Dashboard overview with aggregate metrics"""

    total_compliances: int = Field(..., ge=0, description="Total compliance instances")
    rag_counts: RAGCounts = Field(..., description="RAG status distribution")
    overdue_count: int = Field(..., ge=0, description="Number of overdue items")
    upcoming_count: int = Field(..., ge=0, description="Number of upcoming items (next 7 days)")
    category_breakdown: list[CategoryBreakdown] = Field(
        default_factory=list, description="Breakdown by category"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_compliances": 24,
                "rag_counts": {"green": 10, "amber": 8, "red": 6},
                "overdue_count": 6,
                "upcoming_count": 5,
                "category_breakdown": [
                    {"category": "GST", "green": 3, "amber": 2, "red": 1, "total": 6},
                    {"category": "Direct Tax", "green": 2, "amber": 2, "red": 2, "total": 6},
                ],
            }
        }


class ComplianceInstanceSummary(BaseModel):
    """Summary of a compliance instance for dashboard display"""

    compliance_instance_id: str = Field(..., description="UUID of the compliance instance")
    compliance_name: str = Field(..., description="Name of the compliance")
    compliance_code: str = Field(..., description="Code of the compliance")
    entity_name: str = Field(..., description="Entity this compliance applies to")
    entity_code: str = Field(..., description="Entity code")
    category: str = Field(..., description="Compliance category")
    sub_category: Optional[str] = Field(None, description="Compliance sub-category")
    due_date: datetime = Field(..., description="Due date for this instance")
    rag_status: str = Field(..., description="RAG status (Green, Amber, Red)")
    status: str = Field(..., description="Current status (Not Started, In Progress, etc.)")
    owner_name: Optional[str] = Field(None, description="Name of the owner user")
    frequency: str = Field(..., description="Frequency (monthly, quarterly, annual)")
    period_start: datetime = Field(..., description="Period start date")
    period_end: datetime = Field(..., description="Period end date")
    days_overdue: Optional[int] = Field(
        None, description="Number of days overdue (negative if not overdue)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "compliance_instance_id": "123e4567-e89b-12d3-a456-426614174000",
                "compliance_name": "GSTR-3B Return",
                "compliance_code": "GST_GSTR3B",
                "entity_name": "GCC India Pvt Ltd",
                "entity_code": "GCCINDIA01",
                "category": "GST",
                "sub_category": "Monthly Returns",
                "due_date": "2025-01-20T00:00:00",
                "rag_status": "Green",
                "status": "In Progress",
                "owner_name": "Test Admin",
                "frequency": "monthly",
                "period_start": "2024-12-01T00:00:00",
                "period_end": "2024-12-31T00:00:00",
                "days_overdue": None,
            }
        }
