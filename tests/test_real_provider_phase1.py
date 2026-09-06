from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
import uuid

import orjson
import pytest

from fc27trader.collectors.base import RawObservation
from fc27trader.db.models import Card, ExecutionObservation, ProviderHealth, Source
from fc27trader.db.repositories import reference_observation_key
from fc27trader.ingestion.normalizer import normalize_futdb_players, normalize_futdb_price, normalize_thecoinprinter
from fc27trader.services.app_queries import _portfolio_executable_mark
from fc27trader.services.card_identity import resolve_card_for_provider
from fc27trader.services.provider_health import record_provider_failure, record_provider_success


def obs(source: str, kind: str, payload: dict, at: datetime) -> RawObservation:
    return RawObservation(
        source_key=source, source_kind=kind, url="https://example.invalid", observed_at=at,
        body=orjson.dumps(payload), status_code=200, content_type="application/json",
    )


def test_futdb_universe_and_pc_reference_normalization_preserves_identity_and_metadata():
    at = datetime(2026, 9, 4, 14, 0, tzinfo=UTC)
    payload = {
        "items": [{
            "id": 123, "resourceId": 700123, "resourceBaseId": 12345,
            "futBinId": 9001, "futWizId": 8001,
            "name": "Example Player", "commonName": "Example",
            "rating": 88, "position": "CM", "positionAlternatives": ["CAM", "CDM"],
            "league": 13, "club": 10, "nation": 14, "rarity": 5,
            "playStyles": ["Incisive Pass"], "playStylesPlus": ["Tiki Taka+"],
            "pace": 80, "shooting": 82, "passing": 90, "dribbling": 87,
            "defending": 75, "physicality": 78,
        }],
        "pagination": {"page": 1, "pageCount": 1},
    }
    cards, pagination = normalize_futdb_players(
        obs("futdb", "futdb_players", payload, at),
        entity_names={"league": {"13": "Premier League"}, "club": {"10": "Example FC"}, "nation": {"14": "Croatia"}, "rarity": {"5": "Rare Gold"}},
    )
    card = cards[0]
    assert pagination["pageCount"] == 1
    assert card.external_id == "123"
    assert card.ea_resource_id == 700123
    assert card.alt_positions == ["CAM", "CDM"]
    assert card.league == "Premier League"
    assert card.playstyles == ["Incisive Pass"]
    assert card.playstyles_plus == ["Tiki Taka+"]
    assert card.cross_provider_ids == {"futbin": "9001", "futwiz": "8001"}

    price = normalize_futdb_price(obs("futdb", "futdb_player_price", {
        "pc": {"price": 101000, "priceUpdate": "2026-09-04T13:54:00+00:00"}
    }, at), player_id=123)
    assert price is not None
    assert price.platform.value == "pc"
    assert price.lowest_bin == 101000
    assert price.source_updated_at is not None


def test_thecoinprinter_normalizes_pc_price_as_provider_snapshot_not_execution():
    at = datetime(2026, 9, 4, 14, 0, tzinfo=UTC)
    cards, snapshots = normalize_thecoinprinter(obs("thecoinprinter", "player_search", {
        "data": [{
            "id": "tcp-1", "name": "TCP Player", "rating": 87, "year": 26,
            "position": "ST", "alt_positions": ["CF"], "league": "LaLiga", "team": "Club",
            "nationality": "Spain", "group_type": "Gold Rare", "pc_price": 99000,
            "updated_at": "2026-09-04T13:58:30+00:00", "image": "https://img.invalid/1.png",
        }], "pagination": {"page": 1}
    }, at))
    assert cards[0].game_year == 26
    assert snapshots[0].platform.value == "pc"
    assert snapshots[0].lowest_bin == 99000
    # The normalizer produces provider data; only provider_ingestion is allowed to persist it,
    # and that service writes ReferencePriceObservation rather than ExecutionObservation.
    import inspect
    from fc27trader.services import provider_ingestion
    source = inspect.getsource(provider_ingestion.ingest_thecoinprinter_page)
    assert "insert_reference_price_observation" in source
    assert "insert_execution_observation" not in source


def test_reference_observation_dedupes_exact_reprocessing_but_appends_later_poll():
    card_id, source_id = uuid.uuid4(), uuid.uuid4()
    observed = datetime(2026, 9, 4, 14, 0, tzinfo=UTC)
    provider_ts = observed - timedelta(minutes=6)
    base = dict(card_id=card_id, source_id=source_id, provider_timestamp=provider_ts, price=101000, price_kind="provider_pc_reference")
    first = reference_observation_key(observed_at=observed, **base)
    replay = reference_observation_key(observed_at=observed, **base)
    later = reference_observation_key(observed_at=observed + timedelta(minutes=30), **base)
    assert first == replay
    assert later != first


class IdentitySession:
    def __init__(self, card):
        self.card = card
        self.calls = 0

    def scalar(self, statement):
        self.calls += 1
        if self.calls == 1:  # no source-specific mapping yet
            return None
        if self.calls == 2:  # canonical EA resource match
            return self.card
        raise AssertionError("unexpected scalar call")

    def get(self, model, key):
        return self.card


def test_card_identity_maps_second_provider_by_ea_resource_id():
    now = datetime(2026, 9, 4, 14, 0, tzinfo=UTC)
    card = Card(id=uuid.uuid4(), game_year=26, ea_resource_id=700123, name="Example", rating=88,
                attributes_json={}, playstyles_json={}, roles_json={}, created_at=now, updated_at=now)
    source = Source(id=uuid.uuid4(), key="provider2", name="Provider 2", source_class="api", automation_policy="allowed", training_policy="allowed", enabled=True, metadata_json={})
    resolved, method, confidence = resolve_card_for_provider(
        IdentitySession(card), source=source, external_id="other-55", game_year=26,
        ea_resource_id=700123, name="Different display name", rating=88,
        primary_position="CM", league=None, club=None, nation=None,
    )
    assert resolved is card
    assert method == "ea_resource_id"
    assert confidence == 1.0


class HealthSession:
    def __init__(self, row):
        self.row = row
    def scalar(self, statement):
        return self.row
    def add(self, row):
        self.row = row
    def flush(self):
        pass


def _health_row():
    return ProviderHealth(
        id=uuid.uuid4(), provider_key="futdb", provider_role="reference", platform="pc",
        requests_total=0, requests_failed=0, cards_covered=0,
        updated_at=datetime(2026, 9, 4, 14, 0, tzinfo=UTC), metadata_json={},
    )


def test_provider_failure_and_recovery_health_accounting():
    session = HealthSession(_health_row())
    failed = record_provider_failure(session, provider_key="futdb", provider_role="reference", error="HTTP 503", latency_ms=900)
    assert failed.requests_total == 1
    assert failed.requests_failed == 1
    assert float(failed.error_rate) == 1.0
    assert "503" in failed.last_error

    recovered = record_provider_success(
        session, provider_key="futdb", provider_role="reference", latency_ms=120,
        cards_covered=25, latest_provider_timestamp=datetime.now(UTC) - timedelta(minutes=35),
        rate_limit_remaining=19900,
    )
    assert recovered.requests_total == 2
    assert recovered.requests_failed == 1
    assert float(recovered.error_rate) == 0.5
    assert recovered.cards_covered == 25
    assert recovered.rate_limit_remaining == 19900
    assert recovered.latest_observation_age_seconds > 0


def test_portfolio_mark_never_falls_back_to_reference_price():
    assert _portfolio_executable_mark(None) is None
    ex = SimpleNamespace(lowest_bin=95500)
    assert _portfolio_executable_mark(ex) == 95500
    reference_only = SimpleNamespace(price=101000)
    with pytest.raises(AttributeError):
        _portfolio_executable_mark(reference_only)


def test_tcp_ingestion_persists_reference_rows_only(monkeypatch):
    from fc27trader.services import provider_ingestion
    at = datetime(2026, 9, 4, 14, 0, tzinfo=UTC)
    raw = obs("thecoinprinter", "player_search", {
        "data": [{
            "id": "tcp-2", "name": "Ingested Player", "rating": 86, "year": 26,
            "position": "RW", "alt_positions": [], "league": "Bundesliga", "team": "Club",
            "nationality": "Germany", "group_type": "Gold Rare", "pc_price": 45000,
            "updated_at": "2026-09-04T13:57:00+00:00",
        }], "pagination": {"total": 1}
    }, at)
    now = at
    card = Card(id=uuid.uuid4(), game_year=26, name="Ingested Player", rating=86,
                attributes_json={}, playstyles_json={}, roles_json={}, created_at=now, updated_at=now)
    inserted = []
    monkeypatch.setattr(provider_ingestion, "upsert_external_card", lambda *a, **k: card)
    monkeypatch.setattr(provider_ingestion, "immutable_market_context", lambda *a, **k: {"captured_at": at.isoformat()})
    monkeypatch.setattr(provider_ingestion, "insert_reference_price_observation", lambda *a, **k: inserted.append(k) or SimpleNamespace(provider_timestamp=None))

    result = provider_ingestion.ingest_thecoinprinter_page(SimpleNamespace(), raw, raw_ingest_id=uuid.uuid4())
    assert result["prices_written"] == 1
    assert inserted[0]["provider_role"] == "reference"
    assert inserted[0]["evidence_class"] == "measured_provider"
    assert inserted[0]["price"] == 45000
    assert inserted[0]["metadata"]["executable"] is False


def test_futdb_price_ingestion_persists_reference_not_execution(monkeypatch):
    from fc27trader.services import provider_ingestion
    at = datetime(2026, 9, 4, 14, 0, tzinfo=UTC)
    raw = obs("futdb", "player_price", {"pc": {"price": 73000, "priceUpdate": "2026-09-04T13:30:00+00:00"}}, at)
    source = Source(id=uuid.uuid4(), key="futdb", name="FUT-DB", source_class="api", automation_policy="allowed", training_policy="allowed", enabled=True, metadata_json={})
    card = Card(id=uuid.uuid4(), game_year=26, name="FUTDB Card", rating=87,
                attributes_json={}, playstyles_json={}, roles_json={}, created_at=at, updated_at=at)
    mapping = SimpleNamespace(card_id=card.id)

    class Session:
        def scalar(self, statement): return mapping
        def get(self, model, key): return card

    inserted = []
    monkeypatch.setattr(provider_ingestion, "get_or_create_source", lambda *a, **k: source)
    monkeypatch.setattr(provider_ingestion, "immutable_market_context", lambda *a, **k: {})
    monkeypatch.setattr(provider_ingestion, "insert_reference_price_observation", lambda *a, **k: inserted.append(k) or SimpleNamespace(provider_timestamp=None))
    provider_ingestion.ingest_futdb_price(Session(), raw, player_id=123, raw_ingest_id=uuid.uuid4())
    assert inserted[0]["price"] == 73000
    assert inserted[0]["provider_role"] == "reference"
    assert inserted[0]["metadata"]["executable"] is False
