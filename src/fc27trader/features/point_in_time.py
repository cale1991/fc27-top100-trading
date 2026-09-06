from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from fc27trader.db.models import ContentEvent, ExecutionObservation, ReferencePriceObservation


def reference_observations_known_at(session: Session, *, card_id, market_segment_id, cutoff: datetime, limit: int = 1000):
    """Only observations actually inserted/retrieved by cutoff may participate.

    This deliberately uses knowledge time (inserted_at/observed_at), not provider event
    time. A historical row imported tomorrow is not available to yesterday's backtest.
    """
    known_at = func.coalesce(ReferencePriceObservation.inserted_at, ReferencePriceObservation.observed_at)
    return list(session.scalars(
        select(ReferencePriceObservation).where(
            ReferencePriceObservation.card_id == card_id,
            ReferencePriceObservation.market_segment_id == market_segment_id,
            known_at <= cutoff,
            ReferencePriceObservation.quality_status == "VALID",
        ).order_by(known_at.desc()).limit(limit)
    ))


def execution_observations_known_at(session: Session, *, card_id, market_segment_id, cutoff: datetime, limit: int = 200):
    known_at = func.coalesce(ExecutionObservation.inserted_at, ExecutionObservation.observed_at)
    return list(session.scalars(
        select(ExecutionObservation).where(
            ExecutionObservation.card_id == card_id,
            ExecutionObservation.market_segment_id == market_segment_id,
            known_at <= cutoff,
            ExecutionObservation.quality_status == "VALID",
        ).order_by(known_at.desc()).limit(limit)
    ))


def content_events_known_at(session: Session, *, game_year: int, cutoff: datetime, limit: int = 1000):
    return list(session.scalars(
        select(ContentEvent).where(
            ContentEvent.game_year == game_year,
            ContentEvent.detected_at <= cutoff,
        ).order_by(ContentEvent.detected_at.desc()).limit(limit)
    ))
