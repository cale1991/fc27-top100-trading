from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median


@dataclass(frozen=True, slots=True)
class AcquisitionSample:
    discount_to_reference: float
    time_to_acquisition_seconds: float
    quantity_available: int = 1


@dataclass(frozen=True, slots=True)
class AcquisitionEstimate:
    target_discount: float
    acquisition_probability: float
    expected_time_seconds: float | None
    expected_quantity: float
    sample_count: int


class EmpiricalAcquisitionModel:
    """Learns undercut availability from empirical observations.

    Callers segment samples by card / price tier / category / liquidity /
    time-of-day / regime / content timing / volatility before fitting. This
    class intentionally has no universal 2%, 3%, or 5% undercut assumption.
    """

    def __init__(self, samples: list[AcquisitionSample]):
        self.samples = samples

    def estimate(self, target_discount: float) -> AcquisitionEstimate:
        if not self.samples:
            return AcquisitionEstimate(target_discount, 0.0, None, 0.0, 0)
        qualifying = [s for s in self.samples if s.discount_to_reference >= target_discount]
        probability = len(qualifying) / len(self.samples)
        expected_time = median([s.time_to_acquisition_seconds for s in qualifying]) if qualifying else None
        expected_quantity = mean([s.quantity_available for s in qualifying]) if qualifying else 0.0
        return AcquisitionEstimate(
            target_discount=target_discount,
            acquisition_probability=probability,
            expected_time_seconds=expected_time,
            expected_quantity=expected_quantity,
            sample_count=len(self.samples),
        )
