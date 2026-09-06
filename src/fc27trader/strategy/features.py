from __future__ import annotations

from .models import StrategyMatch


def aggregate_strategy_features(matches: list[StrategyMatch]) -> dict[str, float]:
    if not matches:
        return {
            "strategy_match_count": 0.0,
            "strategy_best_similarity": 0.0,
            "strategy_best_confidence": 0.0,
            "strategy_weighted_success_rate": 0.0,
            "strategy_weighted_median_return": 0.0,
            "strategy_historical_sample_size": 0.0,
            "strategy_decay_risk": 0.0,
        }
    best = max(matches, key=lambda m: m.similarity * m.confidence)
    measured = [m for m in matches if m.historical_sample_size > 0]
    weight_sum = sum(max(1, m.historical_sample_size) * m.confidence for m in measured)
    success = (
        sum((m.historical_success_rate or 0.0) * max(1, m.historical_sample_size) * m.confidence for m in measured) / weight_sum
        if weight_sum else 0.0
    )
    median_return = (
        sum((m.historical_median_net_return or 0.0) * max(1, m.historical_sample_size) * m.confidence for m in measured) / weight_sum
        if weight_sum else 0.0
    )
    decay_values = [m.decay_risk for m in matches if m.decay_risk is not None]
    return {
        "strategy_match_count": float(len(matches)),
        "strategy_best_similarity": float(best.similarity),
        "strategy_best_confidence": float(best.confidence),
        "strategy_weighted_success_rate": float(success),
        "strategy_weighted_median_return": float(median_return),
        "strategy_historical_sample_size": float(sum(m.historical_sample_size for m in measured)),
        "strategy_decay_risk": float(max(decay_values) if decay_values else 0.0),
    }


def strategy_model_signal(features: dict[str, float]) -> dict[str, float]:
    sample = features.get("strategy_historical_sample_size", 0.0)
    if sample <= 0:
        return {"signal": 0.0, "confidence": 0.0}
    sample_conf = min(1.0, sample / 50.0)
    signal = (
        features.get("strategy_weighted_success_rate", 0.0) * 0.55
        + max(-1.0, min(1.0, features.get("strategy_weighted_median_return", 0.0) / 0.10)) * 0.25
        + features.get("strategy_best_similarity", 0.0) * 0.20
    )
    confidence = sample_conf * features.get("strategy_best_confidence", 0.0) * (1.0 - features.get("strategy_decay_risk", 0.0))
    return {"signal": float(signal), "confidence": max(0.0, min(1.0, confidence))}
