from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class OpportunityInputs:
    card_id: str
    observed_at: datetime
    reference_price: int | None
    reference_age_seconds: float | None
    reference_uncertainty_pct: float | None
    expected_net_profit: float | None
    acquisition_probability: float | None
    expected_discount_to_reference: float | None
    profitable_exit_probability: float | None
    liquidity_score: float | None
    sell_through_rate: float | None
    expected_holding_seconds: float | None
    expected_profit_per_hour: float | None
    position_capacity_coins: float | None
    volatility: float | None
    downside_risk: float | None
    ea_tax: float | None
    catalyst_score: float | None
    ea_intervention_risk: float | None
    opportunity_cost: float | None
    community_intelligence_score: float | None = None
    historical_analogue_score: float | None = None
    strategy_match_count: float = 0.0
    strategy_best_similarity: float = 0.0
    strategy_best_confidence: float = 0.0
    strategy_weighted_success_rate: float = 0.0
    strategy_weighted_median_return: float = 0.0
    strategy_historical_sample_size: float = 0.0
    strategy_decay_risk: float = 0.0
    active_position: bool = False
    rapid_movement_score: float | None = None
    unusual_volume_score: float | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RankedOpportunity:
    card_id: str
    score: float
    rank: int
    components: dict[str, float]
    requires_execution_verification: bool
    observed_at: datetime
