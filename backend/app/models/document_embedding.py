"""
Document Embedding model for RAG chatbot (V2)
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UUID as SQLAlchemyUUID
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import uuid


class DocumentEmbedding(Base):
    """
    Document embeddings for RAG-based compliance chatbot

    Stores text chunks with their Claude embeddings (1536-dimensional vectors)
    for semantic search and question answering
    """

    __tablename__ = "document_embeddings"

    embedding_id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_name = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=True)  # Evidence, ComplianceGuide, TaxLaw, etc.
    chunk_text = Column(Text, nullable=False)
    embedding = Column(ARRAY(float), nullable=False)  # 1536-dimensional vector from Claude
    compliance_instance_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("compliance_instances.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    tenant = relationship("Tenant")
    compliance_instance = relationship("ComplianceInstance")

    def __repr__(self):
        return f"<DocumentEmbedding {self.embedding_id}: {self.document_name}>"
