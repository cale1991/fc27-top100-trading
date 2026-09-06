"""provider validation schema

Revision ID: 0002_provider_validation
Revises: 0001_initial
Create Date: 2026-09-04
"""
from alembic import op

from fc27trader.db.base import Base
from fc27trader.db import models  # noqa: F401

revision = "0002_provider_validation"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

_TABLES = [
    "provider_validation_runs",
    "provider_validation_observations",
    "provider_qualifications",
]


def upgrade() -> None:
    bind = op.get_bind()
    for name in _TABLES:
        Base.metadata.tables[name].create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for name in reversed(_TABLES):
        Base.metadata.tables[name].drop(bind=bind, checkfirst=True)
