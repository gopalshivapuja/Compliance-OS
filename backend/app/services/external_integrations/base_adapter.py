"""
Base Adapter for External API Integrations (V2)

Abstract base class defining the interface for all external API adapters
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from uuid import UUID


class ExternalAPIAdapter(ABC):
    """
    Abstract base class for all external API integrations

    This ensures consistent interface across all adapters (GSTN, MCA, ERP)
    """

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        """
        Initialize adapter

        Args:
            api_key: API authentication key
            api_url: Base URL for API endpoints
        """
        self.api_key = api_key
        self.api_url = api_url
        self.access_token: Optional[str] = None

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with external service

        Returns:
            bool: True if authentication successful

        NOTE: Each adapter implements its own auth mechanism
              (OAuth, API key, SAML, etc.)
        """
        pass

    @abstractmethod
    async def fetch_filing_status(
        self, compliance_code: str, period: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch filing status from external system

        Args:
            compliance_code: Compliance identifier (e.g., "GSTR-3B")
            period: Filing period (e.g., "032024")

        Returns:
            dict: Filing status data
                {
                    'status': 'Filed',
                    'filing_date': '2024-04-18',
                    'acknowledgment_number': 'AB2904240012345',
                    'amount_paid': 125000.00
                }
        """
        pass

    @abstractmethod
    async def sync_master_data(self, entity_id: UUID) -> Dict[str, Any]:
        """
        Sync entity master data from external system

        Args:
            entity_id: Entity UUID

        Returns:
            dict: Synced master data
        """
        pass

    async def log_sync(
        self,
        tenant_id: UUID,
        entity_id: UUID,
        sync_type: str,
        status: str,
        records_synced: int = 0,
        error_message: Optional[str] = None,
    ):
        """
        Log sync attempt to database

        Args:
            tenant_id: Tenant UUID
            entity_id: Entity UUID
            sync_type: Type of sync (filing_status, master_data, etc.)
            status: Sync status (success, partial_success, failed)
            records_synced: Number of records synced
            error_message: Error message if failed
        """
        # V2 implementation will insert to api_sync_log table
        pass
