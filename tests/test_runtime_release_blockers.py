from __future__ import annotations

import json
import sys
import types
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from types import SimpleNamespace

import pytest

from fc27trader.collectors.base import RawObservation
from fc27trader.db.json_safe import to_json_safe
from fc27trader.db.models import ProviderHealth
from fc27trader.services.provider_health import record_provider_success


class SampleEnum(Enum):
    OK = "ok"


class JsonCheckingHealthSession:
    def __init__(self, row):
        self.row = row

    def scalar(self, statement):
        return self.row

    def add(self, row):
        self.row = row

    def flush(self):
        # Mirrors the runtime failure boundary: psycopg's JSON serializer must accept this.
        json.dumps(self.row.metadata_json)


def _health_row():
    return ProviderHealth(
        id=uuid.uuid4(), provider_key="futzip", provider_role="context", platform="unknown",
        requests_total=0, requests_failed=0, cards_covered=0,
        updated_at=datetime(2026, 9, 4, 15, 0, tzinfo=UTC), metadata_json={},
    )


def test_json_safe_recursively_normalizes_persistence_metadata():
    dt = datetime(2026, 9, 4, 15, 28, 58, 493114, tzinfo=UTC)
    value = {
        "at": dt,
        "day": date(2026, 9, 4),
        "decimal": Decimal("101000.50"),
        "enum": SampleEnum.OK,
        "nested": [{"provider_timestamp": dt}, (dt,)],
        "set": {"b", "a"},
    }
    safe = to_json_safe(value)
    assert safe["at"] == "2026-09-04T15:28:58.493114+00:00"
    assert safe["day"] == "2026-09-04"
    assert safe["decimal"] == "101000.50"
    assert safe["enum"] == "ok"
    assert safe["nested"][0]["provider_timestamp"] == safe["at"]
    assert safe["nested"][1] == [safe["at"]]
    assert safe["set"] == ["a", "b"]
    json.dumps(safe)


def test_record_provider_success_accepts_datetime_and_nested_datetime_metadata():
    session = JsonCheckingHealthSession(_health_row())
    newest = datetime(2026, 9, 4, 15, 28, 58, 493114, tzinfo=UTC)
    row = record_provider_success(
        session,
        provider_key="futzip",
        provider_role="context",
        platform="unknown",
        latency_ms=42.5,
        latest_provider_timestamp=newest,
        metadata={
            "newest_provider_timestamp": newest,
            "nested": {"oldest_provider_timestamp": newest.replace(minute=20)},
        },
    )
    assert row.metadata_json["newest_provider_timestamp"] == newest.isoformat()
    assert row.metadata_json["nested"]["oldest_provider_timestamp"].endswith("+00:00")
    json.dumps(row.metadata_json)


def test_real_futzip_success_stats_shape_is_json_safe():
    newest = datetime(2026, 9, 4, 15, 28, 58, 493114, tzinfo=UTC)
    stats = {
        "items_seen": 25,
        "items_parsed": 25,
        "items_ingested": 25,
        "duplicates": 0,
        "newest_provider_timestamp": newest,
        "oldest_provider_timestamp": newest.replace(minute=10),
        "gap_status": "UNKNOWN_COVERAGE",
        "nested": {"feed_window": [newest.replace(minute=10), newest]},
    }
    safe = to_json_safe(stats)
    assert safe["newest_provider_timestamp"] == newest.isoformat()
    assert safe["nested"]["feed_window"][1] == newest.isoformat()
    json.dumps(safe)


class FakeSession:
    def __init__(self):
        self.added = []
        self.commits = 0
        self.rollbacks = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def add(self, row):
        self.added.append(row)

    def flush(self):
        for row in self.added:
            metadata = getattr(row, "metadata_json", None)
            if metadata is not None:
                json.dumps(metadata)

    def scalar(self, statement):
        return None

    def commit(self):
        self.flush()
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


@pytest.mark.parametrize("feed_key", ["movers", "new", "sbc"])
def test_all_futzip_collector_success_paths_commit_json_safe_stats(monkeypatch, feed_key):
    # The slim release-test environment intentionally does not install Celery/structlog;
    # stub only their import surfaces so we can exercise the real task function body.
    if "structlog" not in sys.modules:
        logger = SimpleNamespace(info=lambda *a, **k: None, exception=lambda *a, **k: None)
        monkeypatch.setitem(sys.modules, "structlog", SimpleNamespace(get_logger=lambda: logger))
    if "celery" not in sys.modules:
        class DummyTask:
            def __init__(self, fn):
                self.run = fn
                self.__name__ = getattr(fn, "__name__", "task")
            def __call__(self, *args, **kwargs):
                return self.run(*args, **kwargs)
        class DummyConf:
            def update(self, **kwargs):
                return None
        class DummyCelery:
            def __init__(self, *args, **kwargs):
                self.conf = DummyConf()
            def task(self, *args, **kwargs):
                return lambda fn: DummyTask(fn)
            def autodiscover_tasks(self, *args, **kwargs):
                return None
        module = types.ModuleType("celery")
        module.Celery = DummyCelery
        monkeypatch.setitem(sys.modules, "celery", module)
    # Avoid creating a real PostgreSQL engine in the slim test environment.
    db_session_module = types.ModuleType("fc27trader.db.session")
    db_session_module.SessionLocal = lambda: None
    monkeypatch.setitem(sys.modules, "fc27trader.db.session", db_session_module)
    # Force a clean import so the monkeypatched dependency surfaces are used.
    sys.modules.pop("fc27trader.scheduler.tasks", None)
    sys.modules.pop("fc27trader.scheduler.celery_app", None)
    from fc27trader.scheduler import tasks

    session = FakeSession()
    observed = datetime(2026, 9, 4, 15, 35, tzinfo=UTC)
    obs = RawObservation(
        source_key="futzip", source_kind=f"futzip_{feed_key}_rss",
        url=f"https://futzip.com/feed/{feed_key}.xml", observed_at=observed,
        body=b"<rss/>", status_code=200, content_type="application/rss+xml",
        metadata={"feed_key": feed_key},
    )

    class Collector:
        def __init__(self, *args, **kwargs):
            pass

        def collect_feed(self, key, conditional):
            assert key == feed_key
            return [obs]

    stats = {
        "items_seen": 1,
        "items_parsed": 1,
        "items_ingested": 1,
        "duplicates": 0,
        "parse_failures": 0,
        "quarantined": 0,
        "unique_provider_card_ids": 1,
        "newest_provider_timestamp": observed,
        "oldest_provider_timestamp": observed,
        "market_context_only": 1 if feed_key == "movers" else 0,
        "pc_references_created": 0,
        "console_references_created": 0,
        "switch_references_created": 0,
        "gap_status": "UNKNOWN_COVERAGE",
    }

    monkeypatch.setattr(tasks, "SessionLocal", lambda: session)
    monkeypatch.setattr(tasks, "FutzipCollector", Collector)
    monkeypatch.setattr(tasks.raw_store, "put", lambda observation: SimpleNamespace(storage_uri="raw://test", sha256="abc", byte_length=len(observation.body)))
    monkeypatch.setattr(tasks, "record_raw_ingest", lambda *a, **k: SimpleNamespace(id=uuid.uuid4()))
    monkeypatch.setattr(tasks, "ingest_futzip_feed", lambda *a, **k: dict(stats))
    monkeypatch.setattr(tasks, "record_provider_success", lambda *a, **k: None)
    monkeypatch.setattr(tasks, "mark_futzip_failure", lambda *a, **k: None)
    monkeypatch.setattr(tasks, "record_provider_failure", lambda *a, **k: None)

    result = tasks.collect_futzip_feed.run(feed_key)
    assert result["status"] == "success"
    assert result["items_ingested"] == 1
    assert session.commits == 1
    run = next(row for row in session.added if hasattr(row, "collector_key"))
    assert run.metadata_json["newest_provider_timestamp"] == observed.isoformat()
    json.dumps(run.metadata_json)


def test_futzip_repeated_poll_dedupe_contract_is_committed_not_overwritten():
    ingestion = Path("src/fc27trader/services/futzip_ingestion.py").read_text()
    task = Path("src/fc27trader/scheduler/tasks.py").read_text()
    assert "ProviderFeedEvent.provider_event_id == item.guid" in ingestion
    assert 'stats["duplicates"] += 1' in ingestion
    assert "session.commit()" in task
    assert "uq_provider_feed_event_identity" in Path("src/fc27trader/db/models.py").read_text()


def test_runtime_gate_fails_on_smoke_or_required_futzip_and_waits_for_readiness():
    script = Path("scripts/phase2_runtime_check.ps1").read_text()
    assert 'Wait-HttpReady "API" "http://localhost:8080/health"' in script
    assert 'Wait-HttpReady "Web" "http://localhost:3000"' in script
    assert 'Invoke-RequiredNative "Application smoke test"' in script
    assert '& $Command | Out-Host' in script  # required gate returns only the boolean, not native stdout
    for feed in ("futzip-movers", "futzip-new", "futzip-sbc"):
        assert feed in script
    assert 'Invoke-RequiredNative "Required FUTZIP collection: $feed"' in script
    assert 'if ($script:Failures.Count -gt 0)' in script
    assert 'exit 1' in script
    assert 'Phase 2 runtime validation PASSED' in script
    assert 'Phase 2 runtime check complete' not in script


def test_runtime_gate_clean_install_and_upgrade_env_behavior_are_explicit():
    script = Path("scripts/phase2_runtime_check.ps1").read_text()
    assert 'ValidateSet("Auto", "CleanInstall", "Upgrade")' in script
    assert 'CLEAN INSTALL: creating a blank .env' in script
    assert 'UPGRADE mode: .env is missing' in script
    assert 'Preserve/copy the previous release\'s .env' in script
    assert 'will not search for, copy, or print secrets' in script
    assert 'Copy-Item .env.example .env' in script


def test_upgrade_documentation_requires_intentional_env_preservation():
    text = Path("docs/VACATION_PC_SETUP_2026-09-04.md").read_text()
    assert "UPGRADE" in text.upper()
    assert "previous" in text.lower() and ".env" in text
    assert "phase2_runtime_check.ps1" in text
