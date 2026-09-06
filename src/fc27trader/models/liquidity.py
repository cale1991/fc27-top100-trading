from __future__ import annotations

from dataclasses import dataclass
from statistics import median


@dataclass(frozen=True, slots=True)
class LiquidityObservation:
    time_to_sale_seconds: float
    quantity: int = 1
    listing_price: int | None = None
    reference_price: int | None = None


@dataclass(frozen=True, slots=True)
class LiquidityEstimate:
    median_time_to_sale_seconds: float | None
    probability_sale_within_1h: float
    probability_sale_within_6h: float
    position_capacity_quantity: int
    sample_size: int


def estimate_liquidity(samples: list[LiquidityObservation], *, capacity_horizon_seconds: int = 21600) -> LiquidityEstimate:
    if not samples:
        return LiquidityEstimate(None, 0.0, 0.0, 0, 0)
    times = [max(0.0, x.time_to_sale_seconds) for x in samples]
    within_1h = sum(t <= 3600 for t in times) / len(times)
    within_6h = sum(t <= 21600 for t in times) / len(times)
    capacity = sum(max(1, x.quantity) for x in samples if x.time_to_sale_seconds <= capacity_horizon_seconds)
    return LiquidityEstimate(median(times), within_1h, within_6h, capacity, len(samples))
