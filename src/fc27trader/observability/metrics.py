from prometheus_client import Counter, Gauge, Histogram

collector_runs_total = Counter(
    "fc27_collector_runs_total", "Collector runs", ["collector", "status"]
)
collector_records_total = Counter(
    "fc27_collector_records_total", "Normalized records written", ["collector", "record_type"]
)
collector_duration_seconds = Histogram(
    "fc27_collector_duration_seconds", "Collector run duration", ["collector"]
)
source_data_age_seconds = Gauge(
    "fc27_source_data_age_seconds", "Age of provider-side source timestamp", ["source"]
)
market_snapshot_lag_seconds = Gauge(
    "fc27_market_snapshot_lag_seconds", "Observed timestamp minus source timestamp", ["source", "platform"]
)
