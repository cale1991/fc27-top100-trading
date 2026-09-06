from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from fc27trader.db.models import ManualVerificationRequest
from .manual_verification import VerificationRequestDraft
from .market_segments import get_market_segment


def persist_verification_request(
    session: Session,
    draft: VerificationRequestDraft,
    *,
    candidate_id: uuid.UUID | None = None,
    reference_observation_id: int | None = None,
    ttl_seconds: int = 600,
) -> ManualVerificationRequest:
    segment = get_market_segment(session, game_year=26, segment_key="PC")
    row = ManualVerificationRequest(
        candidate_id=candidate_id,
        card_id=uuid.UUID(draft.card_id),
        platform="pc",
        market_segment_id=segment.id,
        requested_at=draft.requested_at,
        priority=draft.priority,
        status="pending",
        reason=draft.reason,
        reference_observation_id=reference_observation_id,
        latest_reference_price=draft.latest_reference_price,
        reference_timestamp=draft.reference_timestamp,
        reference_uncertainty_pct=(Decimal(str(draft.reference_uncertainty_pct)) if draft.reference_uncertainty_pct is not None else None),
        expected_acquisition_min=draft.expected_acquisition_min,
        expected_acquisition_max=draft.expected_acquisition_max,
        attractive_at_or_below=draft.attractive_at_or_below,
        required_information=draft.required_information,
        expected_information_value=Decimal(str(draft.expected_information_value)),
        expires_at=draft.requested_at + timedelta(seconds=ttl_seconds),
        metadata_json={},
    )
    session.add(row)
    session.flush()
    return row
