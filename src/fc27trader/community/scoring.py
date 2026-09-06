from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from math import exp, log
from statistics import mean, median


@dataclass(frozen=True, slots=True)
class TrackedCall:
    occurred_at: datetime
    category: str | None
    horizon_seconds: int | None
    directional_correct: bool | None
    profitable_after_tax: bool | None
    return_pct: float | None
    benchmark_return_pct: float | None
    max_drawdown_pct: float | None
    timing_quality: float | None
    holding_seconds: int | None


@dataclass(frozen=True, slots=True)
class TraderScore:
    sample_size: int
    directional_accuracy: float | None
    profitable_after_tax_rate: float | None
    average_return_pct: float | None
    median_return_pct: float | None
    average_alpha_pct: float | None
    max_drawdown_pct: float | None
    average_drawdown_pct: float | None
    timing_quality: float | None
    average_holding_seconds: int | None
    recent_form_score: float | None
    sample_confidence: float
    reputation_score: float | None
    category_metrics: dict
    horizon_metrics: dict


def _avg(values: list[float]) -> float | None:
    return mean(values) if values else None


def _rate(values: list[bool]) -> float | None:
    return sum(1 for x in values if x) / len(values) if values else None


def _sample_confidence(n: int, full_confidence_n: int = 40) -> float:
    return min(1.0, (n / max(1, full_confidence_n)) ** 0.5)


def _bucket_horizon(seconds: int | None) -> str:
    if seconds is None:
        return "unknown"
    if seconds <= 3600:
        return "<=1h"
    if seconds <= 21600:
        return "1-6h"
    if seconds <= 86400:
        return "6-24h"
    if seconds <= 259200:
        return "1-3d"
    return ">3d"


def score_trader(
    calls: list[TrackedCall],
    *,
    now: datetime | None = None,
    full_confidence_n: int = 40,
    recent_half_life_days: float = 14.0,
) -> TraderScore:
    now = now or datetime.now(UTC)
    n = len(calls)
    directional = [c.directional_correct for c in calls if c.directional_correct is not None]
    profitable = [c.profitable_after_tax for c in calls if c.profitable_after_tax is not None]
    returns = [c.return_pct for c in calls if c.return_pct is not None]
    alphas = [
        c.return_pct - c.benchmark_return_pct
        for c in calls
        if c.return_pct is not None and c.benchmark_return_pct is not None
    ]
    drawdowns = [abs(c.max_drawdown_pct) for c in calls if c.max_drawdown_pct is not None]
    timing = [c.timing_quality for c in calls if c.timing_quality is not None]
    holdings = [c.holding_seconds for c in calls if c.holding_seconds is not None]

    half_life_seconds = max(1.0, recent_half_life_days * 86400)
    weighted_recent: list[tuple[float, float]] = []
    for c in calls:
        age = max(0.0, (now - c.occurred_at).total_seconds())
        weight = exp(-log(2) * age / half_life_seconds)
        if c.return_pct is not None:
            # 10% after-tax return maps near +1; negative returns remain negative.
            performance = max(-1.0, min(1.0, c.return_pct / 0.10))
            weighted_recent.append((performance, weight))
    recent_form = (
        sum(value * weight for value, weight in weighted_recent) / sum(weight for _, weight in weighted_recent)
        if weighted_recent else None
    )

    confidence = _sample_confidence(n, full_confidence_n)
    acc = _rate(directional)
    profit_rate = _rate(profitable)
    avg_alpha = _avg(alphas)
    timing_avg = _avg(timing)
    drawdown_avg = _avg(drawdowns)
    components = []
    if acc is not None:
        components.append((acc, 0.25))
    if profit_rate is not None:
        components.append((profit_rate, 0.30))
    if avg_alpha is not None:
        components.append((max(0.0, min(1.0, 0.5 + avg_alpha / 0.10)), 0.20))
    if timing_avg is not None:
        components.append((max(0.0, min(1.0, timing_avg)), 0.15))
    if drawdown_avg is not None:
        components.append((max(0.0, min(1.0, 1.0 - drawdown_avg / 0.20)), 0.10))
    reputation = None
    if components:
        raw = sum(value * weight for value, weight in components) / sum(weight for _, weight in components)
        reputation = raw * confidence

    def group_metrics(key_fn):
        grouped: dict[str, list[TrackedCall]] = {}
        for c in calls:
            grouped.setdefault(key_fn(c), []).append(c)
        result = {}
        for key, rows in grouped.items():
            r = [x.return_pct for x in rows if x.return_pct is not None]
            p = [x.profitable_after_tax for x in rows if x.profitable_after_tax is not None]
            d = [x.directional_correct for x in rows if x.directional_correct is not None]
            result[key] = {
                "sample_size": len(rows),
                "directional_accuracy": _rate(d),
                "profitable_after_tax_rate": _rate(p),
                "average_return_pct": _avg(r),
            }
        return result

    return TraderScore(
        sample_size=n,
        directional_accuracy=acc,
        profitable_after_tax_rate=profit_rate,
        average_return_pct=_avg(returns),
        median_return_pct=median(returns) if returns else None,
        average_alpha_pct=avg_alpha,
        max_drawdown_pct=max(drawdowns) if drawdowns else None,
        average_drawdown_pct=drawdown_avg,
        timing_quality=timing_avg,
        average_holding_seconds=round(mean(holdings)) if holdings else None,
        recent_form_score=recent_form,
        sample_confidence=confidence,
        reputation_score=reputation,
        category_metrics=group_metrics(lambda c: c.category or "unknown"),
        horizon_metrics=group_metrics(lambda c: _bucket_horizon(c.horizon_seconds)),
    )


def detect_crowding(
    *,
    high_quality_signal_count: int,
    total_signal_count: int,
    market_move_since_early_calls_pct: float,
    early_move_max_pct: float = 0.02,
    late_move_min_pct: float = 0.05,
) -> dict:
    if total_signal_count <= 0:
        return {"state": "none", "score": 0.0}
    consensus = high_quality_signal_count / total_signal_count
    move = abs(market_move_since_early_calls_pct)
    if consensus >= 0.6 and move <= early_move_max_pct:
        return {"state": "early_high_quality_consensus", "score": consensus}
    if total_signal_count >= 5 and move >= late_move_min_pct:
        return {"state": "late_crowded_consensus", "score": min(1.0, consensus + move)}
    return {"state": "mixed", "score": consensus * 0.5}
