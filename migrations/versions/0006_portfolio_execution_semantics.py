"""portfolio executable mark and desired listing semantics

Revision ID: 0006_portfolio_execution_semantics
Revises: 0005_strategy_intelligence
Create Date: 2026-09-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0006_portfolio_execution_semantics"
down_revision = "0005_strategy_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = {c["name"] for c in inspect(bind).get_columns("portfolio_positions")}
    if "desired_listing_price" not in existing:
        op.add_column("portfolio_positions", sa.Column("desired_listing_price", sa.Integer(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    existing = {c["name"] for c in inspect(bind).get_columns("portfolio_positions")}
    if "desired_listing_price" in existing:
        op.drop_column("portfolio_positions", "desired_listing_price")
