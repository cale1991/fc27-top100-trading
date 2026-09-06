from __future__ import annotations

CYCLE_WEIGHTS = {
    "FC26": 1.00,
    "FC25": 0.72,
    "FC24": 0.52,
    "FIFA23": 0.36,
    "FIFA22": 0.25,
}


def cycle_weight(game_cycle: str) -> float:
    return CYCLE_WEIGHTS.get(str(game_cycle).upper(), 0.15)


def strategy_decay_score(
    *,
    historical_cycle: str,
    structural_difference_score: float | None = None,
    measured_deterioration: float | None = None,
) -> float:
    age_decay = 1.0 - cycle_weight(historical_cycle)
    structural = max(0.0, min(1.0, structural_difference_score or 0.0))
    measured = max(0.0, min(1.0, measured_deterioration or 0.0))
    return max(0.0, min(1.0, age_decay * 0.45 + structural * 0.35 + measured * 0.55))
