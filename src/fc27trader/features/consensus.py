from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from math import floor
from statistics import median

from sqlalchemy.orm import Session

from fc27trader.db.models import DerivedFeatureSnapshot, Source
from fc27trader.features.point_in_time import execution_observations_known_at, reference_observations_known_at

ALGORITHM_VERSION = "market-consensus-v1"


def _weighted_median(pairs: list[tuple[float, float]]) -> float | None:
    if not pairs:
        return None
    rows = sorted(pairs)
    total = sum(w for _, w in rows)
    cumulative = 0.0
    for value, weight in rows:
        cumulative += weight
        if cumulative >= total / 2:
            return value
    return rows[-1][0]


def _quartile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    v = sorted(values)
    pos = (len(v) - 1) * q
    lo = floor(pos); hi = min(lo + 1, len(v)-1)
    frac = pos - lo
    return v[lo] * (1-frac) + v[hi] * frac


def calculate_market_consensus(session: Session, *, card_id, market_segment_id, cutoff: datetime, fresh_seconds: int = 300, max_age_seconds: int = 86400) -> dict:
    refs = reference_observations_known_at(session, card_id=card_id, market_segment_id=market_segment_id, cutoff=cutoff)
    # One latest known row per provider avoids a high-frequency source dominating the median.
    latest_by_source = {}
    for row in refs:
        if row.source_id not in latest_by_source:
            latest_by_source[row.source_id] = row
    usable = []
    for row in latest_by_source.values():
        known = row.provider_timestamp or row.observed_at
        age = max(0.0, (cutoff - known).total_seconds())
        if age <= max_age_seconds:
            usable.append((row, age))
    prices = [float(r.price) for r, _ in usable]
    if not prices:
        return {"provider_count": 0, "fresh_provider_count": 0, "median_reference_price": None, "source_observation_ids": []}
    med = float(median(prices))
    weights = []
    for row, age in usable:
        conf = float(row.confidence) if row.confidence is not None else 0.5
        age_weight = max(0.05, 1.0 - min(age / max_age_seconds, 0.95))
        weights.append((float(row.price), max(0.01, conf * age_weight)))
    within1 = sum(abs(p-med)/med <= .01 for p in prices) if med else 0
    within2 = sum(abs(p-med)/med <= .02 for p in prices) if med else 0
    minp, maxp = min(prices), max(prices)
    q1 = _quartile(prices, .25); q3 = _quartile(prices, .75)
    ages = [age for _, age in usable]
    freshest = min(usable, key=lambda x:x[1])[0]
    oldest = max(usable, key=lambda x:x[1])[0]
    executions = execution_observations_known_at(session, card_id=card_id, market_segment_id=market_segment_id, cutoff=cutoff, limit=1)
    exec_price = executions[0].lowest_bin if executions else None
    return {
        "provider_count": len(usable),
        "fresh_provider_count": sum(age <= fresh_seconds for _, age in usable),
        "median_reference_price": med,
        "weighted_median_reference_price": _weighted_median(weights),
        "min_reference": minp,
        "max_reference": maxp,
        "spread_absolute": maxp-minp,
        "spread_pct": (maxp-minp)/med if med else None,
        "interquartile_range": (q3-q1) if q1 is not None and q3 is not None else None,
        "average_age": sum(ages)/len(ages),
        "freshest_provider": session.get(Source, freshest.source_id).key if session.get(Source, freshest.source_id) else None,
        "oldest_provider": session.get(Source, oldest.source_id).key if session.get(Source, oldest.source_id) else None,
        "number_within_1pct": within1,
        "number_within_2pct": within2,
        "disagreement_score": ((maxp-minp)/med if med else 0.0) * (1.0 - within2/len(prices)),
        "stale_source_ratio": sum(age > fresh_seconds for _, age in usable)/len(usable),
        "observation_density": len(usable),
        "platform_certainty": 1.0,
        "reference_execution_divergence": ((exec_price-med)/med if exec_price is not None and med else None),
        "source_observation_ids": [f"reference:{r.id}" for r,_ in usable] + ([f"execution:{executions[0].id}"] if executions else []),
    }


def persist_market_consensus(session: Session, *, card_id, market_segment_id, game_year: int, cutoff: datetime) -> DerivedFeatureSnapshot:
    value = calculate_market_consensus(session, card_id=card_id, market_segment_id=market_segment_id, cutoff=cutoff)
    row = DerivedFeatureSnapshot(
        feature_family="market_consensus", feature_key="reference_consensus", algorithm_version=ALGORITHM_VERSION,
        game_year=game_year, market_segment_id=market_segment_id, card_id=card_id, input_cutoff_at=cutoff,
        calculated_at=datetime.now(UTC), value_json={k:v for k,v in value.items() if k != "source_observation_ids"},
        source_observation_ids_json=value.get("source_observation_ids", []), metadata_json={},
    )
    session.add(row); session.flush(); return row
