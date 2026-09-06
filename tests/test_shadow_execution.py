from datetime import UTC, datetime, timedelta

from fc27trader.shadow.execution import simulate_buy_fill, simulate_sell_fill


def test_buy_rejects_lookahead_violation():
    decision = datetime.now(UTC)
    fill = simulate_buy_fill(
        decision_at=decision,
        snapshot_at=decision,
        observed_buy_price=10_000,
        max_buy_price=10_500,
        requested_quantity=4,
        active_listings=10,
    )
    assert not fill.filled
    assert fill.reason == "snapshot_not_after_decision"


def test_buy_applies_slippage_and_limit():
    decision = datetime.now(UTC)
    fill = simulate_buy_fill(
        decision_at=decision,
        snapshot_at=decision + timedelta(minutes=2),
        observed_buy_price=10_000,
        max_buy_price=10_250,
        requested_quantity=4,
        active_listings=10,
    )
    assert fill.filled
    assert fill.price == 10_250


def test_sell_applies_tax_and_requires_later_snapshot():
    decision = datetime.now(UTC)
    fill = simulate_sell_fill(
        decision_at=decision,
        snapshot_at=decision + timedelta(minutes=2),
        listed_price=20_000,
        observed_market_price=20_500,
        quantity=2,
        confirmed_twice=True,
    )
    assert fill.filled
    assert fill.price == 20_000
    assert fill.ea_tax == 2_000


def test_sell_rejects_lookahead_violation():
    decision = datetime.now(UTC)
    fill = simulate_sell_fill(
        decision_at=decision,
        snapshot_at=decision,
        listed_price=20_000,
        observed_market_price=21_000,
        quantity=1,
        confirmed_twice=True,
    )
    assert not fill.filled
    assert fill.reason == "snapshot_not_after_decision"


def test_reference_only_acquisition_uses_probability_not_reference_as_fill():
    from fc27trader.shadow.execution import simulate_acquisition_attempt
    decision = datetime.now(UTC)
    miss = simulate_acquisition_attempt(
        decision_at=decision, max_buy_price=96_000, requested_quantity=3,
        expected_acquisition_price=95_000, acquisition_probability=0.4,
        expected_acquisition_delay_seconds=180, expected_available_quantity=2,
        random_draw=0.8, reference_uncertainty_pct=0.1,
    )
    assert not miss.filled
    hit = simulate_acquisition_attempt(
        decision_at=decision, max_buy_price=96_000, requested_quantity=3,
        expected_acquisition_price=95_000, acquisition_probability=0.9,
        expected_acquisition_delay_seconds=180, expected_available_quantity=2,
        random_draw=0.2, reference_uncertainty_pct=0.1,
    )
    assert hit.filled
    assert hit.fill_at > decision
    assert hit.quantity == 2
