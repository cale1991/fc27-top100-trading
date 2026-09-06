from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from fc27trader.db.models import (
    Card,
    CardSourceId,
    CollectionTarget,
    OpportunityCandidate,
    PortfolioPosition,
    ReferencePriceObservation,
    Source,
)


def select_futdb_price_targets(session: Session, *, limit: int = 25) -> list[str]:
    """Select adaptive FUT-DB price targets under the provider request budget.

    Priority order is driven by active positions and dynamic attention/candidates,
    then by cards with the stalest/missing FUT-DB reference. This is not a watchlist.
    """
    source = session.scalar(select(Source).where(Source.key == "futdb"))
    if source is None:
        return []

    active_positions = set(session.scalars(select(PortfolioPosition.card_id).where(PortfolioPosition.quantity > 0)))
    candidates = {
        row.card_id: row
        for row in session.scalars(
            select(OpportunityCandidate).where(
                OpportunityCandidate.platform == "pc",
                OpportunityCandidate.status != "superseded",
            )
        )
    }
    attention = {
        row.card_id: row
        for row in session.scalars(
            select(CollectionTarget).where(CollectionTarget.platform == "pc", CollectionTarget.enabled.is_(True))
        )
    }
    mappings = list(
        session.execute(
            select(CardSourceId.card_id, CardSourceId.external_id)
            .where(CardSourceId.source_id == source.id)
        )
    )
    if not mappings:
        return []

    latest = {}
    rows = session.execute(
        select(ReferencePriceObservation.card_id, func.max(ReferencePriceObservation.observed_at))
        .where(ReferencePriceObservation.source_id == source.id, ReferencePriceObservation.platform == "pc")
        .group_by(ReferencePriceObservation.card_id)
    )
    latest.update({card_id: ts for card_id, ts in rows})
    now = datetime.now(UTC)

    ranked: list[tuple[float, str]] = []
    for card_id, external_id in mappings:
        score = 0.0
        if card_id in active_positions:
            score += 10_000
        target = attention.get(card_id)
        if target:
            score += 5_000 + max(0, 1_000 - target.priority)
        candidate = candidates.get(card_id)
        if candidate:
            score += 3_000 + max(0, 1_000 - (candidate.rank or 999))
        ts = latest.get(card_id)
        if ts is None:
            score += 2_000
        else:
            score += min(1_500, max(0.0, (now - ts).total_seconds() / 3600.0) * 10)
        ranked.append((score, external_id))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [external_id for _, external_id in ranked[:limit]]
