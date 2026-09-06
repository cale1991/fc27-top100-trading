from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.collectors.base import RawObservation
from fc27trader.domain.events import MarketEvent
from fc27trader.domain.market import MarketSnapshot as DomainMarketSnapshot
from fc27trader.ingestion.dedupe import stable_hash
from fc27trader.ingestion.raw_store import StoredRaw
from fc27trader.services.card_identity import ensure_source_mapping, resolve_card_for_provider

from .models import Card, CardSourceId, ContentEvent, MarketSnapshot, RawIngest, Source


def get_or_create_source(session: Session, key: str) -> Source:
    source = session.scalar(select(Source).where(Source.key == key))
    if source:
        return source
    source = Source(
        key=key,
        name=key,
        source_class="unknown",
        automation_policy="unknown",
        training_policy="unknown",
        enabled=True,
        metadata_json={},
    )
    session.add(source)
    session.flush()
    return source


def record_raw_ingest(session: Session, obs: RawObservation, stored: StoredRaw) -> RawIngest:
    source = get_or_create_source(session, obs.source_key)
    existing = session.scalar(
        select(RawIngest).where(
            RawIngest.source_id == source.id,
            RawIngest.checksum_sha256 == stored.checksum_sha256,
        )
    )
    if existing:
        return existing
    row = RawIngest(
        source_id=source.id,
        source_kind=obs.source_kind,
        request_url=obs.url,
        request_method="GET",
        http_status=obs.status_code,
        content_type=obs.content_type,
        source_timestamp=obs.source_timestamp,
        observed_at=obs.observed_at,
        retrieved_at=obs.observed_at,
        checksum_sha256=stored.checksum_sha256,
        etag=obs.etag,
        last_modified=obs.last_modified,
        storage_uri=stored.storage_uri,
        payload_size=stored.payload_size,
        parser_version=(obs.metadata or {}).get("parser_version"),
        schema_version=(obs.metadata or {}).get("schema_version", "1"),
        inserted_at=datetime.now(UTC),
        success=True,
        metadata_json=obs.metadata,
    )
    session.add(row)
    session.flush()
    return row


def upsert_external_card_stub(
    session: Session,
    source_key: str,
    external_id: str,
    game_year: int,
    name: str | None = None,
    rating: int | None = None,
    attributes: dict | None = None,
) -> Card:
    source = get_or_create_source(session, source_key)
    mapping = session.scalar(
        select(CardSourceId).where(
            CardSourceId.source_id == source.id,
            CardSourceId.external_id == external_id,
        )
    )
    if mapping:
        return session.get(Card, mapping.card_id)

    now = datetime.now(UTC)
    card = Card(
        game_year=game_year,
        name=name or f"unknown:{source_key}:{external_id}",
        rating=rating,
        attributes_json=attributes or {},
        playstyles_json={},
        roles_json={},
        created_at=now,
        updated_at=now,
    )
    session.add(card)
    session.flush()
    session.add(CardSourceId(card_id=card.id, source_id=source.id, external_id=external_id))
    session.flush()
    return card


def upsert_external_card(
    session: Session,
    *,
    source_key: str,
    external_id: str,
    game_year: int,
    name: str,
    rating: int | None = None,
    primary_position: str | None = None,
    alt_positions: list[str] | None = None,
    league: str | None = None,
    club: str | None = None,
    nation: str | None = None,
    rarity: str | None = None,
    attributes: dict | None = None,
    ea_resource_id: int | None = None,
    ea_asset_id: int | None = None,
    playstyles: list[str] | None = None,
    playstyles_plus: list[str] | None = None,
    roles: dict | None = None,
    image_id: str | None = None,
    image_url: str | None = None,
    source_url: str | None = None,
) -> Card:
    source = get_or_create_source(session, source_key)
    card, mapping_method, mapping_confidence = resolve_card_for_provider(
        session,
        source=source,
        external_id=external_id,
        game_year=game_year,
        ea_resource_id=ea_resource_id,
        name=name,
        rating=rating,
        primary_position=primary_position,
        league=league,
        club=club,
        nation=nation,
    )
    now = datetime.now(UTC)
    if card is None:
        card = Card(
            game_year=game_year,
            name=name,
            created_at=now,
            updated_at=now,
            attributes_json={},
            playstyles_json={},
            roles_json={},
        )
        session.add(card)
        session.flush()

    ensure_source_mapping(
        session,
        card=card,
        source=source,
        external_id=external_id,
        source_url=source_url,
        mapping_method=mapping_method,
        mapping_confidence=mapping_confidence,
    )

    card.name = name
    card.rating = rating
    if primary_position is not None:
        card.primary_position = primary_position
    card.league = league or card.league
    card.club = club or card.club
    card.nation = nation or card.nation
    card.rarity = rarity or card.rarity
    card.ea_resource_id = ea_resource_id or card.ea_resource_id
    card.ea_asset_id = ea_asset_id or card.ea_asset_id
    card.image_id = image_id or card.image_id
    card.image_url = image_url or card.image_url
    merged_attributes = dict(card.attributes_json or {})
    merged_attributes.update(attributes or {})
    merged_attributes["alt_positions"] = alt_positions or merged_attributes.get("alt_positions", [])
    card.attributes_json = merged_attributes
    if playstyles is not None or playstyles_plus is not None:
        card.playstyles_json = {
            "playstyles": playstyles or [],
            "playstyles_plus": playstyles_plus or [],
        }
    if roles is not None:
        card.roles_json = roles
    card.updated_at = now
    session.flush()
    return card


def insert_market_snapshot(
    session: Session,
    snapshot: DomainMarketSnapshot,
    game_year: int,
    raw_ingest_id=None,
) -> MarketSnapshot:
    source = get_or_create_source(session, snapshot.source_key)
    card = upsert_external_card_stub(
        session,
        source_key=snapshot.source_key,
        external_id=snapshot.card_external_id,
        game_year=game_year,
    )
    spread_abs = None
    spread_pct = None
    if snapshot.lowest_bin and snapshot.best_bid:
        spread_abs = snapshot.lowest_bin - snapshot.best_bid
        spread_pct = Decimal(spread_abs) / Decimal(snapshot.lowest_bin)
    row = MarketSnapshot(
        observed_at=snapshot.observed_at,
        source_timestamp=snapshot.source_timestamp,
        card_id=card.id,
        source_id=source.id,
        raw_ingest_id=raw_ingest_id,
        platform=snapshot.platform.value,
        lowest_bin=snapshot.lowest_bin,
        best_bid=snapshot.best_bid,
        active_listings=snapshot.active_listings,
        sales_5m=snapshot.sales_5m,
        sales_15m=snapshot.sales_15m,
        spread_abs=spread_abs,
        spread_pct=spread_pct,
        source_updated_at=snapshot.source_updated_at,
        metadata_json={},
    )
    session.add(row)
    session.flush()
    return row


def insert_content_event(session: Session, event: MarketEvent, raw_ingest_id=None) -> ContentEvent:
    source = get_or_create_source(session, event.source_key)
    event_hash = stable_hash(
        {
            "event_type": event.event_type.value,
            "game_year": event.game_year,
            "source": event.source_key,
            "external_id": event.external_id,
            "title": event.title,
            "published_at": event.published_at,
            "effective_at": event.effective_at,
            "payload": event.payload,
        }
    )
    existing = session.scalar(select(ContentEvent).where(ContentEvent.event_hash == event_hash))
    if existing:
        return existing
    row = ContentEvent(
        event_hash=event_hash,
        game_year=event.game_year,
        event_type=event.event_type.value,
        evidence_class=event.evidence_class.value,
        source_id=source.id,
        raw_ingest_id=raw_ingest_id,
        external_id=event.external_id,
        title=event.title,
        summary=event.summary,
        published_at=event.published_at,
        effective_at=event.effective_at,
        expires_at=event.expires_at,
        detected_at=event.detected_at,
        source_url=event.source_url,
        payload_json={
            **event.payload,
            "affected_card_ids": event.affected_card_ids,
            "affected_segments": event.affected_segments,
        },
    )
    session.add(row)
    session.flush()
    return row




def reference_observation_key(
    *,
    card_id,
    source_id,
    observed_at: datetime,
    provider_timestamp: datetime | None,
    price: int,
    price_kind: str,
    platform: str = "pc",
    market_segment_id=None,
) -> str:
    """Stable identity for one exact provider retrieval.

    `observed_at` is intentionally part of the key: polling the same unchanged provider
    quote later is still a new time-series observation. Re-processing the exact same
    retrieval is idempotent.
    """
    return stable_hash({
        "card_id": str(card_id),
        "source_id": str(source_id),
        "platform": platform,
        "market_segment_id": str(market_segment_id) if market_segment_id else None,
        "provider_timestamp": provider_timestamp,
        "observed_at": observed_at,
        "price": int(price),
        "price_kind": price_kind,
    })

def insert_reference_price_observation(
    session: Session,
    *,
    card: Card,
    source_key: str,
    observed_at: datetime,
    price: int,
    provider_timestamp: datetime | None = None,
    raw_ingest_id=None,
    price_kind: str = "prevailing_bin_region",
    provider_role: str = "reference",
    evidence_class: str = "measured_provider",
    historical_provider_error_pct: float | None = None,
    uncertainty_pct: float | None = None,
    confidence: float | None = None,
    metadata: dict | None = None,
    platform: str = "pc",
    market_segment_id=None,
    quality_status: str = "VALID",
    state_completeness: str = "directly_observed",
    is_backfill: bool = False,
):
    from fc27trader.db.models import ReferencePriceObservation

    source = get_or_create_source(session, source_key)
    age_seconds = None
    if provider_timestamp is not None:
        age_seconds = max(0.0, (observed_at - provider_timestamp).total_seconds())
    observation_key = reference_observation_key(
        card_id=card.id,
        source_id=source.id,
        platform=platform,
        market_segment_id=market_segment_id,
        provider_timestamp=provider_timestamp,
        observed_at=observed_at,
        price=price,
        price_kind=price_kind,
    )
    existing = session.scalar(
        select(ReferencePriceObservation).where(ReferencePriceObservation.observation_key == observation_key)
    )
    if existing:
        return existing
    row = ReferencePriceObservation(
        observed_at=observed_at,
        provider_timestamp=provider_timestamp,
        card_id=card.id,
        source_id=source.id,
        raw_ingest_id=raw_ingest_id,
        market_segment_id=market_segment_id,
        platform=platform,
        inserted_at=datetime.now(UTC),
        price=price,
        price_kind=price_kind,
        provider_role=provider_role,
        evidence_class=evidence_class,
        observation_key=observation_key,
        age_seconds=Decimal(str(age_seconds)) if age_seconds is not None else None,
        historical_provider_error_pct=(
            Decimal(str(historical_provider_error_pct))
            if historical_provider_error_pct is not None else None
        ),
        uncertainty_pct=Decimal(str(uncertainty_pct)) if uncertainty_pct is not None else None,
        confidence=Decimal(str(confidence)) if confidence is not None else None,
        quality_status=quality_status,
        state_completeness=state_completeness,
        is_backfill=is_backfill,
        metadata_json=metadata or {},
    )
    session.add(row)
    session.flush()
    return row


def insert_execution_observation(
    session: Session,
    *,
    card: Card,
    source_key: str,
    observed_at: datetime,
    observation_type: str,
    source_timestamp: datetime | None = None,
    lowest_bin: int | None = None,
    best_bid: int | None = None,
    listing_prices: list[int] | None = None,
    listing_count: int | None = None,
    confidence: float = 1.0,
    expires_at: datetime | None = None,
    manual_verification_request_id=None,
    raw_ingest_id=None,
    metadata: dict | None = None,
    platform: str = "pc",
    market_segment_id=None,
    quality_status: str = "VALID",
):
    from fc27trader.db.models import ExecutionObservation

    source = get_or_create_source(session, source_key)
    row = ExecutionObservation(
        observed_at=observed_at,
        source_timestamp=source_timestamp,
        card_id=card.id,
        source_id=source.id,
        raw_ingest_id=raw_ingest_id,
        market_segment_id=market_segment_id,
        platform=platform,
        inserted_at=datetime.now(UTC),
        observation_type=observation_type,
        lowest_bin=lowest_bin,
        best_bid=best_bid,
        listing_prices_json=listing_prices or [],
        listing_count=listing_count if listing_count is not None else len(listing_prices or []),
        confidence=Decimal(str(confidence)),
        quality_status=quality_status,
        expires_at=expires_at,
        manual_verification_request_id=manual_verification_request_id,
        metadata_json=metadata or {},
    )
    session.add(row)
    session.flush()
    return row
