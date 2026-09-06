from __future__ import annotations

from datetime import UTC, datetime
from math import sqrt

from sqlalchemy.orm import Session

from fc27trader.db.models import DerivedFeatureSnapshot
from fc27trader.features.consensus import calculate_market_consensus

ALGORITHM_VERSION = "cross-market-v1"


def calculate_cross_market_features(session: Session, *, card_id, game_year: int, segments: dict[str, object], cutoff: datetime) -> dict:
    values = {key: calculate_market_consensus(session, card_id=card_id, market_segment_id=seg.id, cutoff=cutoff) for key,seg in segments.items() if key != "UNKNOWN"}
    prices = {k:v.get("weighted_median_reference_price") for k,v in values.items()}
    pc = prices.get("PC")
    # Keep provider-specific console semantics separate. Prefer a proven shared market,
    # otherwise expose provider-labelled PlayStation/generic console independently.
    console_shared = prices.get("CONSOLE_SHARED")
    playstation = prices.get("PLAYSTATION")
    console_generic = prices.get("CONSOLE_GENERIC")
    console = console_shared if console_shared is not None else playstation if playstation is not None else console_generic
    switch = prices.get("SWITCH")
    def ratio(a,b): return a/b if a is not None and b not in (None,0) else None
    def spread(a,b): return a-b if a is not None and b is not None else None
    def spread_pct(a,b): return (a-b)/b if a is not None and b not in (None,0) else None
    source_ids=[]
    for v in values.values(): source_ids.extend(v.get("source_observation_ids",[]))
    return {
        "pc_price": pc, "console_price": console, "console_shared_price": console_shared, "playstation_price": playstation, "console_generic_price": console_generic, "switch_price": switch,
        "pc_console_ratio": ratio(pc, console), "pc_switch_ratio": ratio(pc, switch),
        "pc_console_spread": spread(pc, console), "pc_console_spread_pct": spread_pct(pc, console),
        "pc_switch_spread": spread(pc, switch), "pc_switch_spread_pct": spread_pct(pc, switch),
        # These stay unclaimed until sufficient real paired history exists.
        "historical_ratio_divergence": None, "relative_momentum": None, "relative_volatility": None,
        "rolling_correlation": None, "lead_lag_seconds": None, "event_response_difference": None,
        "sbc_response_difference": None, "promo_response_difference": None, "recovery_time_difference": None,
        "market_regime_divergence": None, "convergence_probability": None,
        "source_observation_ids": source_ids,
    }


def persist_cross_market_features(session: Session, *, card_id, game_year: int, segments: dict[str, object], cutoff: datetime) -> DerivedFeatureSnapshot:
    value=calculate_cross_market_features(session, card_id=card_id, game_year=game_year, segments=segments, cutoff=cutoff)
    row=DerivedFeatureSnapshot(feature_family="cross_market", feature_key="market_divergence", algorithm_version=ALGORITHM_VERSION,
        game_year=game_year, market_segment_id=None, card_id=card_id, input_cutoff_at=cutoff, calculated_at=datetime.now(UTC),
        value_json={k:v for k,v in value.items() if k!="source_observation_ids"}, source_observation_ids_json=value.get("source_observation_ids",[]), metadata_json={})
    session.add(row); session.flush(); return row
