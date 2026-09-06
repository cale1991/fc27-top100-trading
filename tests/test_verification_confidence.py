from datetime import UTC, datetime, timedelta

from fc27trader.services.verification_confidence import calculate_manual_observation_confidence


def test_manual_confidence_distinguishes_quality_and_age():
    now = datetime(2026, 9, 4, 0, 0, tzinfo=UTC)
    fresh = calculate_manual_observation_confidence(
        observed_at=now,
        received_at=now,
        listing_prices=[95000, 95500, 96000, 96500, 97000],
        lowest_bin=95000,
        screenshot_present=True,
    )
    stale = calculate_manual_observation_confidence(
        observed_at=now - timedelta(minutes=20),
        received_at=now,
        listing_prices=[95000],
        lowest_bin=95000,
        screenshot_present=False,
    )
    assert fresh.value > 0.95
    assert stale.value < fresh.value
    assert stale.value >= 0.20
