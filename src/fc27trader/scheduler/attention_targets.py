from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.db.models import AttentionAllocation, CollectionTarget
from fc27trader.services.attention import AttentionDecision


def apply_attention_allocations(
    session: Session,
    decisions: list[AttentionDecision],
    *,
    ttl_seconds: int = 900,
) -> None:
    """Materialize the current attention allocation into collection_targets.

    collection_targets is scheduler state, not a permanent watchlist. Targets
    absent from the latest allocation are disabled and can re-enter later.
    """
    now = datetime.now(UTC)
    active_card_ids = {d.card_id for d in decisions}

    existing = list(session.scalars(select(CollectionTarget).where(CollectionTarget.platform == "pc")))
    by_card = {str(row.card_id): row for row in existing}
    for row in existing:
        if str(row.card_id) not in active_card_ids:
            row.enabled = False

    for d in decisions:
        row = by_card.get(d.card_id)
        if row is None:
            row = CollectionTarget(
                card_id=d.card_id,
                platform="pc",
                tier=d.tier,
                target_interval_seconds=d.target_interval_seconds,
                priority=max(1, int(1000 - min(999, d.attention_score * 100))),
                enabled=True,
                next_due_at=now,
                metadata_json={},
            )
            session.add(row)
        else:
            row.tier = d.tier
            row.target_interval_seconds = d.target_interval_seconds
            row.priority = max(1, int(1000 - min(999, d.attention_score * 100)))
            row.enabled = True
            row.next_due_at = min(row.next_due_at or now, now)
            row.metadata_json = {**(row.metadata_json or {}), "attention_reasons": d.reasons}

        session.add(
            AttentionAllocation(
                card_id=d.card_id,
                platform="pc",
                recomputed_at=now,
                valid_until=now + timedelta(seconds=ttl_seconds),
                attention_score=Decimal(str(d.attention_score)),
                tier=d.tier,
                target_interval_seconds=d.target_interval_seconds,
                reasons_json=d.reasons,
                metadata_json={},
            )
        )
    session.flush()
