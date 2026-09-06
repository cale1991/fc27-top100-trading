from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.db.models import ProviderHealth
from fc27trader.db.json_safe import to_json_safe

_SECRET_RE = re.compile(r"(?i)(authorization|x-auth-token|api[-_ ]?key|bearer)\s*[:=]?\s*[^\s,;]+")


def redact_provider_error(value: str) -> str:
    return _SECRET_RE.sub(lambda m: m.group(1) + ": [REDACTED]", value)[:4000]


def _row(session: Session, provider_key: str, provider_role: str, platform: str = "pc") -> ProviderHealth:
    row = session.scalar(select(ProviderHealth).where(
        ProviderHealth.provider_key == provider_key,
        ProviderHealth.provider_role == provider_role,
        ProviderHealth.platform == platform,
    ))
    if row is None:
        row = ProviderHealth(
            provider_key=provider_key,
            provider_role=provider_role,
            platform=platform,
            requests_total=0,
            requests_failed=0,
            cards_covered=0,
            items_seen=0,
            items_ingested=0,
            duplicates_skipped=0,
            quarantined_observations=0,
            parsing_failures=0,
            normalization_failures=0,
            identity_failures=0,
            status="DISABLED",
            enabled=True,
            supported_segments_json=[],
            updated_at=datetime.now(UTC),
            metadata_json={},
        )
        session.add(row)
        session.flush()
    return row


def set_provider_state(
    session: Session,
    *,
    provider_key: str,
    provider_role: str,
    status: str,
    platform: str = "pc",
    access_type: str | None = None,
    enabled: bool | None = None,
    supported_segments: list[str] | None = None,
    retry_after_seconds: int | None = None,
    metadata: dict | None = None,
) -> ProviderHealth:
    row = _row(session, provider_key, provider_role, platform)
    row.status = status
    row.access_type = access_type or row.access_type
    if enabled is not None:
        row.enabled = enabled
    if supported_segments is not None:
        row.supported_segments_json = supported_segments
    row.retry_after_seconds = retry_after_seconds
    row.updated_at = datetime.now(UTC)
    row.metadata_json = to_json_safe({**(row.metadata_json or {}), **(metadata or {})})
    session.flush()
    return row


def record_provider_success(
    session: Session,
    *,
    provider_key: str,
    provider_role: str,
    latency_ms: float | None,
    platform: str = "pc",
    status: str = "HEALTHY",
    access_type: str | None = None,
    supported_segments: list[str] | None = None,
    cards_covered: int | None = None,
    latest_observation_at: datetime | None = None,
    latest_provider_timestamp: datetime | None = None,
    rate_limit_remaining: int | None = None,
    rate_limit_reset_at: datetime | None = None,
    retry_after_seconds: int | None = None,
    items_seen: int = 0,
    items_ingested: int = 0,
    duplicates_skipped: int = 0,
    quarantined_observations: int = 0,
    parsing_failures: int = 0,
    normalization_failures: int = 0,
    identity_failures: int = 0,
    poll_duration_ms: float | None = None,
    gap_status: str | None = None,
    platform_certainty: float | None = None,
    metadata: dict | None = None,
) -> ProviderHealth:
    now = datetime.now(UTC)
    row = _row(session, provider_key, provider_role, platform)
    row.requests_total += 1
    row.last_request_at = now
    row.last_success_at = now
    row.last_error = None
    row.status = status
    row.access_type = access_type or row.access_type
    if supported_segments is not None:
        row.supported_segments_json = supported_segments
    if cards_covered is not None:
        row.cards_covered = max(row.cards_covered or 0, cards_covered)
    row.latest_observation_at = latest_observation_at or row.latest_observation_at
    row.latest_provider_timestamp = latest_provider_timestamp or row.latest_provider_timestamp
    if latest_provider_timestamp is not None:
        ts = latest_provider_timestamp if latest_provider_timestamp.tzinfo else latest_provider_timestamp.replace(tzinfo=UTC)
        row.latest_observation_age_seconds = Decimal(str(max(0.0, (now - ts).total_seconds())))
    row.last_latency_ms = Decimal(str(latency_ms)) if latency_ms is not None else row.last_latency_ms
    row.error_rate = Decimal(str(row.requests_failed / row.requests_total)) if row.requests_total else Decimal("0")
    row.rate_limit_remaining = rate_limit_remaining
    row.rate_limit_reset_at = rate_limit_reset_at
    row.retry_after_seconds = retry_after_seconds
    row.items_seen = (row.items_seen or 0) + int(items_seen)
    row.items_ingested = (row.items_ingested or 0) + int(items_ingested)
    row.duplicates_skipped = (row.duplicates_skipped or 0) + int(duplicates_skipped)
    row.quarantined_observations = (row.quarantined_observations or 0) + int(quarantined_observations)
    row.parsing_failures = (row.parsing_failures or 0) + int(parsing_failures)
    row.normalization_failures = (row.normalization_failures or 0) + int(normalization_failures)
    row.identity_failures = (row.identity_failures or 0) + int(identity_failures)
    row.last_poll_duration_ms = Decimal(str(poll_duration_ms)) if poll_duration_ms is not None else row.last_poll_duration_ms
    row.gap_status = gap_status or row.gap_status
    row.platform_certainty = Decimal(str(platform_certainty)) if platform_certainty is not None else row.platform_certainty
    row.updated_at = now
    row.metadata_json = to_json_safe({**(row.metadata_json or {}), **(metadata or {})})
    session.flush()
    return row


def record_provider_failure(
    session: Session,
    *,
    provider_key: str,
    provider_role: str,
    error: str,
    platform: str = "pc",
    latency_ms: float | None = None,
    status: str = "DEGRADED",
    retry_after_seconds: int | None = None,
    poll_duration_ms: float | None = None,
    metadata: dict | None = None,
) -> ProviderHealth:
    now = datetime.now(UTC)
    row = _row(session, provider_key, provider_role, platform)
    row.requests_total += 1
    row.requests_failed += 1
    row.last_request_at = now
    row.last_error_at = now
    row.last_error = redact_provider_error(error)
    row.status = status
    row.retry_after_seconds = retry_after_seconds
    row.last_latency_ms = Decimal(str(latency_ms)) if latency_ms is not None else row.last_latency_ms
    row.last_poll_duration_ms = Decimal(str(poll_duration_ms)) if poll_duration_ms is not None else row.last_poll_duration_ms
    row.error_rate = Decimal(str(row.requests_failed / row.requests_total)) if row.requests_total else Decimal("1")
    row.updated_at = now
    row.metadata_json = to_json_safe({**(row.metadata_json or {}), **(metadata or {})})
    session.flush()
    return row
