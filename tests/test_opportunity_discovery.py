from datetime import UTC, datetime

from fc27trader.opportunity.models import OpportunityInputs
from fc27trader.opportunity.scoring import discover_and_rank
from fc27trader.services.attention import allocate_attention


def item(card, profit, pph, active=False):
    return OpportunityInputs(
        card_id=card, observed_at=datetime.now(UTC), reference_price=100_000,
        reference_age_seconds=600, reference_uncertainty_pct=0.03,
        expected_net_profit=profit, acquisition_probability=0.7,
        expected_discount_to_reference=0.05, profitable_exit_probability=0.85,
        liquidity_score=0.8, sell_through_rate=0.7, expected_holding_seconds=1800,
        expected_profit_per_hour=pph, position_capacity_coins=1_000_000,
        volatility=0.03, downside_risk=0.04, ea_tax=5000, catalyst_score=0.6,
        ea_intervention_risk=0.2, opportunity_cost=5000, active_position=active,
    )


def test_dynamic_universe_ranks_quality_not_fixed_watchlist():
    market = [item("a", 40000, 80000), item("b", 5000, 4000), item("c", 70000, 120000)]
    ranked = discover_and_rank(market, minimum_score=0.2)
    assert ranked[0].card_id == "c"
    assert {r.card_id for r in ranked}.issubset({"a", "b", "c"})


def test_attention_promotes_active_positions():
    a = item("a", 40000, 80000, active=True)
    ranked = discover_and_rank([a], minimum_score=0.2)
    decisions = allocate_attention(ranked, {"a": a})
    assert decisions[0].target_interval_seconds == 120
