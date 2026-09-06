from fc27trader.models.ea_intervention import EAInterventionInputs, estimate_ea_intervention_risk
from fc27trader.models.ensemble import ModelSignal, combine_signals
from fc27trader.models.liquidity import LiquidityObservation, estimate_liquidity
from fc27trader.models.portfolio import AllocationCandidate, allocate_capital
from fc27trader.models.regime import RegimeInputs, detect_regime


def test_liquidity_baseline():
    est = estimate_liquidity([LiquidityObservation(900), LiquidityObservation(5400), LiquidityObservation(20000)])
    assert est.sample_size == 3
    assert est.probability_sale_within_1h == 1 / 3


def test_regime_and_ea_risk_baselines():
    assert detect_regime(RegimeInputs(-0.06, -0.08, volume_change_1h=0.3)).regime == "panic"
    risk = estimate_ea_intervention_risk(EAInterventionInputs(store_pack_supply_score=0.9, substitute_release_score=0.8))
    assert risk.net_risk > 0.3


def test_portfolio_and_ensemble_baselines():
    alloc = allocate_capital([AllocationCandidate("a", 30000, 12000, 100000, 4, 0.9, 0.1, 0.9)], 500000)
    assert alloc and alloc[0].quantity > 0
    ens = combine_signals([ModelSignal("a", 10000, 0.8, 0.9), ModelSignal("b", 8000, 0.7, 0.8)])
    assert ens.models_used == 2 and ens.predicted_net_profit and ens.predicted_net_profit > 8000
