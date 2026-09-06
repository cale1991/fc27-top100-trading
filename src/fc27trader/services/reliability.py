from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from fc27trader.db.models import ProviderReliabilitySnapshot


def record_unmeasured_reliability_context(session: Session, *, provider_key: str, market_segment_id=None, card_id=None, dimensions: dict | None=None) -> ProviderReliabilitySnapshot:
    """Infrastructure row only: zero samples means no statistical trust claim."""
    row=ProviderReliabilitySnapshot(provider_key=provider_key, market_segment_id=market_segment_id, card_id=card_id,
        calculated_at=datetime.now(UTC), sample_size=0, dimensions_json=dimensions or {}, metrics_json={
            "reference_error_pct": None, "directional_accuracy": None, "lead_lag_seconds": None,
            "staleness_bias": None, "volatility_response": None, "execution_distance": None,
            "event_response_accuracy": None,
        }, confidence=Decimal("0"), metadata_json={"status":"insufficient_data"})
    session.add(row); session.flush(); return row
