from __future__ import annotations

import math
from datetime import datetime


def pct_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return (current - previous) / previous


def cyclical_time_features(timestamp: datetime) -> dict[str, float | int]:
    hour = timestamp.hour + timestamp.minute / 60.0
    angle = 2 * math.pi * hour / 24.0
    return {
        "hour_sin": math.sin(angle),
        "hour_cos": math.cos(angle),
        "day_of_week": timestamp.weekday(),
    }
