from __future__ import annotations

"""Bridge non-executable market intelligence into a PC verification request.

A research signal in PlayStation/console/Switch is never itself actionable for the
current account.  When it is informative enough, this service creates a request
for fresh PC execution evidence instead of recommending execution elsewhere.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.db.models import ManualVerificationRequest, MarketSegment, ReferencePriceObservation
from fc27trader.services.market_segments import get_market_segment


def create_pc_verification_from_research_signal(
    session: Session,
    *,
    card_id: uuid.UUID,
    source_market_segment: MarketSegment,
    reason: str,
    priority: int = 7,
    pc_reference: ReferencePriceObservation | None = None,
    attractive_at_or_below: int | None = None,
    expected_information_value: float | None = None,
    expires_minutes: int = 15,
) -> ManualVerificationRequest | None:
    """Create one pending PC verification request from a non-PC research signal.

    Returns ``None`` when the originating market is already executable or an
    equivalent pending request already exists.  No non-PC price is copied into
    the PC reference fields.
    """
    if source_market_segment.executable_by_user:
        return None

    pc = get_market_segment(session, game_year=source_market_segment.game_year, segment_key="PC")
    existing = session.scalar(
        select(ManualVerificationRequest).where(
            ManualVerificationRequest.card_id == card_id,
            ManualVerificationRequest.market_segment_id == pc.id,
            ManualVerificationRequest.status == "pending",
        ).limit(1)
    )
    if existing is not None:
        return existing

    now = datetime.now(UTC)
    ref_time = None
    ref_price = None
    uncertainty = None
    ref_id = None
    if pc_reference is not None and pc_reference.market_segment_id == pc.id:
        ref_id = pc_reference.id
        ref_price = pc_reference.price
        ref_time = pc_reference.provider_timestamp or pc_reference.observed_at
        uncertainty = pc_reference.uncertainty_pct

    req = ManualVerificationRequest(
        card_id=card_id,
        platform="pc",
        market_segment_id=pc.id,
        requested_at=now,
        priority=priority,
        status="pending",
        reason=reason,
        reference_observation_id=ref_id,
        latest_reference_price=ref_price,
        reference_timestamp=ref_time,
        reference_uncertainty_pct=uncertainty,
        attractive_at_or_below=attractive_at_or_below,
        required_information="current lowest 5-10 PC BIN listings for exact card/version",
        expected_information_value=(Decimal(str(expected_information_value)) if expected_information_value is not None else None),
        expires_at=now + timedelta(minutes=expires_minutes),
        metadata_json={
            "trigger": "cross_market_research_signal",
            "source_market_segment": source_market_segment.segment_key,
            "source_market_segment_id": str(source_market_segment.id),
        },
    )
    session.add(req)
    session.flush()
    return req
