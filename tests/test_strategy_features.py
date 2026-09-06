from fc27trader.strategy.decay import cycle_weight, strategy_decay_score
from fc27trader.strategy.features import aggregate_strategy_features, strategy_model_signal
from fc27trader.strategy.models import StrategyMatch
from fc27trader.strategy.risk import strategy_risk_adjustment


def test_cycle_weights_prioritize_fc26():
    assert cycle_weight('FC26') > cycle_weight('FC25') > cycle_weight('FC24') > cycle_weight('FIFA23') > cycle_weight('FIFA22')


def test_older_cycle_has_more_decay_all_else_equal():
    assert strategy_decay_score(historical_cycle='FIFA22') > strategy_decay_score(historical_cycle='FC26')


def test_no_matches_produces_zero_features():
    x=aggregate_strategy_features([])
    assert x['strategy_match_count']==0 and x['strategy_historical_sample_size']==0


def test_unmeasured_match_has_zero_model_confidence():
    m=StrategyMatch(slug='x',name='X',similarity=.9,confidence=.8,reasons=())
    assert strategy_model_signal(aggregate_strategy_features([m]))['confidence']==0


def test_measured_match_can_contribute_signal():
    m=StrategyMatch(slug='x',name='X',similarity=.9,confidence=.8,reasons=(),historical_sample_size=50,historical_success_rate=.7,historical_median_net_return=.05,decay_risk=.1)
    x=strategy_model_signal(aggregate_strategy_features([m]))
    assert x['signal']>0 and x['confidence']>0


def test_decay_penalizes_strategy_risk_adjustment():
    assert strategy_risk_adjustment(support=.8,decay_risk=.8) < strategy_risk_adjustment(support=.8,decay_risk=.1)
