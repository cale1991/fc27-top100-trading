from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ShadowRules:
    tax_rate: float = 0.05
    buy_slippage_ticks: int = 1
    sell_slippage_ticks: int = 1
    undercut_ticks: int = 1
    require_two_sell_confirmations: bool = True
    default_fill_fraction_when_depth_unknown: float = 0.25


def price_tick(price: int) -> int:
    if price <= 1_000:
        return 50
    if price <= 10_000:
        return 100
    if price <= 50_000:
        return 250
    if price <= 100_000:
        return 500
    return 1_000


def snap_down(price: int) -> int:
    tick = price_tick(price)
    return (price // tick) * tick


def snap_up(price: int) -> int:
    tick = price_tick(price)
    return ((price + tick - 1) // tick) * tick
