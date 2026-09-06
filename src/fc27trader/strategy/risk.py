from __future__ import annotations


def strategy_risk_adjustment(*, support: float, decay_risk: float, current_difference: float = 0.0) -> float:
    """Small additive risk modifier; current market evidence remains primary."""
    support = max(0.0, min(1.0, support))
    decay = max(0.0, min(1.0, decay_risk))
    difference = max(0.0, min(1.0, current_difference))
    return max(-0.25, min(0.15, support * 0.12 - decay * 0.18 - difference * 0.10))
