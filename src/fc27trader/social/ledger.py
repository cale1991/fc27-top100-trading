from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from fc27trader.db.models import PublicPost, PublicPrediction
from fc27trader.social.persona import anti_slop_preflight


def create_prediction_draft(
    session: Session,
    *,
    full_post: str,
    prediction: str,
    market_state: dict,
    card_id=None,
    category_key: str | None = None,
    target_price: int | None = None,
    horizon_seconds: int | None = None,
    confidence: float | None = None,
    catalyst: str | None = None,
) -> tuple[PublicPrediction, PublicPost]:
    preflight = anti_slop_preflight(full_post)
    now = datetime.now(UTC)
    pred = PublicPrediction(
        created_at=now,
        published_at=None,
        card_id=card_id,
        category_key=category_key,
        full_post=preflight.rewritten,
        market_state_json=market_state,
        prediction=prediction,
        target_price=target_price,
        horizon_seconds=horizon_seconds,
        confidence=Decimal(str(confidence)) if confidence is not None else None,
        catalyst=catalyst,
        status="draft",
        result_json={},
    )
    session.add(pred)
    session.flush()
    post = PublicPost(
        prediction_id=pred.id,
        platform="x",
        created_at=now,
        published_at=None,
        external_post_id=None,
        text=preflight.rewritten,
        status="draft",
        preflight_json={"flags": preflight.flags, "approved": preflight.approved},
        metadata_json={},
    )
    session.add(post)
    session.flush()
    return pred, post
