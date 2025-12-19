"""
Compliance Prediction model for ML-based risk prediction (V2)
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, UUID as SQLAlchemyUUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import uuid


class CompliancePrediction(Base):
    """
    ML predictions for compliance instance late filing risk

    Uses XGBoost model to predict if a compliance instance is likely to be filed late
    based on historical data, entity characteristics, and current status
    """

    __tablename__ = "compliance_predictions"

    prediction_id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    compliance_instance_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("compliance_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    predicted_status = Column(
        String(20), nullable=False, index=True
    )  # on_time, at_risk, likely_late
    confidence_score = Column(Numeric(3, 2), nullable=False)  # 0.00 to 1.00
    risk_factors = Column(JSONB, nullable=True)  # JSON array of contributing risk factors
    model_version = Column(String(50), nullable=True)  # e.g., "xgboost_v1.2"
    predicted_at = Column(DateTime, nullable=False, server_default=func.now())
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    tenant = relationship("Tenant")
    compliance_instance = relationship("ComplianceInstance")

    def __repr__(self):
        return f"<CompliancePrediction {self.prediction_id}: {self.predicted_status} ({self.confidence_score})>"
