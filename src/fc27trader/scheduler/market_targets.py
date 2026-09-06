from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from fc27trader.db.models import CollectionTarget


def due_targets(session: Session, limit: int = 500) -> list[CollectionTarget]:
    now = datetime.now(UTC)
    stmt = (
        select(CollectionTarget)
        .where(
            CollectionTarget.enabled.is_(True),
            or_(CollectionTarget.next_due_at.is_(None), CollectionTarget.next_due_at <= now),
        )
        .order_by(CollectionTarget.priority.asc(), CollectionTarget.next_due_at.asc().nullsfirst())
        .limit(limit)
    )
    return list(session.scalars(stmt))
