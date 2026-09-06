from __future__ import annotations

import ast
import re
from pathlib import Path
from types import SimpleNamespace

from fc27trader.db.alembic_bootstrap import ALEMBIC_VERSION_LENGTH, ensure_alembic_version_capacity

ROOT = Path(__file__).resolve().parents[1]


class FakePostgresConnection:
    dialect = SimpleNamespace(name="postgresql")

    def __init__(self):
        self.sql: list[str] = []

    def execute(self, statement):
        self.sql.append(str(statement))


def _revision(path: Path) -> tuple[str, str | None]:
    text = path.read_text(encoding="utf-8")
    revision = re.search(r'^revision\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE).group(1)
    down_match = re.search(r'^down_revision\s*=\s*(?:["\']([^"\']+)["\']|None)', text, re.MULTILINE)
    return revision, down_match.group(1) if down_match and down_match.group(1) else None


def test_alembic_bootstrap_supports_long_revision_ids_for_fresh_and_upgrade_paths():
    connection = FakePostgresConnection()
    ensure_alembic_version_capacity(connection)
    sql = "\n".join(connection.sql).upper()
    assert ALEMBIC_VERSION_LENGTH >= 255
    assert "CREATE TABLE IF NOT EXISTS ALEMBIC_VERSION" in sql
    assert "VARCHAR(255)" in sql
    assert "ALTER TABLE ALEMBIC_VERSION ALTER COLUMN VERSION_NUM TYPE VARCHAR(255)" in sql

    env = (ROOT / "migrations/env.py").read_text(encoding="utf-8")
    # The widening hook must execute before Alembic configures the migration context.
    assert env.index("ensure_alembic_version_capacity(connection)") < env.index("context.configure(connection=connection")


def test_migration_chain_covers_upgrades_from_0005_and_0006_and_longest_id_fits():
    versions = sorted((ROOT / "migrations/versions").glob("*.py"))
    pairs = dict(_revision(p) for p in versions)
    assert pairs["0006_portfolio_execution_semantics"] == "0005_strategy_intelligence"
    assert pairs["0007_fc26_real_market_phase1"] == "0006_portfolio_execution_semantics"
    assert max(map(len, pairs)) < ALEMBIC_VERSION_LENGTH

    # 0006 must be safe when 0001's current metadata already created the column on a fresh install.
    m6 = (ROOT / "migrations/versions/0006_portfolio_execution_semantics.py").read_text(encoding="utf-8")
    assert 'if "desired_listing_price" not in existing' in m6


def test_strategy_seed_uses_current_seed_function_only():
    path = ROOT / "scripts/seed_strategies.py"
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "seed_strategy_library" in imported
    assert "seed_strategy_library" in calls
    assert "seed_strategy_research" not in text


def test_release_zip_validator_guards_install_regressions(tmp_path):
    import importlib.util
    import zipfile

    module_path = ROOT / "scripts/validate_release_package.py"
    spec = importlib.util.spec_from_file_location("validate_release_package", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    out = tmp_path / "release.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        required = set(module.REQUIRED_FILES)
        required.update(str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / "migrations/versions").glob("*.py"))
        required = sorted(required)
        for rel in required:
            zf.write(ROOT / rel, f"fc27-top100-trading/{rel}")
    assert module.validate_zip(out) == []


def _load_migration(filename: str):
    import importlib.util
    path = ROOT / "migrations/versions" / filename
    spec = importlib.util.spec_from_file_location(filename.replace(".py", ""), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class _FakeInspector:
    def __init__(self, columns): self.columns = columns
    def get_columns(self, table): return [{"name": x} for x in self.columns.get(table, set())]


class _FakeBatch:
    def __init__(self, table, added): self.table=table; self.added=added
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def add_column(self, column): self.added.append((self.table, column.name))
    def drop_column(self, name): pass


class _FakeTable:
    def __init__(self, name, created): self.name=name; self.created=created
    def create(self, bind=None, checkfirst=False): self.created.append((self.name, checkfirst))
    def drop(self, bind=None, checkfirst=False): pass


def test_migration_functions_are_safe_for_fresh_install_and_0005_0006_upgrades(monkeypatch):
    m6 = _load_migration("0006_portfolio_execution_semantics.py")
    added = []
    monkeypatch.setattr(m6.op, "get_bind", lambda: object())
    monkeypatch.setattr(m6, "inspect", lambda bind: _FakeInspector({"portfolio_positions": set()}))
    monkeypatch.setattr(m6.op, "add_column", lambda table, col: added.append((table, col.name)))
    m6.upgrade()  # simulated 0005 -> 0006
    assert ("portfolio_positions", "desired_listing_price") in added

    added.clear()
    monkeypatch.setattr(m6, "inspect", lambda bind: _FakeInspector({"portfolio_positions": {"desired_listing_price"}}))
    m6.upgrade()  # fresh 0001 created current metadata; 0006 must be idempotent
    assert added == []

    m7 = _load_migration("0007_fc26_real_market_phase1.py")
    created, added7 = [], []
    fake_tables = {name: _FakeTable(name, created) for name in ["provider_entities", "provider_health"]}
    monkeypatch.setattr(m7, "Base", SimpleNamespace(metadata=SimpleNamespace(tables=fake_tables)))
    monkeypatch.setattr(m7.op, "get_bind", lambda: object())
    monkeypatch.setattr(m7.op, "batch_alter_table", lambda table: _FakeBatch(table, added7))
    monkeypatch.setattr(m7.op, "create_index", lambda *a, **k: None)

    # Simulated upgrade from 0006: old columns exist, Phase-1 columns do not.
    old_cols = {
        "cards": {"id", "name"},
        "card_source_ids": {"id", "external_id"},
        "reference_price_observations": {"id", "price"},
    }
    monkeypatch.setattr(m7, "inspect", lambda bind: _FakeInspector(old_cols))
    m7.upgrade()
    assert ("cards", "image_id") in added7
    assert ("cards", "image_url") in added7
    assert ("reference_price_observations", "observation_key") in added7
    assert sorted(x[0] for x in created) == ["provider_entities", "provider_health"]

    # Fresh install: 0001 creates current metadata, so 0007 must not add duplicate columns.
    added7.clear(); created.clear()
    current_cols = {
        "cards": {"id", "name", "image_id", "image_url"},
        "card_source_ids": {"id", "external_id", "mapping_method", "mapping_confidence"},
        "reference_price_observations": {"id", "price", "provider_role", "evidence_class", "observation_key"},
    }
    monkeypatch.setattr(m7, "inspect", lambda bind: _FakeInspector(current_cols))
    m7.upgrade()
    assert added7 == []
    assert sorted(x[0] for x in created) == ["provider_entities", "provider_health"]

class _Phase2Bind:
    def __init__(self): self.sql=[]
    def execute(self, statement, params=None): self.sql.append((str(statement), params)); return SimpleNamespace()

class _Phase2Inspector:
    def get_unique_constraints(self, table): return []
    def get_indexes(self, table): return []
    def get_columns(self, table): return []


def test_phase2_0008_upgrade_is_safe_from_phase1_and_current_fresh_schema(monkeypatch):
    m8=_load_migration("0008_fc26_multisource_multimarket.py")
    bind=_Phase2Bind(); created=[]; added=[]
    # Avoid exercising database-specific seed SELECTs in this structural upgrade simulation.
    monkeypatch.setattr(m8,"_seed_segments",lambda:{(26,"PC"):"pc-id"})
    monkeypatch.setattr(m8.op,"get_bind",lambda:bind)
    monkeypatch.setattr(m8,"inspect",lambda b:_Phase2Inspector())
    monkeypatch.setattr(m8.op,"batch_alter_table",lambda table:_FakeBatch(table,added))
    monkeypatch.setattr(m8.op,"create_unique_constraint",lambda *a,**k:None)
    monkeypatch.setattr(m8.op,"drop_constraint",lambda *a,**k:None)
    monkeypatch.setattr(m8,"_index",lambda *a,**k:None)
    tables={name:_FakeTable(name,created) for name in m8._NEW_TABLES}
    monkeypatch.setattr(m8,"Base",SimpleNamespace(metadata=SimpleNamespace(tables=tables)))
    # Phase-1 shape: none of the Phase-2 columns exist.
    phase1_cols={
        "raw_ingests":{"id","observed_at"},"card_source_ids":{"id"},"provider_health":{"id"},
        "reference_price_observations":{"id","platform","observed_at"},"execution_observations":{"id","platform","observed_at"},
        "opportunity_candidates":{"id","platform"},"manual_verification_requests":{"id"},"manual_verification_responses":{"id"},
        "trading_accounts":{"id"},"portfolio_positions":{"id"},"portfolio_transactions":{"id"},
    }
    monkeypatch.setattr(m8,"_columns",lambda table:set(phase1_cols.get(table,set())))
    m8.upgrade()
    assert ("reference_price_observations","market_segment_id") in added
    assert ("execution_observations","market_segment_id") in added
    assert ("portfolio_positions","market_segment_id") in added
    assert {x[0] for x in created}==set(m8._NEW_TABLES)

    # Fresh/current schema path: all Phase-2 columns already exist; no duplicate adds.
    added.clear(); created.clear()
    phase2_cols={
        "raw_ingests":{"id","observed_at","schema_version","inserted_at"},
        "card_source_ids":{"id","mapping_status"},
        "provider_health":{"id","status","access_type","enabled","supported_segments_json","retry_after_seconds","items_seen","items_ingested","duplicates_skipped","quarantined_observations","parsing_failures","normalization_failures","identity_failures","last_poll_duration_ms","gap_status","platform_certainty"},
        "reference_price_observations":{"id","platform","observed_at","market_segment_id","inserted_at","quality_status","state_completeness","is_backfill"},
        "execution_observations":{"id","platform","observed_at","market_segment_id","inserted_at","quality_status"},
        "opportunity_candidates":{"id","platform","market_segment_id","actionable","signal_scope"},
        "manual_verification_requests":{"id","market_segment_id"},"manual_verification_responses":{"id","market_segment_id"},
        "trading_accounts":{"id","game_year"},"portfolio_positions":{"id","market_segment_id"},"portfolio_transactions":{"id","market_segment_id"},
    }
    monkeypatch.setattr(m8,"_columns",lambda table:set(phase2_cols.get(table,set())))
    m8.upgrade()
    assert added==[]
    assert {x[0] for x in created}==set(m8._NEW_TABLES)
