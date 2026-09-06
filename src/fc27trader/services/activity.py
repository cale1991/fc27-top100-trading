from __future__ import annotations

from datetime import UTC, datetime
import uuid

from sqlalchemy.orm import Session

from fc27trader.db.models import ActivityFeedItem, Notification


def record_activity(
    session: Session,
    *,
    category: str,
    title: str,
    message: str | None = None,
    severity: str = "info",
    card_id: uuid.UUID | None = None,
    candidate_id: uuid.UUID | None = None,
    content_event_id: uuid.UUID | None = None,
    source_key: str | None = None,
    occurred_at: datetime | None = None,
    metadata: dict | None = None,
) -> ActivityFeedItem:
    row = ActivityFeedItem(
        occurred_at=occurred_at or datetime.now(UTC),
        category=category,
        severity=severity,
        title=title,
        message=message,
        card_id=card_id,
        candidate_id=candidate_id,
        content_event_id=content_event_id,
        source_key=source_key,
        metadata_json=metadata or {},
    )
    session.add(row)
    session.flush()
    return row


def create_notification(
    session: Session,
    *,
    kind: str,
    priority: int,
    title: str,
    message: str | None = None,
    card_id: uuid.UUID | None = None,
    candidate_id: uuid.UUID | None = None,
    verification_request_id: uuid.UUID | None = None,
    expires_at: datetime | None = None,
    metadata: dict | None = None,
) -> Notification:
    row = Notification(
        created_at=datetime.now(UTC),
        kind=kind,
        priority=priority,
        title=title,
        message=message,
        status="unread",
        card_id=card_id,
        candidate_id=candidate_id,
        verification_request_id=verification_request_id,
        expires_at=expires_at,
        metadata_json=metadata or {},
    )
    session.add(row)
    session.flush()
    return row
