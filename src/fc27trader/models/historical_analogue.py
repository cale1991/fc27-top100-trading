from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True, slots=True)
class AnaloguePoint:
    key: str
    normalized_features: dict[str,float]
    outcome_return: float | None = None


def nearest_analogues(query: dict[str,float], candidates: list[AnaloguePoint], *, limit:int=10) -> list[tuple[AnaloguePoint,float]]:
    rows=[]
    for c in candidates:
        shared=set(query).intersection(c.normalized_features)
        if not shared: continue
        distance=sqrt(sum((query[k]-c.normalized_features[k])**2 for k in shared)/len(shared))
        rows.append((c,distance))
    rows.sort(key=lambda x:x[1])
    return rows[:limit]
