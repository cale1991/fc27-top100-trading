from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass(frozen=True, slots=True)
class EventReaction:
    event_type: str
    segment_key: str
    horizon_seconds: int
    return_pct: float


def estimate_event_response(history:list[EventReaction], *, event_type:str, segment_key:str, horizon_seconds:int) -> dict:
    rows=[x.return_pct for x in history if x.event_type==event_type and x.segment_key==segment_key and x.horizon_seconds==horizon_seconds]
    return {"sample_size":len(rows),"expected_return_pct":mean(rows) if rows else None,"confidence":min(1.0,(len(rows)/20)**0.5) if rows else 0.0}
