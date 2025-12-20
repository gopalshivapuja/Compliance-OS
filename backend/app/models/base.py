"""
Base model classes and mixins for all database models
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base, declared_attr

Base = declarative_base()


class UUIDMixin:
    """Mixin to add UUID primary key to models"""

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)


class TimestampMixin:
    """Mixin to add timestamp fields to models"""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AuditMixin(TimestampMixin):
    """Mixin to add full audit fields (timestamps + user tracking)"""

    created_by = Column(PGUUID(as_uuid=True), nullable=True)
    updated_by = Column(PGUUID(as_uuid=True), nullable=True)


class TenantScopedMixin:
    """Mixin to add tenant_id for multi-tenant isolation"""

    @declared_attr
    def tenant_id(cls):
        return Column(PGUUID(as_uuid=True), nullable=False, index=True)
