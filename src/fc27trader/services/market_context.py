from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.db.models import CollectionTarget, ContentEvent


def immutable_market_context(session: Session, *, card_id, observed_at: datetime) -> dict:
    since = observed_at - timedelta(hours=24)
    events = list(session.scalars(
        select(ContentEvent)
        .where(ContentEvent.detected_at >= since)
        .order_by(ContentEvent.detected_at.desc())
        .limit(20)
    ))
    target = session.scalar(select(CollectionTarget).where(CollectionTarget.card_id == card_id, CollectionTarget.platform == "pc"))
    return {
        "captured_at": observed_at.isoformat(),
        "attention_tier": target.tier if target else None,
        "attention_priority": target.priority if target else None,
        "recent_content_events": [
            {"id": str(e.id), "type": e.event_type, "detected_at": e.detected_at.isoformat(), "title": e.title}
            for e in events
        ],
        "liquidity_proxy": None,
        "market_regime": None,
        "phase": "fc26_real_market_phase1",
    }
