from __future__ import annotations

from datetime import UTC, datetime


def reference_quality(provider_key: str, provider_timestamp: datetime | None, observed_at: datetime) -> tuple[float, float, float | None]:
    """Phase-1 uncertainty prior for non-executable provider reference prices.

    Values are deliberately conservative and tagged as heuristic in observation metadata.
    They are calibration inputs, not claims about provider accuracy.
    Returns (uncertainty_pct, confidence, age_seconds).
    """
    base_uncertainty = {
        "futdb": 0.08,
        "thecoinprinter": 0.07,
    }.get(provider_key, 0.12)
    if provider_timestamp is None:
        return min(0.35, base_uncertainty + 0.08), max(0.20, 1.0 - (base_uncertainty + 0.18)), None
    if provider_timestamp.tzinfo is None:
        provider_timestamp = provider_timestamp.replace(tzinfo=UTC)
    age_seconds = max(0.0, (observed_at - provider_timestamp).total_seconds())
    age_hours = age_seconds / 3600.0
    # Slow reference sources remain useful anchors, but uncertainty rises with age.
    age_penalty = min(0.25, age_hours * 0.015)
    uncertainty = min(0.40, base_uncertainty + age_penalty)
    confidence = max(0.10, min(0.95, 1.0 - uncertainty - min(0.20, age_hours * 0.01)))
    return uncertainty, confidence, age_seconds
