"""
Mock Adapters for Testing (V1 & V2)

Provides mock implementations for testing without actual API calls
"""

from typing import Dict, Any, Optional
from uuid import UUID
from .base_adapter import ExternalAPIAdapter


class MockGSTNAdapter(ExternalAPIAdapter):
    """
    Mock GSTN adapter for testing

    Returns realistic mock data without making actual API calls
    """

    async def authenticate(self) -> bool:
        """Mock authentication - always succeeds"""
        return True

    async def fetch_filing_status(
        self, compliance_code: str, period: str
    ) -> Optional[Dict[str, Any]]:
        """Return mock filing status"""
        return {
            "status": "Filed",
            "filing_date": "2024-04-18",
            "acknowledgment_number": "AB2904240012345",
            "tax_paid": 125000.00,
            "taxable_turnover": 5000000.00,
        }

    async def sync_master_data(self, entity_id: UUID) -> Dict[str, Any]:
        """GSTN doesn't have master data"""
        return {}


class MockMCAAdapter(ExternalAPIAdapter):
    """
    Mock MCA adapter for testing

    Returns realistic mock company data
    """

    async def authenticate(self) -> bool:
        """Mock authentication - always succeeds"""
        return True

    async def fetch_filing_status(
        self, compliance_code: str, period: str
    ) -> Optional[Dict[str, Any]]:
        """Not applicable for MCA"""
        return None

    async def sync_master_data(self, entity_id: UUID) -> Dict[str, Any]:
        """Return mock company data"""
        return {
            "company_name": "ABC Private Limited",
            "cin": "U74999KA2020PTC123456",
            "directors": [
                {"name": "John Doe", "din": "01234567"},
                {"name": "Jane Smith", "din": "76543210"},
            ],
            "authorized_capital": 10000000,
            "upcoming_filings": [
                {"form": "AOC-4", "due_date": "2024-09-30"},
                {"form": "MGT-7", "due_date": "2024-10-30"},
            ],
        }


class MockSAPAdapter(ExternalAPIAdapter):
    """
    Mock SAP adapter for testing

    Returns realistic mock financial data
    """

    async def authenticate(self) -> bool:
        """Mock authentication - always succeeds"""
        return True

    async def fetch_filing_status(
        self, compliance_code: str, period: str
    ) -> Optional[Dict[str, Any]]:
        """Not applicable for SAP"""
        return None

    async def sync_master_data(self, entity_id: UUID) -> Dict[str, Any]:
        """Return empty for SAP"""
        return {}

    async def fetch_pl_statement(self, entity_id: UUID, period: str) -> Optional[Dict[str, Any]]:
        """Return mock P&L data"""
        return {
            "period": period,
            "revenue": 10000000,
            "cogs": 6000000,
            "gross_profit": 4000000,
            "operating_expenses": 2500000,
            "operating_income": 1500000,
            "net_income": 1200000,
        }
