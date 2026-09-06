from __future__ import annotations

from dataclasses import dataclass
from statistics import median


@dataclass(frozen=True, slots=True)
class TradeOutcome:
    net_profit: float
    capital: float
    holding_seconds: float
    return_pct: float | None = None
    liquidity_score: float | None = None
    regime: str | None = None
    event_type: str | None = None


@dataclass(frozen=True, slots=True)
class AcquisitionAttempt:
    acquired: bool
    delay_seconds: float | None = None
    execution_quality: float | None = None


def _max_drawdown(profits: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for p in profits:
        equity += p
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return max_dd


def evaluate_strategy(trades: list[TradeOutcome], attempts: list[AcquisitionAttempt]) -> dict:
    if not trades:
        return {
            "status": "insufficient_data",
            "sample_size": 0,
            "acquisition_attempt_sample_size": len(attempts),
            "total_net_transfer_profit": None,
            "hit_rate": None,
            "acquisition_probability": (sum(a.acquired for a in attempts) / len(attempts)) if attempts else None,
            "confidence": 0.0,
        }
    profits = [float(t.net_profit) for t in trades]
    capitals = [max(0.0, float(t.capital)) for t in trades]
    hours = [max(1.0, float(t.holding_seconds)) / 3600.0 for t in trades]
    returns = [t.return_pct if t.return_pct is not None else (t.net_profit / t.capital if t.capital else 0.0) for t in trades]
    total_profit = sum(profits)
    total_capital = sum(capitals)
    total_hours = sum(hours)
    acquisition_probability = (sum(a.acquired for a in attempts) / len(attempts)) if attempts else None
    confidence = min(1.0, len(trades) / 50.0) * 0.75 + (min(1.0, len(attempts) / 100.0) * 0.25 if attempts else 0.0)
    return {
        "status": "measured",
        "sample_size": len(trades),
        "acquisition_attempt_sample_size": len(attempts),
        "total_net_transfer_profit": total_profit,
        "roi": total_profit / total_capital if total_capital else None,
        "profit_per_hour": total_profit / total_hours if total_hours else None,
        "profit_per_deployed_million": total_profit / (total_capital / 1_000_000) if total_capital else None,
        "capital_turnover": total_capital / max(capitals) if capitals and max(capitals) else None,
        "hit_rate": sum(p > 0 for p in profits) / len(profits),
        "max_drawdown": _max_drawdown(profits),
        "acquisition_probability": acquisition_probability,
        "profitable_exit_probability": sum(p > 0 for p in profits) / len(profits),
        "median_return_pct": median(returns),
        "median_holding_seconds": median([t.holding_seconds for t in trades]),
        "liquidity_score": median([t.liquidity_score for t in trades if t.liquidity_score is not None]) if any(t.liquidity_score is not None for t in trades) else None,
        "confidence": min(1.0, confidence),
    }
