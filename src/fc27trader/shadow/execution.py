from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import math

from .rules import ShadowRules, price_tick, snap_down, snap_up


@dataclass(frozen=True, slots=True)
class FillResult:
    filled: bool
    quantity: int
    price: int | None
    ea_tax: int
    reason: str


@dataclass(frozen=True, slots=True)
class AcquisitionAttemptResult:
    filled: bool
    quantity: int
    price: int | None
    fill_at: datetime | None
    effective_acquisition_probability: float
    signal_quality: float
    execution_quality: float
    reason: str


def simulate_buy_fill(
    *,
    decision_at: datetime,
    snapshot_at: datetime,
    observed_buy_price: int | None,
    max_buy_price: int,
    requested_quantity: int,
    active_listings: int | None,
    rules: ShadowRules = ShadowRules(),
) -> FillResult:
    """Execution-observation fill path.

    This is used only when a post-decision executable listing/market observation
    exists. A third-party reference price must not be passed here as if it were
    an achievable listing.
    """
    if snapshot_at <= decision_at:
        return FillResult(False, 0, None, 0, "snapshot_not_after_decision")
    if observed_buy_price is None:
        return FillResult(False, 0, None, 0, "no_achievable_buy_price")

    tick = price_tick(observed_buy_price)
    conservative_price = snap_up(observed_buy_price + rules.buy_slippage_ticks * tick)
    if conservative_price > max_buy_price:
        return FillResult(False, 0, None, 0, "price_above_limit_after_slippage")

    if active_listings is None:
        quantity = max(1, math.floor(requested_quantity * rules.default_fill_fraction_when_depth_unknown))
    else:
        quantity = min(requested_quantity, max(0, active_listings))
    if quantity <= 0:
        return FillResult(False, 0, None, 0, "no_depth")
    return FillResult(True, quantity, conservative_price, 0, "filled_from_execution_observation")


def simulate_acquisition_attempt(
    *,
    decision_at: datetime,
    max_buy_price: int,
    requested_quantity: int,
    expected_acquisition_price: int | None,
    acquisition_probability: float,
    expected_acquisition_delay_seconds: int | None,
    expected_available_quantity: float | None,
    random_draw: float,
    reference_uncertainty_pct: float | None = None,
    signal_quality: float = 0.5,
    rules: ShadowRules = ShadowRules(),
) -> AcquisitionAttemptResult:
    """Shadow a search for an undercut when no executable quote exists.

    The reference quote only informs the learned acquisition model upstream.
    We fill from the model's expected acquisition distribution, not at the
    reference BIN itself. Stale/reference uncertainty reduces execution quality
    and therefore the effective fill probability.
    """
    if expected_acquisition_price is None:
        return AcquisitionAttemptResult(False, 0, None, None, 0.0, signal_quality, 0.0, "no_acquisition_price_model")
    if not 0.0 <= random_draw <= 1.0:
        raise ValueError("random_draw must be in [0, 1]")

    uncertainty = min(1.0, max(0.0, reference_uncertainty_pct or 0.0))
    base_probability = min(1.0, max(0.0, acquisition_probability))
    effective_probability = base_probability * (1.0 - uncertainty)
    execution_quality = max(0.0, 1.0 - uncertainty)

    if random_draw > effective_probability:
        return AcquisitionAttemptResult(
            False, 0, None, None, effective_probability, signal_quality, execution_quality,
            "undercut_not_observed_within_modeled_search_window",
        )

    tick = price_tick(expected_acquisition_price)
    fill_price = snap_up(expected_acquisition_price + rules.buy_slippage_ticks * tick)
    if fill_price > max_buy_price:
        return AcquisitionAttemptResult(
            False, 0, None, None, effective_probability, signal_quality, execution_quality,
            "modeled_acquisition_above_limit_after_slippage",
        )

    expected_qty = expected_available_quantity if expected_available_quantity is not None else 1.0
    quantity = min(requested_quantity, max(1, math.floor(expected_qty)))
    delay = max(1, expected_acquisition_delay_seconds or 1)
    return AcquisitionAttemptResult(
        True,
        quantity,
        fill_price,
        decision_at + timedelta(seconds=delay),
        effective_probability,
        signal_quality,
        execution_quality,
        "filled_from_learned_acquisition_distribution",
    )


def simulate_sell_fill(
    *,
    decision_at: datetime,
    snapshot_at: datetime,
    listed_price: int,
    observed_market_price: int | None,
    quantity: int,
    confirmed_twice: bool,
    rules: ShadowRules = ShadowRules(),
) -> FillResult:
    if snapshot_at <= decision_at:
        return FillResult(False, 0, None, 0, "snapshot_not_after_decision")
    if observed_market_price is None:
        return FillResult(False, 0, None, 0, "no_market_price")
    if rules.require_two_sell_confirmations and not confirmed_twice:
        return FillResult(False, 0, None, 0, "awaiting_second_confirmation")

    tick = price_tick(observed_market_price)
    conservative_market_ceiling = snap_down(
        observed_market_price - (rules.undercut_ticks + rules.sell_slippage_ticks) * tick
    )
    if listed_price > conservative_market_ceiling:
        return FillResult(False, 0, None, 0, "listing_not_competitive_after_slippage")

    tax = math.floor(listed_price * quantity * rules.tax_rate)
    return FillResult(True, quantity, listed_price, tax, "filled")
