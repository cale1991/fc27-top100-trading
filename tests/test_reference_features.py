from datetime import UTC, datetime, timedelta
from fc27trader.features.reference_features import derive_reference_features


def test_older_reference_has_more_uncertainty():
    now = datetime.now(UTC)
    fresh = derive_reference_features(reference_price=100000, provider_timestamp=now-timedelta(minutes=1), observed_at=now,
        historical_provider_error_pct=0.01, stated_uncertainty_pct=0.01, confidence=0.9)
    stale = derive_reference_features(reference_price=100000, provider_timestamp=now-timedelta(hours=2), observed_at=now,
        historical_provider_error_pct=0.01, stated_uncertainty_pct=0.01, confidence=0.9)
    assert stale["reference_uncertainty_pct"] > fresh["reference_uncertainty_pct"]
