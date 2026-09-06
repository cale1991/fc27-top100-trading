"""historical trading strategy intelligence

Revision ID: 0005_strategy_intelligence
Revises: 0004_application_layer
Create Date: 2026-09-04
"""
from alembic import op

from fc27trader.db.base import Base
from fc27trader.db import models  # noqa: F401

revision = "0005_strategy_intelligence"
down_revision = "0004_application_layer"
branch_labels = None
depends_on = None

_NEW_TABLES = [
    "strategy_library",
    "strategy_aliases",
    "strategy_evidence",
    "strategy_cycle_assessments",
    "strategy_backtest_runs",
    "strategy_performance_snapshots",
    "opportunity_strategy_matches",
    "strategy_trader_performance",
    "strategy_discovery_candidates",
    "community_signal_strategy_links",
]


def upgrade() -> None:
    bind = op.get_bind()
    for name in _NEW_TABLES:
        Base.metadata.tables[name].create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for name in reversed(_NEW_TABLES):
        Base.metadata.tables[name].drop(bind=bind, checkfirst=True)
