from __future__ import annotations

from sqlalchemy import case, desc, or_, select
from sqlalchemy.orm import Session

from fc27trader.db.models import CardSourceId, CollectionTarget, OpportunityCandidate, PortfolioPosition, Source


def select_parse_futbin_hot_targets(session: Session, *, limit: int = 10) -> list[str]:
    """Deterministic scarce-credit allocation: holdings > hot targets > active candidates."""
    source = session.scalar(select(Source).where(Source.key == "parse_futbin"))
    if source is None:
        return []
    mappings = list(session.execute(
        select(CardSourceId.external_id, CardSourceId.card_id)
        .where(CardSourceId.source_id == source.id)
    ))
    if not mappings:
        return []
    card_to_external = {card_id: external_id for external_id, card_id in mappings}
    card_ids = list(card_to_external)
    position_ids = set(session.scalars(select(PortfolioPosition.card_id).where(PortfolioPosition.card_id.in_(card_ids), PortfolioPosition.quantity > 0)))
    targets = list(session.scalars(select(CollectionTarget).where(CollectionTarget.card_id.in_(card_ids), CollectionTarget.enabled.is_(True)).order_by(CollectionTarget.priority.desc())))
    target_rank = {row.card_id: int(row.priority or 0) for row in targets}
    candidates = list(session.scalars(select(OpportunityCandidate).where(OpportunityCandidate.card_id.in_(card_ids), OpportunityCandidate.status != "superseded").order_by(OpportunityCandidate.opportunity_score.desc())))
    candidate_rank = {row.card_id: float(row.opportunity_score or 0) for row in candidates}
    scored = []
    for card_id, external_id in card_to_external.items():
        score = (1_000_000 if card_id in position_ids else 0) + target_rank.get(card_id, 0) * 100 + candidate_rank.get(card_id, 0)
        if score > 0:
            scored.append((score, external_id))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [external_id for _, external_id in scored[:limit]]
