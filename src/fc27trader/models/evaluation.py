from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TradingEvaluation:
    total_transfer_profit: float
    profit_per_day: float
    profit_per_deployed_million: float
    max_drawdown: float
    win_rate: float
    capital_turnover: float
    time_to_sale_mae_seconds: float
    calibration_error: float


def dominates(candidate: TradingEvaluation, incumbent: TradingEvaluation) -> bool:
    """Conservative retention gate: profit first, then turnover/drawdown as tie-breakers."""
    if candidate.total_transfer_profit <= incumbent.total_transfer_profit:
        return False
    if candidate.max_drawdown > incumbent.max_drawdown * 1.25:
        return False
    return candidate.capital_turnover >= incumbent.capital_turnover * 0.90
