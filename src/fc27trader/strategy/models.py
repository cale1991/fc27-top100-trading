from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class StrategyDefinition:
    slug: str
    name: str
    aliases: tuple[str, ...] = ()
    explanation: str = ""
    mechanism: str = ""
    card_categories: tuple[str, ...] = ()
    market_regimes: tuple[str, ...] = ()
    catalysts: tuple[str, ...] = ()
    rule: dict = field(default_factory=dict)
    ea_tax_sensitivity: str | None = None
    ea_intervention_risk: str | None = None


@dataclass(frozen=True, slots=True)
class StrategyContext:
    card_id: str
    observed_at: datetime
    card_category: str | None = None
    market_regime: str | None = None
    catalysts: tuple[str, ...] = ()
    in_packs: bool | None = None
    promo_active: bool | None = None
    price_change_1h: float | None = None
    price_change_24h: float | None = None
    liquidity_score: float | None = None
    demand_score: float | None = None
    seconds_to_content: float | None = None
    seconds_since_content: float | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StrategyMatch:
    slug: str
    name: str
    similarity: float
    confidence: float
    reasons: tuple[str, ...]
    current_conditions_differ: bool = False
    structural_difference_score: float | None = None
    historical_sample_size: int = 0
    historical_success_rate: float | None = None
    historical_median_net_return: float | None = None
    expected_holding_seconds: int | None = None
    decay_risk: float | None = None
    failure_conditions: tuple[str, ...] = ()
