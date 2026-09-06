from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.db.models import CommunityContent, CommunitySignal, CommunityTrader
from fc27trader.db.repositories import get_or_create_source, insert_content_event
from fc27trader.domain.enums import EvidenceClass, EventType
from fc27trader.domain.events import MarketEvent


@dataclass(frozen=True, slots=True)
class CommunitySignalInput:
    source_key: str
    source_platform: str
    author_handle: str
    published_at: datetime
    observed_at: datetime
    text: str
    external_id: str | None = None
    source_url: str | None = None
    external_author_id: str | None = None
    display_name: str | None = None
    card_id: uuid.UUID | None = None
    category_key: str | None = None
    direction: str = "watch"
    quoted_entry: int | None = None
    target_price: int | None = None
    catalyst: str | None = None
    horizon_seconds: int | None = None
    stated_confidence: float | None = None
    extraction_confidence: float | None = None
    preceded_market_move: bool | None = None
    metadata: dict | None = None


def ingest_community_signal(session: Session, item: CommunitySignalInput) -> CommunitySignal:
    """Persist permitted community content and mirror the extracted call into the core event stream."""
    trader = session.scalar(
        select(CommunityTrader).where(
            CommunityTrader.source_platform == item.source_platform,
            CommunityTrader.handle == item.author_handle,
        )
    )
    if trader is None:
        trader = CommunityTrader(
            source_platform=item.source_platform,
            external_author_id=item.external_author_id,
            handle=item.author_handle,
            display_name=item.display_name,
            enabled=True,
            created_at=datetime.now(UTC),
            metadata_json={},
        )
        session.add(trader)
        session.flush()

    source = get_or_create_source(session, item.source_key)
    content = CommunityContent(
        trader_id=trader.id,
        source_id=source.id,
        external_id=item.external_id,
        published_at=item.published_at,
        observed_at=item.observed_at,
        source_url=item.source_url,
        text=item.text,
        raw_ingest_id=None,
        metadata_json=item.metadata or {},
    )
    session.add(content)
    session.flush()
    signal = CommunitySignal(
        content_id=content.id,
        trader_id=trader.id,
        card_id=item.card_id,
        category_key=item.category_key,
        extracted_at=item.observed_at,
        direction=item.direction,
        quoted_entry=item.quoted_entry,
        target_price=item.target_price,
        catalyst=item.catalyst,
        horizon_seconds=item.horizon_seconds,
        stated_confidence=Decimal(str(item.stated_confidence)) if item.stated_confidence is not None else None,
        preceded_market_move=item.preceded_market_move,
        extraction_confidence=Decimal(str(item.extraction_confidence)) if item.extraction_confidence is not None else None,
        metadata_json=item.metadata or {},
    )
    session.add(signal)
    session.flush()

    event = MarketEvent(
        event_type=EventType.COMMUNITY_SIGNAL,
        evidence_class=EvidenceClass.MEASURED,
        game_year=26,
        source_key=item.source_key,
        external_id=item.external_id or str(content.id),
        title=f"Community call: {item.author_handle} {item.direction}",
        summary=item.catalyst or item.text[:280],
        published_at=item.published_at,
        effective_at=item.published_at,
        detected_at=item.observed_at,
        source_url=item.source_url,
        affected_card_ids=[str(item.card_id)] if item.card_id else [],
        affected_segments=[item.category_key] if item.category_key else [],
        payload={
            "community_signal_id": str(signal.id),
            "trader_id": str(trader.id),
            "quoted_entry": item.quoted_entry,
            "target_price": item.target_price,
            "horizon_seconds": item.horizon_seconds,
            "extraction_confidence": item.extraction_confidence,
        },
    )
    insert_content_event(session, event)
    # Strategy links are contextual evidence only; they do not define the production universe.
    try:
        from fc27trader.services.strategy_intelligence import link_community_signal_strategies
        link_community_signal_strategies(session, signal, item.text, item.catalyst)
    except Exception:
        # Community ingestion must not fail solely because the optional research layer is unavailable.
        pass
    return signal
