from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class VerificationDecision:
    should_request: bool
    expected_information_value: float
    reason: str


@dataclass(frozen=True, slots=True)
class VerificationRequestDraft:
    card_id: str
    requested_at: datetime
    priority: int
    reason: str
    latest_reference_price: int
    reference_timestamp: datetime | None
    reference_uncertainty_pct: float | None
    expected_acquisition_min: int | None
    expected_acquisition_max: int | None
    attractive_at_or_below: int | None
    required_information: str
    expected_information_value: float


def verification_value(
    *,
    probability_decision_changes: float,
    expected_profit_if_actionable: float,
    confidence_gain: float,
    interruption_cost: float,
) -> VerificationDecision:
    eiv = probability_decision_changes * expected_profit_if_actionable * confidence_gain - interruption_cost
    return VerificationDecision(
        should_request=eiv > 0,
        expected_information_value=eiv,
        reason="positive_expected_information_value" if eiv > 0 else "interrupt_cost_exceeds_value",
    )


def build_verification_request(
    *,
    card_id: str,
    requested_at: datetime,
    priority: int,
    reason: str,
    latest_reference_price: int,
    reference_timestamp: datetime | None,
    reference_uncertainty_pct: float | None,
    expected_acquisition_min: int | None,
    expected_acquisition_max: int | None,
    attractive_at_or_below: int | None,
    expected_information_value: float,
    sample_size: int = 10,
) -> VerificationRequestDraft:
    return VerificationRequestDraft(
        card_id=card_id,
        requested_at=requested_at,
        priority=priority,
        reason=reason,
        latest_reference_price=latest_reference_price,
        reference_timestamp=reference_timestamp,
        reference_uncertainty_pct=reference_uncertainty_pct,
        expected_acquisition_min=expected_acquisition_min,
        expected_acquisition_max=expected_acquisition_max,
        attractive_at_or_below=attractive_at_or_below,
        required_information=f"current lowest 5-{sample_size} PC BIN listings for exact card/version",
        expected_information_value=expected_information_value,
    )
