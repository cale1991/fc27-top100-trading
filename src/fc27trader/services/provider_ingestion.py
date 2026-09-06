from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import orjson
from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.collectors.base import RawObservation
from fc27trader.db.models import Card, CardSourceId, ProviderEntity, Source
from fc27trader.db.repositories import (
    get_or_create_source,
    insert_reference_price_observation,
    upsert_external_card,
)
from fc27trader.ingestion.normalizer import (
    normalize_futdb_entities,
    normalize_futdb_players,
    normalize_futdb_price,
    normalize_thecoinprinter,
)
from fc27trader.services.card_identity import ensure_source_mapping
from fc27trader.services.market_context import immutable_market_context
from fc27trader.services.market_segments import get_market_segment
from fc27trader.services.reference_quality import reference_quality


def _market_segment_id(session: Session, key: str, game_year: int = 26):
    """Resolve segment in production while keeping pure/fake-session unit tests lightweight."""
    try:
        segment = get_market_segment(session, game_year=game_year, segment_key=key)
        return getattr(segment, "id", None)
    except (AttributeError, TypeError):
        return None


def _entity_names(session: Session, source_key: str) -> dict[str, dict[str, str]]:
    source = session.scalar(select(Source).where(Source.key == source_key))
    if source is None:
        return {}
    result: dict[str, dict[str, str]] = {}
    rows = session.scalars(select(ProviderEntity).where(ProviderEntity.source_id == source.id))
    for row in rows:
        if row.name:
            result.setdefault(row.entity_type, {})[row.external_id] = row.name
    return result


def ingest_futdb_entity_page(session: Session, obs: RawObservation, *, entity_type: str) -> dict[str, Any]:
    source = get_or_create_source(session, "futdb")
    rows, pagination = normalize_futdb_entities(obs, entity_type)
    now = datetime.now(UTC)
    written = 0
    for item in rows:
        existing = session.scalar(select(ProviderEntity).where(
            ProviderEntity.source_id == source.id,
            ProviderEntity.entity_type == entity_type,
            ProviderEntity.external_id == item["external_id"],
        ))
        if existing is None:
            existing = ProviderEntity(
                source_id=source.id,
                entity_type=entity_type,
                external_id=item["external_id"],
                name=item["name"],
                updated_at=now,
                metadata_json=item["metadata"],
            )
            session.add(existing)
            written += 1
        else:
            existing.name = item["name"]
            existing.updated_at = now
            existing.metadata_json = item["metadata"]
    session.flush()
    return {"seen": len(rows), "written": written, "pagination": pagination}


def _add_cross_provider_mappings(session: Session, card: Card, cross_ids: dict[str, str] | None) -> None:
    for provider, external_id in (cross_ids or {}).items():
        source = get_or_create_source(session, provider)
        existing = session.scalar(select(CardSourceId).where(
            CardSourceId.source_id == source.id,
            CardSourceId.external_id == external_id,
        ))
        if existing is None:
            ensure_source_mapping(
                session,
                card=card,
                source=source,
                external_id=external_id,
                source_url=None,
                mapping_method="futdb_cross_id",
                mapping_confidence=0.98,
            )


def ingest_futdb_player_page(session: Session, obs: RawObservation) -> dict[str, Any]:
    cards, pagination = normalize_futdb_players(obs, entity_names=_entity_names(session, "futdb"))
    created_or_updated = 0
    for item in cards:
        card = upsert_external_card(
            session,
            source_key=item.source_key,
            external_id=item.external_id,
            game_year=item.game_year,
            name=item.name,
            rating=item.rating,
            primary_position=item.primary_position,
            alt_positions=item.alt_positions,
            league=item.league,
            club=item.club,
            nation=item.nation,
            rarity=item.rarity,
            attributes=item.attributes,
            ea_resource_id=item.ea_resource_id,
            ea_asset_id=item.ea_asset_id,
            playstyles=item.playstyles,
            playstyles_plus=item.playstyles_plus,
            roles=item.roles,
            image_id=item.image_id,
            image_url=item.image_url,
            source_url=item.source_url,
        )
        _add_cross_provider_mappings(session, card, item.cross_provider_ids)
        created_or_updated += 1
    session.flush()
    return {"seen": len(cards), "written": created_or_updated, "pagination": pagination}


def _reference_metadata(session: Session, card: Card, provider_key: str, observed_at: datetime, raw_ingest_id, extra: dict | None = None) -> dict:
    return {
        "observation_kind": "reference_price",
        "executable": False,
        "provider": provider_key,
        "raw_ingest_id": str(raw_ingest_id) if raw_ingest_id else None,
        "uncertainty_method": "phase1_age_prior_unmeasured",
        "market_context": immutable_market_context(session, card_id=card.id, observed_at=observed_at),
        **(extra or {}),
    }


def ingest_futdb_price(session: Session, obs: RawObservation, *, player_id: int | str, raw_ingest_id=None):
    snapshot = normalize_futdb_price(obs, player_id=player_id)
    if snapshot is None or snapshot.lowest_bin is None:
        return None
    source = get_or_create_source(session, "futdb")
    mapping = session.scalar(select(CardSourceId).where(CardSourceId.source_id == source.id, CardSourceId.external_id == str(player_id)))
    if mapping is None:
        raise LookupError(f"FUT-DB player {player_id} has not been ingested into the card universe")
    card = session.get(Card, mapping.card_id)
    uncertainty, confidence, _ = reference_quality("futdb", snapshot.source_updated_at, snapshot.observed_at)
    segment_id = _market_segment_id(session, "PC", game_year=26)
    return insert_reference_price_observation(
        session,
        card=card,
        source_key="futdb",
        observed_at=snapshot.observed_at,
        provider_timestamp=snapshot.source_updated_at,
        price=snapshot.lowest_bin,
        raw_ingest_id=raw_ingest_id,
        price_kind="provider_pc_reference",
        provider_role="reference",
        evidence_class="measured_provider",
        uncertainty_pct=uncertainty,
        confidence=confidence,
        metadata=_reference_metadata(session, card, "futdb", snapshot.observed_at, raw_ingest_id, {
            "provider_external_id": str(player_id),
        }),
        platform="pc", market_segment_id=segment_id,
    )


def ingest_thecoinprinter_page(session: Session, obs: RawObservation, *, raw_ingest_id=None) -> dict[str, Any]:
    cards, snapshots = normalize_thecoinprinter(obs)
    card_by_external: dict[str, Card] = {}
    for item in cards:
        card_by_external[item.external_id] = upsert_external_card(
            session,
            source_key=item.source_key,
            external_id=item.external_id,
            game_year=item.game_year,
            name=item.name,
            rating=item.rating,
            primary_position=item.primary_position,
            alt_positions=item.alt_positions,
            league=item.league,
            club=item.club,
            nation=item.nation,
            rarity=item.rarity,
            attributes=item.attributes,
            image_id=item.image_id,
            image_url=item.image_url,
            source_url=item.source_url,
        )
    prices_written = 0
    latest_provider_timestamp = None
    for snapshot in snapshots:
        if snapshot.lowest_bin is None:
            continue
        card = card_by_external[snapshot.card_external_id]
        uncertainty, confidence, _ = reference_quality("thecoinprinter", snapshot.source_updated_at, snapshot.observed_at)
        segment_key = "PC" if snapshot.platform.value == "pc" else "CONSOLE_GENERIC" if snapshot.platform.value == "console" else "UNKNOWN"
        market_segment_id = _market_segment_id(session, segment_key, game_year=26)
        row = insert_reference_price_observation(
            session,
            card=card,
            source_key="thecoinprinter",
            observed_at=snapshot.observed_at,
            provider_timestamp=snapshot.source_updated_at,
            price=snapshot.lowest_bin,
            raw_ingest_id=raw_ingest_id,
            price_kind=f"provider_{snapshot.platform.value}_reference",
            provider_role="reference",
            evidence_class="measured_provider",
            uncertainty_pct=uncertainty,
            confidence=confidence,
            metadata=_reference_metadata(session, card, "thecoinprinter", snapshot.observed_at, raw_ingest_id, {
                "provider_external_id": snapshot.card_external_id,
            }),
            platform=snapshot.platform.value, market_segment_id=market_segment_id,
        )
        if row is not None:
            prices_written += 1
        if snapshot.source_updated_at and (latest_provider_timestamp is None or snapshot.source_updated_at > latest_provider_timestamp):
            latest_provider_timestamp = snapshot.source_updated_at
    payload = orjson.loads(obs.body)
    return {
        "seen": len(cards),
        "cards_written": len(cards),
        "prices_written": prices_written,
        "pagination": payload.get("pagination") or {},
        "latest_provider_timestamp": latest_provider_timestamp,
    }
