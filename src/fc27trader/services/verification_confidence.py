from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from math import exp, log
from pathlib import Path

import yaml


@dataclass(frozen=True, slots=True)
class VerificationConfidence:
    value: float
    age_seconds: float
    base_confidence: float
    reasons: list[str]


def _load_config(path: str | Path = "config/manual_verification.yaml") -> dict:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def calculate_manual_observation_confidence(
    *,
    observed_at: datetime,
    received_at: datetime | None = None,
    listing_prices: list[int] | None = None,
    lowest_bin: int | None = None,
    screenshot_present: bool = False,
    approximate: bool = False,
    config: dict | None = None,
) -> VerificationConfidence:
    cfg = config or _load_config()
    conf = cfg["confidence"]
    now = received_at or datetime.now(UTC)
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=UTC)
    age = max(0.0, (now - observed_at).total_seconds())

    prices = sorted(int(x) for x in (listing_prices or []) if int(x) > 0)
    reasons: list[str] = []
    if approximate:
        base = float(conf["manual_approximate"])
        reasons.append("approximate_manual_value")
    elif screenshot_present and len(prices) >= 5:
        base = float(conf["screenshot_with_5_plus_exact"])
        reasons.append("screenshot_plus_5_or_more_exact_listings")
    elif len(prices) >= 5:
        base = float(conf["manual_5_plus_exact"])
        reasons.append("5_or_more_exact_listings")
    elif len(prices) >= 3:
        base = float(conf["manual_3_4_exact"])
        reasons.append("3_to_4_exact_listings")
    elif len(prices) == 2:
        base = float(conf["manual_2_exact"])
        reasons.append("2_exact_listings")
    elif len(prices) == 1 or lowest_bin is not None:
        base = float(conf["manual_1_exact"])
        reasons.append("single_exact_listing")
    elif screenshot_present:
        base = float(conf["screenshot_only"])
        reasons.append("screenshot_without_numeric_listing_sample")
    else:
        base = float(conf["minimum"])
        reasons.append("insufficient_observation_detail")

    if prices and lowest_bin is not None and min(prices) != lowest_bin:
        base *= float(conf["inconsistency_multiplier"])
        reasons.append("lowest_bin_inconsistent_with_listing_sample")

    half_life = max(1.0, float(conf["age_half_life_seconds"]))
    decay = exp(-log(2.0) * age / half_life)
    value = max(float(conf["minimum"]), min(1.0, base * decay))
    if age > 0:
        reasons.append("confidence_decayed_with_observation_age")

    return VerificationConfidence(
        value=value,
        age_seconds=age,
        base_confidence=base,
        reasons=reasons,
    )
