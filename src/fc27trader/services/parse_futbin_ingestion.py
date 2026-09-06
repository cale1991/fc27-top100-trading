from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.collectors.base import RawObservation
from fc27trader.collectors.parse_futbin import parse_parse_payload
from fc27trader.db.models import Card, CardSourceId, DataQualityIncident, ReferencePriceObservation, Source
from fc27trader.db.repositories import get_or_create_source, insert_reference_price_observation, upsert_external_card
from fc27trader.domain.enums import DataQualityStatus, IdentityStatus, MarketSegmentKey
from fc27trader.services.card_identity import ensure_source_mapping
from fc27trader.services.market_context import immutable_market_context
from fc27trader.services.market_segments import get_market_segment

_PRICE_RE = re.compile(r"^\s*([+-]?\d+(?:[.,]\d+)?)\s*([KMB])?\s*$", re.I)

_VALID_FUT_POSITIONS = frozenset({
    "GK", "RB", "RWB", "CB", "LB", "LWB",
    "CDM", "CM", "CAM", "RM", "RW", "LM", "LW", "CF", "ST",
})
_POSITION_SPLIT_RE = re.compile(r"[,;/|]+")


def _normalize_single_position(value: Any) -> str | None:
    """Return one trustworthy FUT position or None.

    Parse documents ``position`` as a single string and commonly decorates it with
    role markers such as ``ST++``. Provider/parser glitches have also produced
    composite values. Composite/ambiguous strings are never truncated or guessed.
    """
    if value is None:
        return None
    text = str(value).strip().upper()
    if not text:
        return None
    # Parse examples use +/++ as role decorations; stripping only trailing pluses
    # preserves the actual single position without interpreting composite strings.
    text = re.sub(r"\++$", "", text).strip()
    return text if text in _VALID_FUT_POSITIONS else None


def _parse_position_metadata(player: dict[str, Any]) -> tuple[str | None, list[str], dict[str, Any]]:
    """Normalize optional position metadata without making identity position-driven."""
    explicit_primary_raw = player.get("primary_position")
    provider_position_raw = player.get("position")

    primary = _normalize_single_position(explicit_primary_raw)
    primary_source = "primary_position" if primary else None
    if primary is None:
        primary = _normalize_single_position(provider_position_raw)
        if primary:
            primary_source = "position"

    candidates: list[Any] = []
    for key in ("positions", "alternate_positions", "alt_positions"):
        value = player.get(key)
        if isinstance(value, (list, tuple, set)):
            candidates.extend(value)
        elif value not in (None, ""):
            candidates.extend(_POSITION_SPLIT_RE.split(str(value)))

    # Preserve useful exact tokens from a composite provider ``position`` value, but
    # never infer a primary from it. E.g. CAMCDM is ambiguous and ignored; RM/CM are
    # retained as optional metadata.
    if provider_position_raw not in (None, "") and _normalize_single_position(provider_position_raw) is None:
        candidates.extend(_POSITION_SPLIT_RE.split(str(provider_position_raw)))

    alt_positions: list[str] = []
    for candidate in candidates:
        normalized = _normalize_single_position(candidate)
        if normalized and normalized != primary and normalized not in alt_positions:
            alt_positions.append(normalized)

    metadata = {
        "parse_position_raw": provider_position_raw,
        "parse_primary_position_raw": explicit_primary_raw,
        "parse_primary_position_source": primary_source,
        "parse_positions_normalized": ([primary] if primary else []) + alt_positions,
        "parse_position_valid_single": primary is not None,
    }
    return primary, alt_positions, metadata


def parse_coin_price(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().replace(" ", "")
    if not text or text in {"—", "-", "N/A", "n/a", "null", "None"}:
        return None
    match = _PRICE_RE.match(text.replace(",", ".") if text.count(",") == 1 and "." not in text and len(text.split(",")[-1]) <= 2 else text.replace(",", ""))
    if not match:
        return None
    number = float(match.group(1).replace(",", "."))
    suffix = (match.group(2) or "").upper()
    multiplier = {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[suffix]
    return int(round(number * multiplier))


def _body_data(obs: RawObservation) -> dict[str, Any]:
    payload = parse_parse_payload(obs.body)
    data = payload.get("data", payload)
    return data if isinstance(data, dict) else {}


def _players(obs: RawObservation) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    data = _body_data(obs)
    players = data.get("players") or data.get("items") or []
    if not isinstance(players, list):
        players = []
    return [x for x in players if isinstance(x, dict)], data


def _quality_for_price(session: Session, *, card_id, source_id, market_segment_id, price: int, observed_at: datetime) -> str:
    if price <= 0:
        return DataQualityStatus.QUARANTINED.value
    previous = session.scalar(
        select(ReferencePriceObservation)
        .where(
            ReferencePriceObservation.card_id == card_id,
            ReferencePriceObservation.source_id == source_id,
            ReferencePriceObservation.market_segment_id == market_segment_id,
            ReferencePriceObservation.quality_status == DataQualityStatus.VALID.value,
        )
        .order_by(ReferencePriceObservation.observed_at.desc())
        .limit(1)
    )
    if previous and previous.price > 0:
        ratio = max(price, previous.price) / min(price, previous.price)
        if ratio >= 100:
            return DataQualityStatus.QUARANTINED.value
        if ratio >= 10:
            return DataQualityStatus.SUSPECT.value
    return DataQualityStatus.VALID.value


def _canonical_card_for_futbin_id(session: Session, external_id: str) -> Card | None:
    futbin = session.scalar(select(Source).where(Source.key == "futbin"))
    if futbin is None:
        return None
    mapping = session.scalar(select(CardSourceId).where(CardSourceId.source_id == futbin.id, CardSourceId.external_id == external_id))
    return session.get(Card, mapping.card_id) if mapping else None


def _upsert_parse_card(session: Session, player: dict[str, Any], *, observed_at: datetime) -> tuple[Card | None, str]:
    external_id = player.get("id")
    if external_id is None:
        return None, IdentityStatus.UNRESOLVED.value
    external_id = str(external_id)
    existing_canonical = _canonical_card_for_futbin_id(session, external_id)
    source = get_or_create_source(session, "parse_futbin")
    source.name = "Parse.bot FUTBIN wrapper"
    source.source_class = "commercial_structured_api"
    source.automation_policy = "optional_authenticated_api"
    source.training_policy = "reference_with_provenance"
    source.enabled = True
    source.metadata_json = {
        **(source.metadata_json or {}),
        "upstream": "futbin",
        "official_futbin_api": False,
        "reference_only": True,
    }
    if existing_canonical is not None:
        mapping = session.scalar(select(CardSourceId).where(CardSourceId.source_id == source.id, CardSourceId.external_id == external_id))
        if mapping is None:
            ensure_source_mapping(
                session, card=existing_canonical, source=source, external_id=external_id,
                source_url=player.get("url"), mapping_method="shared_futbin_id", mapping_confidence=1.0,
            )
            mapping = session.scalar(select(CardSourceId).where(CardSourceId.source_id == source.id, CardSourceId.external_id == external_id))
        if mapping:
            mapping.mapping_status = IdentityStatus.CONFIRMED.value
        return existing_canonical, IdentityStatus.CONFIRMED.value

    name = (player.get("name") or player.get("full_name") or "").strip()
    if not name:
        return None, IdentityStatus.UNRESOLVED.value
    stats = player.get("stats") if isinstance(player.get("stats"), dict) else {}
    primary_position, alt_positions, position_metadata = _parse_position_metadata(player)
    card = upsert_external_card(
        session,
        source_key="parse_futbin",
        external_id=external_id,
        game_year=26,
        name=name,
        rating=int(player["rating"]) if str(player.get("rating") or "").isdigit() else None,
        primary_position=primary_position,
        alt_positions=alt_positions,
        league=player.get("league"), club=player.get("club"), nation=player.get("nation"),
        rarity=player.get("version"), attributes={
            **stats,
            "skill_moves": player.get("skill_moves"),
            "weak_foot": player.get("weak_foot"),
            **position_metadata,
        },
        image_id=external_id, image_url=player.get("image_large") or player.get("image"), source_url=player.get("url"),
    )
    mapping = session.scalar(select(CardSourceId).where(CardSourceId.source_id == source.id, CardSourceId.external_id == external_id))
    if mapping:
        mapping.mapping_status = IdentityStatus.HIGH_CONFIDENCE.value
        mapping.mapping_method = "stable_parse_futbin_id"
        mapping.mapping_confidence = Decimal("0.95")
    return card, IdentityStatus.HIGH_CONFIDENCE.value


def _insert_price(session: Session, *, card: Card, source: Source, raw_ingest_id, observed_at: datetime, field: str, value: Any, segment_key: str, platform: str, external_id: str):
    price = parse_coin_price(value)
    if price is None:
        return None
    segment = get_market_segment(session, game_year=26, segment_key=segment_key)
    quality = _quality_for_price(session, card_id=card.id, source_id=source.id, market_segment_id=segment.id, price=price, observed_at=observed_at)
    return insert_reference_price_observation(
        session,
        card=card,
        source_key="parse_futbin",
        observed_at=observed_at,
        provider_timestamp=None,
        price=price,
        raw_ingest_id=raw_ingest_id,
        price_kind=f"parse_futbin_{field}",
        provider_role="reference",
        evidence_class="measured_provider",
        uncertainty_pct=0.12 if quality == DataQualityStatus.VALID.value else 0.5,
        confidence=0.55 if quality == DataQualityStatus.VALID.value else 0.1,
        metadata={
            "observation_kind": "reference_price", "executable": False,
            "provider": "parse_futbin", "upstream": "futbin", "provider_external_id": external_id,
            "field": field, "provider_timestamp_available": False,
            "market_context": immutable_market_context(session, card_id=card.id, observed_at=observed_at),
        },
        platform=platform,
        market_segment_id=segment.id,
        quality_status=quality,
        state_completeness="directly_observed",
    )


def ingest_parse_futbin_catalogue_page(session: Session, obs: RawObservation, *, raw_ingest_id=None) -> dict[str, Any]:
    players, data = _players(obs)
    source = get_or_create_source(session, "parse_futbin")
    seen = len(players); cards_written = 0; pc_written = 0; ps_written = 0; malformed = 0; quarantined = 0
    identities = []
    for player in players:
        external_id = str(player.get("id")) if player.get("id") is not None else None
        try:
            # One provider row must never poison the page/run. Any flush failure is
            # contained by a SAVEPOINT; the outer transaction remains usable.
            with session.begin_nested():
                card, status = _upsert_parse_card(session, player, observed_at=obs.observed_at)
                if card is None:
                    raise ValueError("unresolved Parse/FUTBIN player identity")
                pc = _insert_price(session, card=card, source=source, raw_ingest_id=raw_ingest_id, observed_at=obs.observed_at,
                                   field="price_pc", value=player.get("price_pc"), segment_key=MarketSegmentKey.PC.value, platform="pc", external_id=external_id or "")
                ps = _insert_price(session, card=card, source=source, raw_ingest_id=raw_ingest_id, observed_at=obs.observed_at,
                                   field="price_ps", value=player.get("price_ps"), segment_key=MarketSegmentKey.PLAYSTATION.value, platform="playstation", external_id=external_id or "")
                session.flush()

            cards_written += 1
            identities.append(status)
            if pc is not None:
                pc_written += 1
                quarantined += int(pc.quality_status != DataQualityStatus.VALID.value)
            if ps is not None:
                ps_written += 1
                quarantined += int(ps.quality_status != DataQualityStatus.VALID.value)
        except Exception as exc:
            malformed += 1
            # Raw page payload already remains immutable through raw_ingest_id. Record
            # only safe item identity/error metadata here; do not duplicate raw payload.
            session.add(DataQualityIncident(
                detected_at=datetime.now(UTC),
                source_id=source.id,
                severity="warning",
                incident_type="parse_futbin_item_persistence",
                description="Parse/FUTBIN catalogue item failed normalization/persistence and was isolated",
                metadata_json={
                    "raw_ingest_id": str(raw_ingest_id) if raw_ingest_id else None,
                    "provider_external_id": external_id,
                    "error_type": type(exc).__name__,
                },
            ))
            continue
    session.flush()
    return {
        "seen": seen, "cards_written": cards_written, "pc_references": pc_written, "ps_references": ps_written,
        "malformed": malformed, "quarantined_or_suspect": quarantined,
        "page": data.get("page"), "page_count_returned": data.get("total"), "identity_statuses": identities,
    }


def _details_player(obs: RawObservation) -> dict[str, Any]:
    data = _body_data(obs)
    # Parse responses may wrap a single player in player/details; keep normalization defensive.
    for key in ("player", "details"):
        if isinstance(data.get(key), dict):
            return data[key]
    return data


def ingest_parse_futbin_player_details(session: Session, obs: RawObservation, *, raw_ingest_id=None, player_id: str | int | None = None) -> dict[str, Any]:
    player = _details_player(obs)
    if player_id is not None and player.get("id") is None:
        player = {**player, "id": str(player_id)}
    prices = player.get("prices") if isinstance(player.get("prices"), dict) else {}
    if player.get("price_pc") is None:
        player["price_pc"] = prices.get("pc") or prices.get("PC") or prices.get("price_pc")
    if player.get("price_ps") is None:
        player["price_ps"] = prices.get("ps") or prices.get("PS") or prices.get("playstation") or prices.get("price_ps")
    card, status = _upsert_parse_card(session, player, observed_at=obs.observed_at)
    if card is None:
        return {"seen": 1, "cards_written": 0, "pc_references": 0, "ps_references": 0, "malformed": 1, "identity_status": IdentityStatus.UNRESOLVED.value}
    source = get_or_create_source(session, "parse_futbin")
    external_id = str(player.get("id"))
    pc = _insert_price(session, card=card, source=source, raw_ingest_id=raw_ingest_id, observed_at=obs.observed_at,
                       field="price_pc", value=player.get("price_pc"), segment_key=MarketSegmentKey.PC.value, platform="pc", external_id=external_id)
    ps = _insert_price(session, card=card, source=source, raw_ingest_id=raw_ingest_id, observed_at=obs.observed_at,
                       field="price_ps", value=player.get("price_ps"), segment_key=MarketSegmentKey.PLAYSTATION.value, platform="playstation", external_id=external_id)
    return {
        "seen": 1, "cards_written": 1, "pc_references": int(pc is not None), "ps_references": int(ps is not None),
        "malformed": 0, "identity_status": status,
        "quarantined_or_suspect": sum(int(x is not None and x.quality_status != DataQualityStatus.VALID.value) for x in (pc, ps)),
    }
