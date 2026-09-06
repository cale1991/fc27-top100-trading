from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fc27trader.collectors.futzip import FutzipItem, parse_futzip_rss
from fc27trader.db.models import CardSourceId, ContentEvent, ProviderFeedEvent, ProviderFeedState, RawIngest
from fc27trader.db.repositories import get_or_create_source, upsert_external_card_stub
from fc27trader.domain.enums import DataQualityStatus, GapStatus, IdentityStatus, MarketSegmentKey, ObservationSemantics
from fc27trader.ingestion.dedupe import stable_hash
from fc27trader.services.market_segments import get_market_segment


def _quality(item: FutzipItem, retrieved_at: datetime) -> str:
    if item.provider_timestamp is not None and item.provider_timestamp > retrieved_at + timedelta(minutes=10):
        return DataQualityStatus.QUARANTINED.value
    if item.feed_key == "movers":
        if not item.old_price or not item.new_price or item.old_price <= 0 or item.new_price <= 0:
            return DataQualityStatus.QUARANTINED.value
        ratio = max(item.old_price, item.new_price) / min(item.old_price, item.new_price)
        if ratio >= 100:
            return DataQualityStatus.QUARANTINED.value
        if ratio >= 10:
            return DataQualityStatus.SUSPECT.value
    return DataQualityStatus.VALID.value


def _ensure_futzip_card(session: Session, item: FutzipItem, *, game_year: int):
    if not item.provider_card_id:
        return None, IdentityStatus.UNRESOLVED.value
    card = upsert_external_card_stub(
        session,
        source_key="futzip",
        external_id=item.provider_card_id,
        game_year=game_year,
        name=item.player_name or f"futzip:{item.provider_card_id}",
        rating=item.rating,
        attributes={"identity_source": "futzip_feed", "identity_status": IdentityStatus.UNRESOLVED.value},
    )
    # Enrich only descriptive fields from the same provider identity. Do not cross-provider merge.
    if item.player_name and (not card.name or card.name.startswith("unknown:") or card.name.startswith("futzip:")):
        card.name = item.player_name
    if item.rating and card.rating is None:
        card.rating = item.rating
    source = get_or_create_source(session, "futzip")
    mapping = session.scalar(select(CardSourceId).where(
        CardSourceId.source_id == source.id,
        CardSourceId.external_id == item.provider_card_id,
    ))
    if mapping:
        mapping.mapping_method = mapping.mapping_method or "stable_provider_id_only"
        mapping.mapping_confidence = mapping.mapping_confidence or Decimal("0.70")
        mapping.mapping_status = mapping.mapping_status or IdentityStatus.UNRESOLVED.value
        return card, mapping.mapping_status
    return card, IdentityStatus.UNRESOLVED.value


def _feed_state(session: Session, source_id, feed_key: str, source_url: str) -> ProviderFeedState:
    row = session.scalar(select(ProviderFeedState).where(
        ProviderFeedState.source_id == source_id,
        ProviderFeedState.feed_key == feed_key,
    ))
    if row is None:
        row = ProviderFeedState(
            source_id=source_id,
            feed_key=feed_key,
            source_url=source_url,
            consecutive_failures=0,
            gap_status=GapStatus.UNKNOWN_COVERAGE.value,
            metadata_json={},
        )
        session.add(row)
        session.flush()
    return row


def ingest_futzip_feed(
    session: Session,
    *,
    raw_ingest: RawIngest,
    feed_key: str,
    body: bytes,
    retrieved_at: datetime,
    source_url: str,
    etag: str | None = None,
    last_modified: str | None = None,
    game_year: int = 26,
) -> dict:
    source = get_or_create_source(session, "futzip")
    source.name = "FUTZIP"
    source.source_class = "public_feed"
    source.automation_policy = "public_rss"
    source.training_policy = "provider_context_with_provenance"
    source.enabled = True
    source.metadata_json = {**(source.metadata_json or {}), "market_platform_semantics": "rss_unspecified"}

    state = _feed_state(session, source.id, feed_key, source_url)
    previous_success = state.last_success_at
    items, failures = parse_futzip_rss(body, feed_key)
    timestamps = [i.provider_timestamp for i in items if i.provider_timestamp is not None]
    newest = max(timestamps) if timestamps else None
    oldest = min(timestamps) if timestamps else None
    coverage_seconds = int((newest - oldest).total_seconds()) if newest and oldest else None
    if previous_success and oldest:
        gap = GapStatus.COMPLETE_WINDOW.value if oldest <= previous_success else GapStatus.POSSIBLE_GAP.value
    else:
        gap = GapStatus.UNKNOWN_COVERAGE.value

    unknown_segment = get_market_segment(session, game_year=game_year, segment_key=MarketSegmentKey.UNKNOWN.value)
    stats = {
        "items_seen": len(items) + len(failures),
        "items_parsed": len(items),
        "items_ingested": 0,
        "duplicates": 0,
        "parse_failures": len(failures),
        "quarantined": 0,
        "unique_provider_card_ids": len({i.provider_card_id for i in items if i.provider_card_id}),
        "newest_provider_timestamp": newest,
        "oldest_provider_timestamp": oldest,
        "market_context_only": 0,
        "pc_references_created": 0,
        "console_references_created": 0,
        "switch_references_created": 0,
        "gap_status": gap,
    }
    for item in items:
        existing = session.scalar(select(ProviderFeedEvent).where(
            ProviderFeedEvent.source_id == source.id,
            ProviderFeedEvent.feed_key == feed_key,
            ProviderFeedEvent.provider_event_id == item.guid,
        ))
        if existing:
            stats["duplicates"] += 1
            continue
        card, identity_status = _ensure_futzip_card(session, item, game_year=game_year)
        quality = _quality(item, retrieved_at)
        if quality == DataQualityStatus.QUARANTINED.value:
            stats["quarantined"] += 1
        semantics = ObservationSemantics.MARKET_CONTEXT.value if feed_key == "movers" else ObservationSemantics.CONTENT_EVENT.value
        row = ProviderFeedEvent(
            source_id=source.id,
            raw_ingest_id=raw_ingest.id,
            market_segment_id=unknown_segment.id,
            game_year=game_year,
            feed_key=feed_key,
            event_type={"movers": "MARKET_MOVE", "new": "NEW_CARD", "sbc": "SBC"}[feed_key],
            provider_event_id=item.guid,
            provider_card_id=item.provider_card_id,
            card_id=card.id if card else None,
            identity_status=identity_status,
            title=item.title,
            description=item.description,
            source_url=source_url,
            entity_url=item.link,
            provider_timestamp=item.provider_timestamp,
            retrieved_at=retrieved_at,
            inserted_at=datetime.now(UTC),
            old_price=item.old_price,
            new_price=item.new_price,
            absolute_change=(item.new_price - item.old_price) if item.new_price is not None and item.old_price is not None else None,
            percentage_change=Decimal(str(item.percentage_change)) if item.percentage_change is not None else None,
            rating=item.rating,
            observation_semantics=semantics,
            state_completeness="unknown",
            quality_status=quality,
            parser_version=(raw_ingest.parser_version or "futzip-rss-v1"),
            payload_json={
                "raw_item_xml": item.raw_xml,
                "raw_ingest_id": str(raw_ingest.id),
                "platform_semantics": "unspecified_in_rss",
                "feed_is_event_stream": True,
            },
        )
        session.add(row)
        session.flush()
        stats["items_ingested"] += 1
        if feed_key == "movers":
            stats["market_context_only"] += 1
        elif feed_key == "sbc":
            event_hash = stable_hash({"source": "futzip", "feed": "sbc", "guid": item.guid})
            if session.scalar(select(ContentEvent).where(ContentEvent.event_hash == event_hash)) is None:
                session.add(ContentEvent(
                    event_hash=event_hash,
                    game_year=game_year,
                    event_type="sbc_released",
                    evidence_class="measured_provider",
                    source_id=source.id,
                    raw_ingest_id=raw_ingest.id,
                    external_id=item.guid,
                    title=item.title,
                    summary=item.description,
                    published_at=item.provider_timestamp,
                    effective_at=item.provider_timestamp,
                    detected_at=retrieved_at,
                    source_url=item.link or source_url,
                    payload_json={
                        "information_class": "PROVIDER_DATA",
                        "authority_priority": "below_ea_official",
                        "provider_feed_event_id": str(row.id),
                    },
                ))

    state.etag = etag or state.etag
    state.last_modified = last_modified or state.last_modified
    state.last_poll_at = retrieved_at
    state.last_success_at = retrieved_at
    state.last_http_status = 200
    state.consecutive_failures = 0
    state.newest_provider_event_at = newest or state.newest_provider_event_at
    state.oldest_provider_event_at = oldest or state.oldest_provider_event_at
    state.inferred_coverage_seconds = coverage_seconds
    state.gap_status = gap
    state.metadata_json = {
        **(state.metadata_json or {}),
        "feed_is_complete_snapshot": False,
        "last_parse_failures": len(failures),
        "last_items_seen": stats["items_seen"],
        "last_items_ingested": stats["items_ingested"],
    }
    session.flush()
    return stats


def mark_futzip_not_modified(session: Session, *, feed_key: str, source_url: str, retrieved_at: datetime, etag: str | None, last_modified: str | None) -> ProviderFeedState:
    source = get_or_create_source(session, "futzip")
    state = _feed_state(session, source.id, feed_key, source_url)
    state.etag = etag or state.etag
    state.last_modified = last_modified or state.last_modified
    state.last_poll_at = retrieved_at
    state.last_success_at = retrieved_at
    state.last_http_status = 304
    state.consecutive_failures = 0
    session.flush()
    return state


def mark_futzip_failure(session: Session, *, feed_key: str, source_url: str, retrieved_at: datetime, error: str) -> ProviderFeedState:
    source = get_or_create_source(session, "futzip")
    state = _feed_state(session, source.id, feed_key, source_url)
    state.last_poll_at = retrieved_at
    state.last_http_status = None
    state.consecutive_failures = (state.consecutive_failures or 0) + 1
    state.metadata_json = {**(state.metadata_json or {}), "last_error": error[:1000]}
    session.flush()
    return state
