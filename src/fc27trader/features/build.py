"""Feature materialization entrypoint.

Phase 1 writes point-in-time-correct training rows from market_snapshots + content_events.
Never join an event/snapshot whose detected_at/observed_at is after the prediction timestamp.
"""


def assert_point_in_time_safe(feature_timestamp, source_timestamp) -> None:
    if source_timestamp > feature_timestamp:
        raise ValueError("lookahead detected: source timestamp is after feature timestamp")
