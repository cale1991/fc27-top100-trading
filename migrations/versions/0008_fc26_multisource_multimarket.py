"""FC26 Phase 2 multi-source multi-market intelligence

Revision ID: 0008_fc26_multisource_multimarket
Revises: 0007_fc26_real_market_phase1
Create Date: 2026-09-04
"""
from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

from fc27trader.db.base import Base
from fc27trader.db import models  # noqa: F401

revision = "0008_fc26_multisource_multimarket"
down_revision = "0007_fc26_real_market_phase1"
branch_labels = None
depends_on = None

_NEW_TABLES = [
    "market_segments",
    "provider_feed_events",
    "provider_feed_states",
    "provider_budget_states",
    "provider_audit_records",
    "derived_feature_snapshots",
    "provider_reliability_snapshots",
    "historical_import_batches",
    "recommendation_ledger",
    "account_constraints",
    "account_market_access",
]


def _columns(table: str) -> set[str]:
    return {c["name"] for c in inspect(op.get_bind()).get_columns(table)}


def _add_missing(table: str, columns: list[sa.Column]) -> None:
    existing = _columns(table)
    with op.batch_alter_table(table) as batch:
        for column in columns:
            if column.name not in existing:
                batch.add_column(column)


def _index(name: str, table: str, columns: list[str], unique: bool = False) -> None:
    existing = {i["name"] for i in inspect(op.get_bind()).get_indexes(table)}
    if name not in existing:
        op.create_index(name, table, columns, unique=unique)


def _seed_segments() -> dict[tuple[int, str], uuid.UUID]:
    bind = op.get_bind()
    table = Base.metadata.tables["market_segments"]
    rows = {}
    definitions = {
        26: [("PC", "PC", "pc", "pc", True), ("PLAYSTATION", "PlayStation (provider-labelled)", "playstation", "playstation_provider", False), ("CONSOLE_GENERIC", "Console (provider-defined)", "console", "console_provider", False), ("CONSOLE_SHARED", "Shared console market", "console", "console_shared", False), ("SWITCH", "Switch", "switch", "switch", False), ("UNKNOWN", "Unknown / unspecified", "unknown", "unknown", False)],
        27: [("PC", "PC", "pc", "pc", False), ("PLAYSTATION", "PlayStation (provider-labelled)", "playstation", "playstation_provider", False), ("CONSOLE_GENERIC", "Console (provider-defined)", "console", "console_provider", False), ("CONSOLE_SHARED", "Shared console market", "console", "configurable_console", False), ("SWITCH", "Switch", "switch", "switch", False), ("UNKNOWN", "Unknown / unspecified", "unknown", "unknown", False)],
    }
    for game_year, specs in definitions.items():
        for key, name, platform, group, executable in specs:
            current = bind.execute(sa.select(table.c.id).where(table.c.game_year == game_year, table.c.segment_key == key)).scalar_one_or_none()
            if current is None:
                current = uuid.uuid4()
                bind.execute(table.insert().values(
                    id=current, game_year=game_year, segment_key=key, display_name=name,
                    platform=platform, platform_group=group, executable_by_user=executable,
                    provider_support_json={}, metadata_json={}, notes=None,
                ))
            rows[(game_year, key)] = current
    return rows


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.tables["market_segments"].create(bind=bind, checkfirst=True)
    segments = _seed_segments()

    _add_missing("raw_ingests", [
        sa.Column("schema_version", sa.String(64), nullable=True),
        sa.Column("inserted_at", sa.DateTime(timezone=True), nullable=True),
    ])
    _add_missing("card_source_ids", [sa.Column("mapping_status", sa.String(32), nullable=True)])
    _add_missing("provider_health", [
        sa.Column("status", sa.String(32), nullable=True),
        sa.Column("access_type", sa.String(32), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("supported_segments_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("retry_after_seconds", sa.Integer(), nullable=True),
        sa.Column("items_seen", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("items_ingested", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("duplicates_skipped", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("quarantined_observations", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("parsing_failures", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("normalization_failures", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("identity_failures", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("last_poll_duration_ms", sa.Numeric(14, 3), nullable=True),
        sa.Column("gap_status", sa.String(32), nullable=True),
        sa.Column("platform_certainty", sa.Numeric(8, 6), nullable=True),
    ])
    _add_missing("reference_price_observations", [
        sa.Column("market_segment_id", sa.UUID(), sa.ForeignKey("market_segments.id"), nullable=True),
        sa.Column("inserted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quality_status", sa.String(32), nullable=False, server_default="VALID"),
        sa.Column("state_completeness", sa.String(32), nullable=False, server_default="directly_observed"),
        sa.Column("is_backfill", sa.Boolean(), nullable=False, server_default=sa.false()),
    ])
    _add_missing("execution_observations", [
        sa.Column("market_segment_id", sa.UUID(), sa.ForeignKey("market_segments.id"), nullable=True),
        sa.Column("inserted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quality_status", sa.String(32), nullable=False, server_default="VALID"),
    ])
    _add_missing("opportunity_candidates", [
        sa.Column("market_segment_id", sa.UUID(), sa.ForeignKey("market_segments.id"), nullable=True),
        sa.Column("actionable", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("signal_scope", sa.String(32), nullable=False, server_default="ACTIONABLE"),
    ])
    _add_missing("manual_verification_requests", [sa.Column("market_segment_id", sa.UUID(), sa.ForeignKey("market_segments.id"), nullable=True)])
    _add_missing("manual_verification_responses", [sa.Column("market_segment_id", sa.UUID(), sa.ForeignKey("market_segments.id"), nullable=True)])
    _add_missing("trading_accounts", [sa.Column("game_year", sa.Integer(), nullable=False, server_default="26")])
    _add_missing("portfolio_positions", [sa.Column("market_segment_id", sa.UUID(), sa.ForeignKey("market_segments.id"), nullable=True)])
    _add_missing("portfolio_transactions", [sa.Column("market_segment_id", sa.UUID(), sa.ForeignKey("market_segments.id"), nullable=True)])

    pc_id = segments[(26, "PC")]
    legacy_pc_tables = {"manual_verification_requests", "manual_verification_responses", "portfolio_positions", "portfolio_transactions"}
    for table in ("reference_price_observations", "execution_observations", "opportunity_candidates", "manual_verification_requests", "manual_verification_responses", "portfolio_positions", "portfolio_transactions"):
        columns = _columns(table)
        if "market_segment_id" not in columns:
            continue
        if "platform" in columns:
            bind.execute(sa.text(f"UPDATE {table} SET market_segment_id = :pc WHERE market_segment_id IS NULL AND lower(platform) = 'pc'"), {"pc": pc_id})
        elif table in legacy_pc_tables:
            # Every pre-Phase-2 manual verification/portfolio row belongs to the user's
            # validated FC26 PC execution account. Do not guess for future rows.
            bind.execute(sa.text(f"UPDATE {table} SET market_segment_id = :pc WHERE market_segment_id IS NULL"), {"pc": pc_id})

    # Knowledge-time defaults for legacy live rows. Backfilled data added later keeps its
    # actual insertion/import timestamp rather than pretending it was known earlier.
    if "inserted_at" in _columns("raw_ingests"):
        bind.execute(sa.text("UPDATE raw_ingests SET inserted_at = observed_at WHERE inserted_at IS NULL"))
    for table in ("reference_price_observations", "execution_observations"):
        if "inserted_at" in _columns(table):
            bind.execute(sa.text(f"UPDATE {table} SET inserted_at = observed_at WHERE inserted_at IS NULL"))

    # Replace the legacy account+card portfolio uniqueness with market-aware uniqueness.
    uniques = {u.get("name") for u in inspect(bind).get_unique_constraints("portfolio_positions")}
    if "uq_portfolio_account_card" in uniques:
        op.drop_constraint("uq_portfolio_account_card", "portfolio_positions", type_="unique")
    uniques = {u.get("name") for u in inspect(bind).get_unique_constraints("portfolio_positions")}
    if "uq_portfolio_account_card_segment" not in uniques:
        op.create_unique_constraint("uq_portfolio_account_card_segment", "portfolio_positions", ["account_id", "card_id", "market_segment_id"])

    for table, col in [
        ("reference_price_observations", "market_segment_id"), ("execution_observations", "market_segment_id"),
        ("opportunity_candidates", "market_segment_id"), ("portfolio_positions", "market_segment_id"),
        ("portfolio_transactions", "market_segment_id"), ("card_source_ids", "mapping_status"),
    ]:
        _index(f"ix_{table}_{col}", table, [col])

    for name in _NEW_TABLES[1:]:
        Base.metadata.tables[name].create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for name in reversed(_NEW_TABLES[1:]):
        Base.metadata.tables[name].drop(bind=bind, checkfirst=True)
    # Destructive column rollback is intentionally conservative; Phase 2 history should not be silently discarded.
    Base.metadata.tables["market_segments"].drop(bind=bind, checkfirst=True)
