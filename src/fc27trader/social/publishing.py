from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.db.models import PersonaState, PublicPost, PublicPrediction, SocialMarketImpact
from fc27trader.db.repositories import insert_content_event
from fc27trader.domain.enums import EvidenceClass, EventType
from fc27trader.domain.events import MarketEvent
from fc27trader.social.persona import anti_slop_preflight
from fc27trader.social.x_client import XPostingClient

_PRIVATE_KEYS = {"portfolio", "position", "inventory", "cost_basis", "average_buy_price", "private_exit"}


def validate_public_market_state(market_state: dict) -> None:
    forbidden = _PRIVATE_KEYS.intersection(k.lower() for k in market_state)
    if forbidden:
        raise ValueError(f"public prediction market_state contains private portfolio fields: {sorted(forbidden)}")


def publish_prediction(
    session: Session,
    *,
    prediction: PublicPrediction,
    post: PublicPost,
    client: XPostingClient,
) -> dict:
    if prediction.status == "published" or post.status == "published":
        raise ValueError("prediction/post already published")
    validate_public_market_state(prediction.market_state_json or {})
    preflight = anti_slop_preflight(post.text)
    post.text = preflight.rewritten
    post.preflight_json = {"flags": preflight.flags, "approved": preflight.approved}

    result = client.post(post.text)
    external_id = str((result.get("data") or {}).get("id") or "")
    if not external_id:
        raise RuntimeError("X API response did not contain a post id")
    now = datetime.now(UTC)
    post.external_post_id = external_id
    post.published_at = now
    post.status = "published"
    prediction.full_post = post.text
    prediction.published_at = now
    prediction.status = "published"

    event = MarketEvent(
        event_type=EventType.PUBLIC_PREDICTION,
        evidence_class=EvidenceClass.CONFIRMED,
        game_year=26,
        source_key="public_ai_trader_x",
        external_id=external_id,
        title="Public AI trader prediction published",
        summary=prediction.prediction,
        published_at=now,
        effective_at=now,
        detected_at=now,
        affected_card_ids=[str(prediction.card_id)] if prediction.card_id else [],
        affected_segments=[prediction.category_key] if prediction.category_key else [],
        payload={
            "prediction_id": str(prediction.id),
            "target_price": prediction.target_price,
            "horizon_seconds": prediction.horizon_seconds,
            "confidence": float(prediction.confidence) if prediction.confidence is not None else None,
        },
    )
    insert_content_event(session, event)

    state = session.scalar(select(PersonaState).where(PersonaState.account_key == "public_ai_trader_x"))
    if state is None:
        state = PersonaState(account_key="public_ai_trader_x", updated_at=now, recent_style_json={}, recent_posts_json=[], metadata_json={})
        session.add(state)
    recent = list(state.recent_posts_json or [])[-49:]
    recent.append({"published_at": now.isoformat(), "text": post.text, "external_post_id": external_id})
    state.recent_posts_json = recent
    state.updated_at = now
    session.flush()
    return result


def record_social_market_impact(
    session: Session,
    *,
    post: PublicPost,
    card_id,
    price_before: int | None,
    price_after: int | None,
    listing_change_pct: float | None = None,
    liquidity_change_pct: float | None = None,
    abnormal_move_pct: float | None = None,
    reach: int | None = None,
    engagement: int | None = None,
) -> SocialMarketImpact:
    impact_score = None
    if abnormal_move_pct is not None:
        reach_factor = min(1.0, (reach or 0) / 10000) if reach is not None else 0.25
        impact_score = min(1.0, abs(abnormal_move_pct) / 0.10) * reach_factor
    row = SocialMarketImpact(
        public_post_id=post.id,
        card_id=card_id,
        measured_at=datetime.now(UTC),
        price_before=price_before,
        price_after=price_after,
        listing_change_pct=Decimal(str(listing_change_pct)) if listing_change_pct is not None else None,
        liquidity_change_pct=Decimal(str(liquidity_change_pct)) if liquidity_change_pct is not None else None,
        abnormal_move_pct=Decimal(str(abnormal_move_pct)) if abnormal_move_pct is not None else None,
        reach=reach,
        engagement=engagement,
        impact_score=Decimal(str(impact_score)) if impact_score is not None else None,
        metadata_json={},
    )
    session.add(row)
    session.flush()
    event = MarketEvent(
        event_type=EventType.SOCIAL_MARKET_IMPACT,
        evidence_class=EvidenceClass.MEASURED,
        game_year=26,
        source_key="public_ai_trader_x",
        external_id=str(row.id),
        title="Public account market-impact measurement",
        detected_at=row.measured_at,
        effective_at=row.measured_at,
        affected_card_ids=[str(card_id)] if card_id else [],
        payload={"social_market_impact_id": str(row.id), "impact_score": impact_score, "reach": reach, "engagement": engagement},
    )
    insert_content_event(session, event)
    return row
