"""
API Sync Log model for external API integration tracking (V2)
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, UUID as SQLAlchemyUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import uuid


class APISyncLog(Base):
    """
    Audit log for external API synchronization attempts

    Tracks sync attempts with GSTN, MCA, SAP, Oracle, NetSuite
    for filing status, master data, and financial data
    """

    __tablename__ = "api_sync_log"

    sync_log_id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("entities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    api_provider = Column(
        String(50), nullable=False, index=True
    )  # GSTN, MCA, SAP, ORACLE, NETSUITE
    sync_type = Column(String(50), nullable=False)  # filing_status, master_data, financial_data
    sync_status = Column(String(20), nullable=False, index=True)  # success, partial_success, failed
    records_synced = Column(Integer, nullable=True, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    # Relationships
    tenant = relationship("Tenant")
    entity = relationship("Entity")

    def __repr__(self):
        return f"<APISyncLog {self.sync_log_id}: {self.api_provider} - {self.sync_status}>"
