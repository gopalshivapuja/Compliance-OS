"""Add AI and integration tables (V2)

Revision ID: b7d4e5f1c8a2
Revises: a3f8c2b9d4e1
Create Date: 2025-12-19 10:45:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b7d4e5f1c8a2"
down_revision = "a3f8c2b9d4e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add AI and integration tables for V2 features"""

    # Enable pgvector extension for vector embeddings
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create document_embeddings table (for RAG chatbot)
    op.create_table(
        "document_embeddings",
        sa.Column("embedding_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("document_name", sa.String(length=255), nullable=False),
        sa.Column("document_type", sa.String(length=50), nullable=True),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column(
            "embedding", postgresql.ARRAY(sa.Float()), nullable=False
        ),  # 1536-dimensional vector
        sa.Column("compliance_instance_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["compliance_instance_id"], ["compliance_instances.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("embedding_id"),
    )
    op.create_index("idx_document_embeddings_tenant", "document_embeddings", ["tenant_id"])
    op.create_index(
        "idx_document_embeddings_compliance", "document_embeddings", ["compliance_instance_id"]
    )

    # Create compliance_predictions table (for ML risk prediction)
    op.create_table(
        "compliance_predictions",
        sa.Column("prediction_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("compliance_instance_id", sa.UUID(), nullable=False),
        sa.Column(
            "predicted_status", sa.String(length=20), nullable=False
        ),  # on_time, at_risk, likely_late
        sa.Column(
            "confidence_score", sa.Numeric(precision=3, scale=2), nullable=False
        ),  # 0.00 to 1.00
        sa.Column("risk_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("model_version", sa.String(length=50), nullable=True),
        sa.Column("predicted_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["compliance_instance_id"], ["compliance_instances.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("prediction_id"),
    )
    op.create_index("idx_compliance_predictions_tenant", "compliance_predictions", ["tenant_id"])
    op.create_index(
        "idx_compliance_predictions_instance", "compliance_predictions", ["compliance_instance_id"]
    )
    op.create_index(
        "idx_compliance_predictions_status", "compliance_predictions", ["predicted_status"]
    )

    # Create api_sync_log table (for external API integration tracking)
    op.create_table(
        "api_sync_log",
        sa.Column("sync_log_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column(
            "api_provider", sa.String(length=50), nullable=False
        ),  # GSTN, MCA, SAP, ORACLE, NETSUITE
        sa.Column(
            "sync_type", sa.String(length=50), nullable=False
        ),  # filing_status, master_data, financial_data
        sa.Column(
            "sync_status", sa.String(length=20), nullable=False
        ),  # success, partial_success, failed
        sa.Column("records_synced", sa.Integer(), nullable=True, default=0),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["entity_id"], ["entities.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("sync_log_id"),
    )
    op.create_index("idx_api_sync_log_tenant", "api_sync_log", ["tenant_id"])
    op.create_index("idx_api_sync_log_entity", "api_sync_log", ["entity_id"])
    op.create_index("idx_api_sync_log_provider", "api_sync_log", ["api_provider"])
    op.create_index("idx_api_sync_log_status", "api_sync_log", ["sync_status"])
    op.create_index(
        "idx_api_sync_log_created",
        "api_sync_log",
        ["created_at"],
        postgresql_ops={"created_at": "DESC"},
    )


def downgrade() -> None:
    """Remove AI and integration tables"""

    # Drop tables in reverse order
    op.drop_index("idx_api_sync_log_created", table_name="api_sync_log")
    op.drop_index("idx_api_sync_log_status", table_name="api_sync_log")
    op.drop_index("idx_api_sync_log_provider", table_name="api_sync_log")
    op.drop_index("idx_api_sync_log_entity", table_name="api_sync_log")
    op.drop_index("idx_api_sync_log_tenant", table_name="api_sync_log")
    op.drop_table("api_sync_log")

    op.drop_index("idx_compliance_predictions_status", table_name="compliance_predictions")
    op.drop_index("idx_compliance_predictions_instance", table_name="compliance_predictions")
    op.drop_index("idx_compliance_predictions_tenant", table_name="compliance_predictions")
    op.drop_table("compliance_predictions")

    op.drop_index("idx_document_embeddings_compliance", table_name="document_embeddings")
    op.drop_index("idx_document_embeddings_tenant", table_name="document_embeddings")
    op.drop_table("document_embeddings")

    # Disable pgvector extension (optional - comment out if other tables use it)
    # op.execute('DROP EXTENSION IF EXISTS vector')
