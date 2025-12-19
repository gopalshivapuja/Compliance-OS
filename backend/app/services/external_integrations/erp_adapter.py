"""
ERP Adapters (V2)

Integrations with ERP systems for FP&A data import
Supports: SAP S/4HANA, Oracle Financials, NetSuite
"""

from typing import Dict, Any, Optional
from uuid import UUID
from .base_adapter import ExternalAPIAdapter


class ERPAdapter(ExternalAPIAdapter):
    """
    Base ERP adapter

    Provides common interface for all ERP systems
    """

    async def authenticate(self) -> bool:
        """Authenticate with ERP system"""
        return False

    async def fetch_filing_status(
        self, compliance_code: str, period: str
    ) -> Optional[Dict[str, Any]]:
        """Not applicable for ERP systems"""
        return None

    async def sync_master_data(self, entity_id: UUID) -> Dict[str, Any]:
        """Sync entity master data"""
        return {}

    async def fetch_pl_statement(self, entity_id: UUID, period: str) -> Optional[Dict[str, Any]]:
        """
        Fetch P&L statement for FP&A compliance

        Args:
            entity_id: Entity UUID
            period: Financial period (e.g., "202403")

        Returns:
            dict: P&L data

        NOTE: V1 stub - returns None
        """
        return None

    async def fetch_balance_sheet(self, entity_id: UUID, period: str) -> Optional[Dict[str, Any]]:
        """
        Fetch balance sheet

        Args:
            entity_id: Entity UUID
            period: Financial period

        Returns:
            dict: Balance sheet data

        NOTE: V1 stub - returns None
        """
        return None


class SAPAdapter(ERPAdapter):
    """
    SAP S/4HANA adapter using OData API

    NOTE: V1 stub - all methods return None/empty
          V2 implementation will use SAP OData API
    """

    async def authenticate(self) -> bool:
        """Authenticate with SAP using OAuth 2.0"""
        # V1: No auth
        return False

        # V2 implementation:
        # response = httpx.post(
        #     f"{self.api_url}/oauth/token",
        #     data={
        #         "grant_type": "client_credentials",
        #         "client_id": settings.SAP_CLIENT_ID,
        #         "client_secret": settings.SAP_CLIENT_SECRET
        #     }
        # )
        # self.access_token = response.json()["access_token"]
        # return True

    async def fetch_pl_statement(self, entity_id: UUID, period: str) -> Optional[Dict[str, Any]]:
        """Fetch P&L from SAP"""
        # V1: Return None
        return None

        # V2 implementation:
        # company_code = entity.sap_company_code
        #
        # response = httpx.get(
        #     f"{self.api_url}/odata/sap/ProfitAndLoss",
        #     params={
        #         "CompanyCode": company_code,
        #         "FiscalPeriod": period
        #     },
        #     headers={"Authorization": f"Bearer {self.access_token}"}
        # )
        #
        # return response.json()


class OracleAdapter(ERPAdapter):
    """
    Oracle Financials adapter using REST API

    NOTE: V1 stub - all methods return None/empty
          V2 implementation will use Oracle Cloud REST API
    """

    async def authenticate(self) -> bool:
        """Authenticate with Oracle using Basic Auth"""
        # V1: No auth
        return False

    async def fetch_pl_statement(self, entity_id: UUID, period: str) -> Optional[Dict[str, Any]]:
        """Fetch P&L from Oracle Financials"""
        # V1: Return None
        return None


class NetSuiteAdapter(ERPAdapter):
    """
    NetSuite adapter using SuiteTalk SOAP API

    NOTE: V1 stub - all methods return None/empty
          V2 implementation will use NetSuite SuiteTalk API
    """

    async def authenticate(self) -> bool:
        """Authenticate with NetSuite using Token-Based Auth"""
        # V1: No auth
        return False

    async def fetch_pl_statement(self, entity_id: UUID, period: str) -> Optional[Dict[str, Any]]:
        """Fetch P&L from NetSuite"""
        # V1: Return None
        return None
