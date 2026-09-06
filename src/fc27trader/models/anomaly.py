from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev


@dataclass(frozen=True, slots=True)
class AnomalyEstimate:
    z_score: float
    is_anomaly: bool
    direction: str


def price_anomaly(current: float, history: list[float], *, threshold: float = 2.5) -> AnomalyEstimate:
    if len(history)<5:return AnomalyEstimate(0.0,False,"none")
    sd=pstdev(history)
    if sd==0:return AnomalyEstimate(0.0,False,"none")
    z=(current-mean(history))/sd
    return AnomalyEstimate(z,abs(z)>=threshold,"high" if z>0 else "low")
