from fc27trader.strategy.backtest import AcquisitionAttempt, TradeOutcome, evaluate_strategy


def test_empty_trade_sample_is_not_fabricated():
    x=evaluate_strategy([],[])
    assert x['status']=='insufficient_data' and x['total_net_transfer_profit'] is None and x['confidence']==0


def test_acquisition_probability_counts_misses():
    x=evaluate_strategy([], [AcquisitionAttempt(True), AcquisitionAttempt(False), AcquisitionAttempt(False)])
    assert abs(x['acquisition_probability'] - 1/3) < 1e-9


def test_profit_metrics_are_measured_from_all_trades():
    trades=[TradeOutcome(1000,10000,3600),TradeOutcome(-500,10000,3600)]
    x=evaluate_strategy(trades,[])
    assert x['total_net_transfer_profit']==500
    assert x['hit_rate']==.5
    assert abs(x['roi']-.025)<1e-9


def test_drawdown_retains_losses():
    trades=[TradeOutcome(1000,10000,3600),TradeOutcome(-1500,10000,3600),TradeOutcome(500,10000,3600)]
    assert evaluate_strategy(trades,[])['max_drawdown']==1500
