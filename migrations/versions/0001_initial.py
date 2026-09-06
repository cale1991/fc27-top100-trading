"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-04

Bootstrap revision. It creates the SQLAlchemy schema exactly as defined in db/models.py.
TimescaleDB is installed by infrastructure, but hypertable conversion is deliberately deferred:
our time-series rows currently use single-column surrogate primary keys that are referenced by
shadow/provenance tables, while Timescale unique constraints must include the partition key.
Reliability beats prematurely forcing hypertables. Convert in an explicit later migration after
that key design is finalized and load-tested.
"""
from alembic import op

from fc27trader.db.base import Base
from fc27trader.db import models  # noqa: F401

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
