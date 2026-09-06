from __future__ import annotations

from collections.abc import Iterable

from .models import OpportunityInputs, RankedOpportunity


DEFAULT_WEIGHTS = {
    "expected_net_profit": 1.35,
    "acquisition_probability": 0.80,
    "expected_discount_to_reference": 0.45,
    "profitable_exit_probability": 0.95,
    "liquidity_score": 0.85,
    "sell_through_rate": 0.65,
    "expected_profit_per_hour": 1.20,
    "position_capacity_coins": 0.85,
    "catalyst_score": 0.45,
    "community_intelligence_score": 0.20,
    "historical_analogue_score": 0.25,
    "strategy_best_similarity": 0.08,
    "strategy_best_confidence": 0.06,
    "strategy_weighted_success_rate": 0.10,
    "strategy_weighted_median_return": 0.06,
    "strategy_decay_risk": -0.15,
    "volatility": -0.35,
    "downside_risk": -0.90,
    "ea_intervention_risk": -0.70,
    "opportunity_cost": -0.80,
    "reference_uncertainty_pct": -0.45,
}


def _bounded(value: float | None, *, scale: float = 1.0) -> float:
    if value is None:
        return 0.0
    if scale <= 0:
        return float(value)
    x = float(value) / scale
    return max(-1.0, min(1.0, x))


def score_opportunity(item: OpportunityInputs, weights: dict[str, float] | None = None) -> tuple[float, dict[str, float]]:
    """Rank opportunity quality without assuming a fixed card universe.

    Monetary terms are compressed to prevent one huge but illiquid card from
    dominating solely because of nominal coin size. No fixed acquisition
    discount is encoded here; discount probability comes from the acquisition model.
    """
    w = weights or DEFAULT_WEIGHTS
    raw = {
        "expected_net_profit": _bounded(item.expected_net_profit, scale=100_000),
        "acquisition_probability": _bounded(item.acquisition_probability),
        "expected_discount_to_reference": _bounded(item.expected_discount_to_reference, scale=0.10),
        "profitable_exit_probability": _bounded(item.profitable_exit_probability),
        "liquidity_score": _bounded(item.liquidity_score),
        "sell_through_rate": _bounded(item.sell_through_rate),
        "expected_profit_per_hour": _bounded(item.expected_profit_per_hour, scale=100_000),
        "position_capacity_coins": _bounded(item.position_capacity_coins, scale=2_000_000),
        "catalyst_score": _bounded(item.catalyst_score),
        "community_intelligence_score": _bounded(item.community_intelligence_score),
        "historical_analogue_score": _bounded(item.historical_analogue_score),
        "strategy_best_similarity": _bounded(item.strategy_best_similarity),
        "strategy_best_confidence": _bounded(item.strategy_best_confidence),
        "strategy_weighted_success_rate": _bounded(item.strategy_weighted_success_rate),
        "strategy_weighted_median_return": _bounded(item.strategy_weighted_median_return, scale=0.10),
        "strategy_decay_risk": _bounded(item.strategy_decay_risk),
        "volatility": _bounded(item.volatility, scale=0.15),
        "downside_risk": _bounded(item.downside_risk, scale=0.20),
        "ea_intervention_risk": _bounded(item.ea_intervention_risk),
        "opportunity_cost": _bounded(item.opportunity_cost, scale=100_000),
        "reference_uncertainty_pct": _bounded(item.reference_uncertainty_pct, scale=0.10),
    }
    components = {name: raw[name] * w.get(name, 0.0) for name in raw}
    return sum(components.values()), components


def discover_and_rank(
    market: Iterable[OpportunityInputs],
    *,
    minimum_score: float = 0.35,
    max_candidates: int = 100,
    execution_confidence_threshold: float = 0.80,
    weights: dict[str, float] | None = None,
) -> list[RankedOpportunity]:
    scored: list[tuple[OpportunityInputs, float, dict[str, float]]] = []
    for item in market:
        # Basic viability only. The production universe is whatever is observable,
        # not a permanent allow-list/watchlist.
        if item.reference_price is None or item.reference_price <= 0:
            continue
        if item.metadata.get("production_evidence_sufficient") is False:
            continue
        score, components = score_opportunity(item, weights)
        if score >= minimum_score:
            scored.append((item, score, components))

    scored.sort(key=lambda row: row[1], reverse=True)
    ranked: list[RankedOpportunity] = []
    for rank, (item, score, components) in enumerate(scored[:max_candidates], start=1):
        uncertainty = item.reference_uncertainty_pct
        confidence = 1.0 if uncertainty is None else max(0.0, 1.0 - uncertainty)
        ranked.append(
            RankedOpportunity(
                card_id=item.card_id,
                score=score,
                rank=rank,
                components=components,
                requires_execution_verification=confidence < execution_confidence_threshold,
                observed_at=item.observed_at,
            )
        )
    return ranked
