from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from sqlalchemy import JSON, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from fc27trader.collectors.base import RawObservation
from fc27trader.domain.enums import MarketSegmentKey
from fc27trader.services import parse_futbin_ingestion as ingestion


LIVE_BAD_POSITION = "CAMCDM, RM, CM, 1"


def _obs(players: list[dict], page: int = 1) -> RawObservation:
    return RawObservation(
        source_key="parse_futbin",
        source_kind="parse_futbin_get_players",
        url=f"https://example.test/get_players?page={page}",
        observed_at=datetime(2026, 9, 4, 18, 0, tzinfo=UTC),
        body=json.dumps({"data": {"page": page, "total": len(players), "players": players}}).encode(),
        content_type="application/json",
    )


def test_live_composite_position_is_not_primary_and_raw_is_preserved():
    primary, alt, metadata = ingestion._parse_position_metadata({"position": LIVE_BAD_POSITION})
    assert primary is None
    assert alt == ["RM", "CM"]
    assert metadata["parse_position_raw"] == LIVE_BAD_POSITION
    assert metadata["parse_positions_normalized"] == ["RM", "CM"]
    assert metadata["parse_position_valid_single"] is False
    # Parse's documented role decoration remains safe for a genuine single position.
    assert ingestion._normalize_single_position("ST++") == "ST"


def test_bad_position_metadata_does_not_drop_card_or_drive_identity(monkeypatch):
    captured = {}
    fake_card = SimpleNamespace(id=uuid.uuid4(), attributes_json={})
    fake_mapping = SimpleNamespace(mapping_status=None, mapping_method=None, mapping_confidence=None)
    fake_source = SimpleNamespace(
        id=uuid.uuid4(), name="parse", source_class="x", automation_policy="x",
        training_policy="x", enabled=True, metadata_json={}
    )

    class FakeSession:
        def scalar(self, *args, **kwargs):
            return fake_mapping

    monkeypatch.setattr(ingestion, "_canonical_card_for_futbin_id", lambda *a, **k: None)
    monkeypatch.setattr(ingestion, "get_or_create_source", lambda *a, **k: fake_source)

    def fake_upsert(session, **kwargs):
        captured.update(kwargs)
        fake_card.attributes_json = kwargs["attributes"]
        return fake_card

    monkeypatch.setattr(ingestion, "upsert_external_card", fake_upsert)

    player = {
        "id": "998877",
        "name": "Position Glitch Player",
        "rating": "91",
        "position": LIVE_BAD_POSITION,
        "version": "Special",
        "club": "Club",
        "league": "League",
        "nation": "Nation",
    }
    card, status = ingestion._upsert_parse_card(FakeSession(), player, observed_at=datetime.now(UTC))

    assert card is fake_card
    assert captured["external_id"] == "998877"
    assert captured["name"] == "Position Glitch Player"
    assert captured["primary_position"] is None
    assert captured["alt_positions"] == ["RM", "CM"]
    assert captured["attributes"]["parse_position_raw"] == LIVE_BAD_POSITION
    # Position is metadata only; the stable provider ID/player/card still survives.
    assert status == "HIGH_CONFIDENCE"


def test_catalogue_savepoint_isolates_bad_item_and_next_page_commits(monkeypatch):
    class MiniBase(DeclarativeBase):
        pass

    class MiniRow(MiniBase):
        __tablename__ = "mini_rows"
        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        provider_id: Mapped[str] = mapped_column(String(64), unique=True)

    class MiniIncident(MiniBase):
        __tablename__ = "mini_incidents"
        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        detected_at: Mapped[datetime]
        source_id: Mapped[str | None] = mapped_column(String(64))
        severity: Mapped[str] = mapped_column(String(16))
        incident_type: Mapped[str] = mapped_column(String(64))
        description: Mapped[str] = mapped_column(String(255))
        metadata_json: Mapped[dict] = mapped_column(JSON)

    engine = create_engine("sqlite+pysqlite:///:memory:")
    MiniBase.metadata.create_all(engine)

    source = SimpleNamespace(id="source-1")
    monkeypatch.setattr(ingestion, "DataQualityIncident", MiniIncident)
    monkeypatch.setattr(ingestion, "get_or_create_source", lambda *a, **k: source)

    def fake_upsert(session: Session, player: dict, **kwargs):
        provider_id = str(player["id"])
        # Simulate a genuine database flush failure for one provider item.
        row = MiniRow(provider_id="already-there" if provider_id == "bad" else provider_id)
        session.add(row)
        session.flush()
        return SimpleNamespace(id=uuid.uuid4()), "HIGH_CONFIDENCE"

    seen_segments: list[str] = []

    def fake_insert_price(session: Session, *, segment_key: str, **kwargs):
        seen_segments.append(segment_key)
        return SimpleNamespace(quality_status="VALID")

    monkeypatch.setattr(ingestion, "_upsert_parse_card", fake_upsert)
    monkeypatch.setattr(ingestion, "_insert_price", fake_insert_price)

    page1 = [
        {"id": "good-1", "name": "Good One", "position": "ST++", "price_pc": "10K", "price_ps": "9K"},
        {"id": "bad", "name": "Bad DB Item", "position": LIVE_BAD_POSITION, "price_pc": "20K", "price_ps": "19K"},
        {"id": "good-2", "name": "Good Two", "position": "CM", "price_pc": "30K", "price_ps": "29K"},
    ]
    page2 = [
        {"id": "good-3", "name": "Good Three", "position": "RW+", "price_pc": "40K", "price_ps": "39K"},
    ]

    with Session(engine) as session:
        session.add(MiniRow(provider_id="already-there"))
        session.commit()

        r1 = ingestion.ingest_parse_futbin_catalogue_page(session, _obs(page1, 1), raw_ingest_id=uuid.uuid4())
        # The same SQLAlchemy session remains usable after the failed nested flush.
        assert session.scalar(select(MiniRow).where(MiniRow.provider_id == "good-2")) is not None
        r2 = ingestion.ingest_parse_futbin_catalogue_page(session, _obs(page2, 2), raw_ingest_id=uuid.uuid4())
        session.commit()

        provider_ids = set(session.scalars(select(MiniRow.provider_id)))
        incidents = list(session.scalars(select(MiniIncident)))

    assert r1["cards_written"] == 2
    assert r1["malformed"] == 1
    assert r2["cards_written"] == 1
    assert {"good-1", "good-2", "good-3"}.issubset(provider_ids)
    assert len(incidents) == 1 and incidents[0].metadata_json["provider_external_id"] == "bad"
    # Every successful card emits independent PC + PlayStation reference semantics.
    assert seen_segments.count(MarketSegmentKey.PC.value) == 3
    assert seen_segments.count(MarketSegmentKey.PLAYSTATION.value) == 3


def test_card_identity_source_no_longer_uses_position_as_match_clause():
    text = open("src/fc27trader/services/card_identity.py", encoding="utf-8").read()
    assert "Card.primary_position == primary_position" not in text
