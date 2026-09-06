from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ReferenceFeatureConfig:
    age_penalty_half_life_seconds: float = 1800.0
    max_uncertainty_pct: float = 0.50


def derive_reference_features(
    *,
    reference_price: int | None,
    provider_timestamp: datetime | None,
    observed_at: datetime,
    historical_provider_error_pct: float | None,
    stated_uncertainty_pct: float | None,
    confidence: float | None,
    execution_price: int | None = None,
    execution_observed_at: datetime | None = None,
    config: ReferenceFeatureConfig = ReferenceFeatureConfig(),
) -> dict[str, float | int | None]:
    age = None
    if provider_timestamp is not None:
        age = max(0.0, (observed_at - provider_timestamp).total_seconds())

    empirical_error = max(0.0, historical_provider_error_pct or 0.0)
    stated = max(0.0, stated_uncertainty_pct or 0.0)
    if age is None:
        age_component = 0.10
    else:
        # Smoothly increases with age; this is uncertainty weighting, not an acquisition discount.
        age_component = 0.05 * (1.0 - math.exp(-age / max(1.0, config.age_penalty_half_life_seconds)))
    combined = math.sqrt(empirical_error**2 + stated**2 + age_component**2)
    combined = min(config.max_uncertainty_pct, combined)

    execution_age = None
    if execution_observed_at is not None:
        execution_age = max(0.0, (observed_at - execution_observed_at).total_seconds())
    gap = None
    if reference_price and execution_price is not None:
        gap = (execution_price - reference_price) / reference_price

    return {
        "reference_price": reference_price,
        "reference_age_seconds": age,
        "reference_provider_error_pct": historical_provider_error_pct,
        "reference_stated_uncertainty_pct": stated_uncertainty_pct,
        "reference_uncertainty_pct": combined,
        "reference_confidence": confidence,
        "execution_price": execution_price,
        "execution_age_seconds": execution_age,
        "reference_execution_gap_pct": gap,
    }
