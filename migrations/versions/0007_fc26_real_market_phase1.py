"""FC26 real market data phase 1

Revision ID: 0007_fc26_real_market_phase1
Revises: 0006_portfolio_execution_semantics
Create Date: 2026-09-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

from fc27trader.db.base import Base
from fc27trader.db import models  # noqa: F401

revision = "0007_fc26_real_market_phase1"
down_revision = "0006_portfolio_execution_semantics"
branch_labels = None
depends_on = None

_NEW_TABLES = ["provider_entities", "provider_health"]


def _add_missing_columns(table: str, columns: list[sa.Column]) -> None:
    bind = op.get_bind()
    existing = {c["name"] for c in inspect(bind).get_columns(table)}
    with op.batch_alter_table(table) as batch:
        for column in columns:
            if column.name not in existing:
                batch.add_column(column)


def upgrade() -> None:
    bind = op.get_bind()
    for name in _NEW_TABLES:
        Base.metadata.tables[name].create(bind=bind, checkfirst=True)

    _add_missing_columns("cards", [
        sa.Column("image_id", sa.String(length=256), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
    ])
    _add_missing_columns("card_source_ids", [
        sa.Column("mapping_method", sa.String(length=64), nullable=True),
        sa.Column("mapping_confidence", sa.Numeric(8, 6), nullable=True),
    ])
    _add_missing_columns("reference_price_observations", [
        sa.Column("provider_role", sa.String(length=32), nullable=True, server_default="reference"),
        sa.Column("evidence_class", sa.String(length=32), nullable=True, server_default="measured_provider"),
        sa.Column("observation_key", sa.String(length=64), nullable=True),
    ])
    # Existing rows predate observation keys. Keep them nullable; new writes populate keys.
    try:
        op.create_index("ix_reference_price_observations_observation_key", "reference_price_observations", ["observation_key"], unique=True)
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_index("ix_reference_price_observations_observation_key", table_name="reference_price_observations")
    except Exception:
        pass
    with op.batch_alter_table("reference_price_observations") as batch:
        for name in ["observation_key", "evidence_class", "provider_role"]:
            try:
                batch.drop_column(name)
            except Exception:
                pass
    with op.batch_alter_table("card_source_ids") as batch:
        for name in ["mapping_confidence", "mapping_method"]:
            try:
                batch.drop_column(name)
            except Exception:
                pass
    with op.batch_alter_table("cards") as batch:
        for name in ["image_url", "image_id"]:
            try:
                batch.drop_column(name)
            except Exception:
                pass
    bind = op.get_bind()
    for name in reversed(_NEW_TABLES):
        Base.metadata.tables[name].drop(bind=bind, checkfirst=True)
