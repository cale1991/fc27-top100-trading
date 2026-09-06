from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.db.models import StrategyDiscoveryCandidate


def record_discovered_pattern(
    session: Session,
    *,
    pattern_key: str,
    sample_size: int,
    effect_size: float | None,
    confidence: float | None,
    description: str,
    feature_signature: dict,
    supporting_outcomes: dict | None = None,
) -> StrategyDiscoveryCandidate:
    now = datetime.now(UTC)
    row = session.scalar(select(StrategyDiscoveryCandidate).where(StrategyDiscoveryCandidate.pattern_key == pattern_key))
    status = "reviewable" if sample_size >= 30 and (confidence or 0) >= 0.75 else "observing"
    if row is None:
        row = StrategyDiscoveryCandidate(
            pattern_key=pattern_key, first_detected_at=now, last_seen_at=now, status=status,
            sample_size=sample_size, effect_size=Decimal(str(effect_size)) if effect_size is not None else None,
            confidence=Decimal(str(confidence)) if confidence is not None else None,
            description=description, feature_signature_json=feature_signature,
            supporting_outcomes_json=supporting_outcomes or {}, metadata_json={},
        )
        session.add(row)
    else:
        row.last_seen_at = now; row.status = status; row.sample_size = sample_size
        row.effect_size = Decimal(str(effect_size)) if effect_size is not None else None
        row.confidence = Decimal(str(confidence)) if confidence is not None else None
        row.description = description; row.feature_signature_json = feature_signature
        row.supporting_outcomes_json = supporting_outcomes or row.supporting_outcomes_json
    session.flush()
    return row
