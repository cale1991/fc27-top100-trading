from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlalchemy import select

from fc27trader.api.schemas import ManualVerificationResponseIn
from fc27trader.db.models import Card, ManualVerificationRequest, ManualVerificationResponse, OpportunityCandidate
from fc27trader.db.repositories import insert_execution_observation
from fc27trader.db.session import SessionLocal
from fc27trader.services.activity import create_notification, record_activity
from fc27trader.services.market_segments import get_market_segment
from fc27trader.services.verification_confidence import calculate_manual_observation_confidence
from fc27trader.settings import get_settings

router = APIRouter(prefix="/manual-verifications", tags=["verification"])
settings = get_settings()


def _serialize_request(session, r: ManualVerificationRequest) -> dict:
    card = session.get(Card, r.card_id)
    now = datetime.now(UTC)
    ref_age = None
    if r.reference_timestamp:
        ref_age = max(0, (now - r.reference_timestamp).total_seconds())
    return {
        "id": str(r.id),
        "candidate_id": str(r.candidate_id) if r.candidate_id else None,
        "card_id": str(r.card_id),
        "card": card.name if card else "Unknown card",
        "card_version": (card.rarity if card else None) or "Unknown",
        "rating": card.rating if card else None,
        "priority": r.priority,
        "reason": r.reason,
        "latest_reference_price": r.latest_reference_price,
        "reference_timestamp": r.reference_timestamp.isoformat() if r.reference_timestamp else None,
        "reference_age_seconds": ref_age,
        "reference_uncertainty_pct": float(r.reference_uncertainty_pct) if r.reference_uncertainty_pct is not None else None,
        "expected_acquisition_range": [r.expected_acquisition_min, r.expected_acquisition_max],
        "attractive_at_or_below": r.attractive_at_or_below,
        "required_information": r.required_information,
        "expected_information_value": float(r.expected_information_value) if r.expected_information_value is not None else None,
        "expires_at": r.expires_at.isoformat() if r.expires_at else None,
    }


@router.get("/pending")
def pending_manual_verifications(limit: int = 20) -> list[dict]:
    with SessionLocal() as session:
        rows = list(
            session.scalars(
                select(ManualVerificationRequest)
                .where(ManualVerificationRequest.status == "pending")
                .order_by(ManualVerificationRequest.priority.desc(), ManualVerificationRequest.requested_at.asc())
                .limit(limit)
            )
        )
        return [_serialize_request(session, row) for row in rows]


def _record_response(
    *,
    request_id: uuid.UUID,
    payload: ManualVerificationResponseIn,
    screenshot_uri: str | None = None,
) -> dict:
    received_at = datetime.now(UTC)
    with SessionLocal() as session:
        request = session.get(ManualVerificationRequest, request_id)
        if request is None:
            raise HTTPException(status_code=404, detail="verification request not found")
        if request.status != "pending":
            raise HTTPException(status_code=409, detail=f"request status is {request.status}")
        card = session.get(Card, request.card_id)
        if card is None:
            raise HTTPException(status_code=404, detail="card not found")

        listings = sorted(int(x) for x in payload.listing_prices if int(x) > 0)
        lowest = payload.lowest_bin or (listings[0] if listings else None)
        screenshot_uri = screenshot_uri or payload.screenshot_uri
        quality = calculate_manual_observation_confidence(
            observed_at=payload.observed_at,
            received_at=received_at,
            listing_prices=listings,
            lowest_bin=lowest,
            screenshot_present=bool(screenshot_uri),
            approximate=payload.approximate,
        )
        input_kind = (
            "screenshot_with_values" if screenshot_uri and (listings or lowest)
            else "screenshot_only" if screenshot_uri
            else "manual_approximate" if payload.approximate
            else "manual_exact"
        )

        segment = session.get(__import__("fc27trader.db.models", fromlist=["MarketSegment"]).MarketSegment, request.market_segment_id) if request.market_segment_id else get_market_segment(session, game_year=26, segment_key="PC")
        execution = insert_execution_observation(
            session,
            card=card,
            source_key="manual_user",
            observed_at=payload.observed_at,
            observation_type=input_kind,
            lowest_bin=lowest,
            best_bid=payload.best_bid,
            listing_prices=listings,
            confidence=quality.value,
            expires_at=payload.observed_at + timedelta(minutes=5),
            manual_verification_request_id=request.id,
            platform=(segment.platform or "unknown"),
            market_segment_id=segment.id,
            metadata={
                "verification_request_id": str(request.id),
                "quality_reasons": quality.reasons,
                "screenshot_uri": screenshot_uri,
                "approximate": payload.approximate,
            },
        )
        response = ManualVerificationResponse(
            request_id=request.id,
            market_segment_id=segment.id,
            received_at=received_at,
            observed_at=payload.observed_at,
            listing_prices_json=listings,
            lowest_bin=lowest,
            best_bid=payload.best_bid,
            screenshot_uri=screenshot_uri,
            notes=payload.notes,
            input_kind=input_kind,
            observation_confidence=Decimal(str(quality.value)),
            observation_age_seconds=Decimal(str(quality.age_seconds)),
            execution_observation_id=execution.id,
            metadata_json={"quality_reasons": quality.reasons},
        )
        session.add(response)

        # Screenshot-only evidence is preserved but cannot produce a price decision yet.
        actionable = None
        candidate_status = None
        resolved = lowest is not None
        if resolved:
            request.status = "resolved"
            request.resolved_at = received_at
        else:
            request.status = "pending"

        action = "WATCH"
        trade_model_confidence = None
        if request.candidate_id:
            candidate = session.get(OpportunityCandidate, request.candidate_id)
            if candidate:
                trade_model_confidence = float(candidate.confidence_score) if candidate.confidence_score is not None else None
                candidate.execution_observation_id = execution.id
                candidate.last_scored_at = received_at
                if lowest is not None and request.attractive_at_or_below is not None:
                    actionable = lowest <= request.attractive_at_or_below
                    if actionable:
                        action = "BUY" if (candidate.action or "buy").lower() not in {"strong_buy"} else "STRONG BUY"
                        candidate.status = "execution_verified_actionable"
                    else:
                        action = "PASS"
                        candidate.status = "execution_verified_not_actionable"
                elif lowest is not None:
                    candidate.status = "execution_verified_needs_model_reevaluation"
                    action = (candidate.action or "WATCH").upper()
                else:
                    candidate.status = "needs_verification"
                    action = "VERIFY"
                candidate_status = candidate.status

        record_activity(
            session,
            category="verification",
            severity="success" if actionable else "info",
            title=f"Market verification received — {card.name}",
            message=(
                f"Lowest observed PC BIN {lowest:,}; execution-observation confidence {quality.value:.0%}; result {action}."
                if lowest is not None
                else f"Screenshot stored; numeric listings still required. Execution-observation confidence {quality.value:.0%}."
            ),
            card_id=card.id,
            candidate_id=request.candidate_id,
            metadata={"request_id": str(request.id), "action": action},
        )
        if actionable:
            create_notification(
                session,
                kind="verified_buy",
                priority=max(7, request.priority),
                title=f"{action}: {card.name}",
                message=f"Verified lowest BIN {lowest:,}; threshold {request.attractive_at_or_below:,}.",
                card_id=card.id,
                candidate_id=request.candidate_id,
                verification_request_id=request.id,
            )
        session.commit()
        return {
            "request_id": str(request.id),
            "execution_observation_id": execution.id,
            "lowest_bin": lowest,
            "observation_confidence": quality.value,
            "execution_observation_confidence": quality.value,
            "trade_model_confidence": trade_model_confidence,
            "confidence_reasons": quality.reasons,
            "input_kind": input_kind,
            "actionable_against_current_threshold": actionable,
            "action": action,
            "candidate_status": candidate_status,
            "reevaluation_triggered": lowest is not None,
            "resolved": resolved,
        }


@router.post("/{request_id}/response")
def record_manual_verification(request_id: uuid.UUID, payload: ManualVerificationResponseIn) -> dict:
    return _record_response(request_id=request_id, payload=payload)


@router.post("/{request_id}/evidence")
async def upload_verification_evidence(
    request_id: uuid.UUID,
    observed_at: datetime = Form(...),
    listing_prices: str = Form(""),
    lowest_bin: int | None = Form(None),
    best_bid: int | None = Form(None),
    approximate: bool = Form(False),
    notes: str | None = Form(None),
    screenshot: UploadFile | None = File(None),
) -> dict:
    prices = []
    if listing_prices.strip():
        try:
            prices = [int(x.strip()) for x in listing_prices.replace("\n", ",").split(",") if x.strip()]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="listing_prices must be comma/newline-separated integers") from exc

    screenshot_uri = None
    if screenshot is not None:
        suffix = Path(screenshot.filename or "capture.jpg").suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise HTTPException(status_code=400, detail="screenshot must be PNG/JPG/WEBP")
        folder = settings.upload_store_path / "verifications" / str(request_id)
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"{uuid.uuid4()}{suffix}"
        content = await screenshot.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="screenshot exceeds 10 MB")
        target.write_bytes(content)
        screenshot_uri = str(target.as_posix())

    payload = ManualVerificationResponseIn(
        observed_at=observed_at,
        listing_prices=prices,
        lowest_bin=lowest_bin,
        best_bid=best_bid,
        approximate=approximate,
        notes=notes,
        screenshot_uri=screenshot_uri,
    )
    return _record_response(request_id=request_id, payload=payload, screenshot_uri=screenshot_uri)
