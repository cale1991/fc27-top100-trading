from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RegimeInputs:
    market_return_1h: float
    market_return_6h: float
    listing_supply_change_1h: float | None = None
    volume_change_1h: float | None = None
    content_shock_score: float = 0.0
    reward_window: bool = False


@dataclass(frozen=True, slots=True)
class RegimeEstimate:
    regime: str
    confidence: float
    reasons: list[str]


def detect_regime(x: RegimeInputs) -> RegimeEstimate:
    reasons: list[str] = []
    supply = x.listing_supply_change_1h or 0.0
    volume = x.volume_change_1h or 0.0
    if x.content_shock_score >= 0.7:
        reasons.append("major_content_shock")
        return RegimeEstimate("content_shock", min(1.0, x.content_shock_score), reasons)
    if x.reward_window and supply >= 0.12:
        reasons += ["reward_window", "supply_expansion"]
        return RegimeEstimate("supply_flood", min(1.0, 0.6 + supply), reasons)
    if x.market_return_1h <= -0.05 and volume >= 0.20:
        reasons += ["rapid_market_drop", "elevated_volume"]
        return RegimeEstimate("panic", min(1.0, 0.65 + abs(x.market_return_1h)), reasons)
    if x.market_return_1h >= 0.03 and x.market_return_6h > 0:
        reasons.append("broad_recovery_or_rally")
        return RegimeEstimate("recovery", min(1.0, 0.55 + x.market_return_1h), reasons)
    if abs(x.market_return_1h) < 0.01 and abs(x.market_return_6h) < 0.02 and abs(supply) < 0.05:
        reasons.append("low_broad_market_movement")
        return RegimeEstimate("quiet", 0.7, reasons)
    return RegimeEstimate("normal", 0.5, ["no_dominant_regime_signal"])
