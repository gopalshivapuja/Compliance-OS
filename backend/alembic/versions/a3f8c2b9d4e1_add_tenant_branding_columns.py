"""Add tenant branding columns

Revision ID: a3f8c2b9d4e1
Revises: 5f701fd63a5d
Create Date: 2025-12-19 10:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a3f8c2b9d4e1"
down_revision = "5f701fd63a5d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add branding columns to tenants table for V2 white-labeling feature"""
    # Add logo_url column
    op.add_column("tenants", sa.Column("logo_url", sa.String(length=500), nullable=True))

    # Add primary_color column (hex color code, e.g., #10b981)
    op.add_column("tenants", sa.Column("primary_color", sa.String(length=7), nullable=True))

    # Add secondary_color column (hex color code)
    op.add_column("tenants", sa.Column("secondary_color", sa.String(length=7), nullable=True))

    # Add company_website column
    op.add_column("tenants", sa.Column("company_website", sa.String(length=500), nullable=True))

    # Add support_email column
    op.add_column("tenants", sa.Column("support_email", sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Remove branding columns from tenants table"""
    # Drop columns in reverse order
    op.drop_column("tenants", "support_email")
    op.drop_column("tenants", "company_website")
    op.drop_column("tenants", "secondary_color")
    op.drop_column("tenants", "primary_color")
    op.drop_column("tenants", "logo_url")
