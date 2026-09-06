from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AllocationCandidate:
    key: str
    expected_net_profit: float
    expected_profit_per_hour: float
    capital_per_unit: int
    max_quantity: int
    liquidity_score: float
    downside_risk: float
    confidence: float
    strategy_support: float = 0.0
    strategy_decay_risk: float = 0.0


@dataclass(frozen=True, slots=True)
class Allocation:
    key: str
    quantity: int
    capital: int
    expected_net_profit: float
    score: float


def allocate_capital(candidates: list[AllocationCandidate], available_coins: int, *, max_risk_weighted_fraction: float = 0.45) -> list[Allocation]:
    """Greedy baseline allocator optimized for scalable profit/turnover, not raw ROI."""
    ranked=[]
    for c in candidates:
        if c.capital_per_unit<=0 or c.max_quantity<=0 or c.expected_net_profit<=0:
            continue
        scalability=min(1.0,(c.capital_per_unit*c.max_quantity)/max(1,available_coins))
        score=(c.expected_profit_per_hour/100000)*0.45 + (c.expected_net_profit/100000)*0.30 + c.liquidity_score*0.15 + scalability*0.10
        score += max(0.0, min(1.0, c.strategy_support)) * 0.05
        score *= 1.0 - max(0.0, min(1.0, c.strategy_decay_risk)) * 0.08
        score*=max(0.0,c.confidence)*(1-max(0.0,min(1.0,c.downside_risk)))
        ranked.append((score,c))
    ranked.sort(key=lambda x:x[0],reverse=True)
    remaining=available_coins; result=[]
    for score,c in ranked:
        risk_cap=int(available_coins*max_risk_weighted_fraction/max(0.25,c.downside_risk+0.25))
        max_cap=min(remaining,risk_cap,c.capital_per_unit*c.max_quantity)
        qty=max_cap//c.capital_per_unit
        if qty<=0: continue
        capital=qty*c.capital_per_unit
        unit_profit=c.expected_net_profit/max(1,c.max_quantity)
        result.append(Allocation(c.key,qty,capital,unit_profit*qty,score))
        remaining-=capital
        if remaining<c.capital_per_unit: continue
    return result
