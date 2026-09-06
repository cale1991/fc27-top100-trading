from __future__ import annotations

import math
from statistics import median
from typing import Iterable


def percentile(values: Iterable[float], p: float) -> float | None:
    xs = sorted(float(x) for x in values)
    if not xs:
        return None
    if not 0 <= p <= 100:
        raise ValueError("p must be in [0, 100]")
    if len(xs) == 1:
        return xs[0]
    rank = (len(xs) - 1) * p / 100
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return xs[lo]
    frac = rank - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


def p50(values: Iterable[float]) -> float | None:
    xs = list(values)
    return float(median(xs)) if xs else None


def p90(values: Iterable[float]) -> float | None:
    return percentile(values, 90)


def p95(values: Iterable[float]) -> float | None:
    return percentile(values, 95)
