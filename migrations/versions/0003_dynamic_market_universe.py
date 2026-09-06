"""dynamic production market universe and observation roles

Revision ID: 0003_dynamic_market_universe
Revises: 0002_provider_validation
Create Date: 2026-09-04
"""
from alembic import op

from fc27trader.db.base import Base
from fc27trader.db import models  # noqa: F401

revision = "0003_dynamic_market_universe"
down_revision = "0002_provider_validation"
branch_labels = None
depends_on = None

_TABLES = [
    "reference_price_observations",
    "execution_observations",
    "opportunity_candidates",
    "manual_verification_requests",
    "manual_verification_responses",
    "attention_allocations",
    "acquisition_opportunity_observations",
    "shadow_execution_attempts",
]


def upgrade() -> None:
    bind = op.get_bind()
    for name in _TABLES:
        Base.metadata.tables[name].create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for name in reversed(_TABLES):
        Base.metadata.tables[name].drop(bind=bind, checkfirst=True)
