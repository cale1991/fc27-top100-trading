"""user application, portfolio, community, and public-ledger layer

Revision ID: 0004_application_layer
Revises: 0003_dynamic_market_universe
Create Date: 2026-09-04
"""
from alembic import op
from sqlalchemy import Column, Integer, Numeric, String, Text, inspect

from fc27trader.db.base import Base
from fc27trader.db import models  # noqa: F401

revision = "0004_application_layer"
down_revision = "0003_dynamic_market_universe"
branch_labels = None
depends_on = None

_NEW_TABLES = [
    "trading_accounts",
    "portfolio_positions",
    "portfolio_transactions",
    "activity_feed_items",
    "notifications",
    "service_heartbeats",
    "community_traders",
    "community_content",
    "community_signals",
    "community_signal_outcomes",
    "trader_reputation_snapshots",
    "public_predictions",
    "public_posts",
    "social_market_impacts",
    "persona_state",
]


def upgrade() -> None:
    bind = op.get_bind()
    for name in _NEW_TABLES:
        Base.metadata.tables[name].create(bind=bind, checkfirst=True)

    # 0001 is a create_all bootstrap migration and therefore sees the current metadata on
    # a fresh database. Add evolving columns only when an older database does not have them.
    inspector = inspect(bind)
    opportunity_existing = {c["name"] for c in inspector.get_columns("opportunity_candidates")}
    opportunity_columns = [
        Column("action", String(32), nullable=True),
        Column("max_recommended_buy_price", Integer(), nullable=True),
        Column("target_sell_low", Integer(), nullable=True),
        Column("target_sell_high", Integer(), nullable=True),
        Column("recommended_quantity", Integer(), nullable=True),
        Column("expected_roi", Numeric(12, 8), nullable=True),
        Column("confidence_score", Numeric(8, 6), nullable=True),
        Column("main_catalyst", Text(), nullable=True),
        Column("invalidation_condition", Text(), nullable=True),
        Column("exit_logic", Text(), nullable=True),
    ]
    with op.batch_alter_table("opportunity_candidates") as batch:
        for column in opportunity_columns:
            if column.name not in opportunity_existing:
                batch.add_column(column)

    response_existing = {c["name"] for c in inspect(bind).get_columns("manual_verification_responses")}
    response_columns = [
        Column("input_kind", String(32), nullable=True),
        Column("observation_confidence", Numeric(8, 6), nullable=True),
        Column("observation_age_seconds", Numeric(14, 3), nullable=True),
    ]
    with op.batch_alter_table("manual_verification_responses") as batch:
        for column in response_columns:
            if column.name not in response_existing:
                batch.add_column(column)


def downgrade() -> None:
    with op.batch_alter_table("manual_verification_responses") as batch:
        batch.drop_column("observation_age_seconds")
        batch.drop_column("observation_confidence")
        batch.drop_column("input_kind")

    with op.batch_alter_table("opportunity_candidates") as batch:
        for name in [
            "exit_logic",
            "invalidation_condition",
            "main_catalyst",
            "confidence_score",
            "expected_roi",
            "recommended_quantity",
            "target_sell_high",
            "target_sell_low",
            "max_recommended_buy_price",
            "action",
        ]:
            batch.drop_column(name)

    bind = op.get_bind()
    for name in reversed(_NEW_TABLES):
        Base.metadata.tables[name].drop(bind=bind, checkfirst=True)
