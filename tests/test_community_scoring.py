from datetime import UTC, datetime, timedelta

from fc27trader.community.scoring import TrackedCall, detect_crowding, score_trader


def test_trader_score_uses_performance_not_followers():
    now = datetime(2026, 9, 4, tzinfo=UTC)
    calls = [
        TrackedCall(now - timedelta(days=i), "fodder", 86400, True, True, 0.04, 0.01, 0.01, 0.9, 20000)
        for i in range(10)
    ]
    score = score_trader(calls, now=now)
    assert score.sample_size == 10
    assert score.directional_accuracy == 1.0
    assert score.profitable_after_tax_rate == 1.0
    assert score.reputation_score is not None and score.reputation_score > 0.4


def test_crowding_distinguishes_early_and_late_consensus():
    early = detect_crowding(high_quality_signal_count=4, total_signal_count=5, market_move_since_early_calls_pct=0.01)
    late = detect_crowding(high_quality_signal_count=4, total_signal_count=6, market_move_since_early_calls_pct=0.07)
    assert early["state"] == "early_high_quality_consensus"
    assert late["state"] == "late_crowded_consensus"
