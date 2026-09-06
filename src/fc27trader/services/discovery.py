from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.db.models import ManualVerificationRequest, OpportunityCandidate, ReferencePriceObservation
from fc27trader.opportunity.models import OpportunityInputs
from fc27trader.opportunity.scoring import discover_and_rank
from fc27trader.services.activity import create_notification, record_activity
from fc27trader.services.manual_verification import verification_value


def _action_for(score: float, requires_verification: bool, metadata: dict) -> str:
    explicit = metadata.get("action")
    if explicit:
        return str(explicit).lower()
    if score >= 2.5:
        return "strong_buy"
    if score >= 1.25:
        return "buy"
    return "watch"


def persist_discovery_cycle(
    session: Session,
    market: list[OpportunityInputs],
    *,
    minimum_score: float = 0.35,
    max_candidates: int = 100,
    ttl_seconds: int = 900,
) -> list[OpportunityCandidate]:
    """Persist a new ranking over whatever broad PC market is observable now.

    No card list is carried forward as a permanent universe. Previous active
    candidates are superseded; cards can leave and re-enter on later cycles.
    Manual verification is requested only for BUY-class candidates when the
    expected information value is positive.
    """
    now = datetime.now(UTC)
    ranked = discover_and_rank(
        market,
        minimum_score=minimum_score,
        max_candidates=max_candidates,
    )
    by_card = {x.card_id: x for x in market}

    previous = list(
        session.scalars(
            select(OpportunityCandidate).where(
                OpportunityCandidate.platform == "pc",
                OpportunityCandidate.status.in_([
                    "ranked", "needs_verification", "execution_verified_actionable",
                    "execution_verified_not_actionable", "execution_verified_needs_model_reevaluation",
                ]),
            )
        )
    )
    previous_by_card = {str(row.card_id): row for row in previous}
    for row in previous:
        row.status = "superseded"

    rows: list[OpportunityCandidate] = []
    for candidate in ranked:
        x = by_card[candidate.card_id]
        metadata = x.metadata or {}
        action = _action_for(candidate.score, candidate.requires_execution_verification, metadata)
        ref_id = metadata.get("reference_observation_id")
        ref = None
        if ref_id:
            try:
                ref = session.get(ReferencePriceObservation, int(ref_id))
            except (TypeError, ValueError):
                ref = None
        max_buy = metadata.get("max_recommended_buy_price") or metadata.get("max_buy_price") or metadata.get("expected_acquisition_price")
        quantity = int(metadata.get("recommended_quantity") or 1)
        target_low = metadata.get("target_sell_low") or metadata.get("target_sell_price")
        target_high = metadata.get("target_sell_high") or target_low
        capital = int(max_buy) * quantity if max_buy else None
        expected_roi = (x.expected_net_profit / capital) if x.expected_net_profit is not None and capital else None
        confidence = None if x.reference_uncertainty_pct is None else max(0.0, min(1.0, 1.0 - x.reference_uncertainty_pct))

        row = OpportunityCandidate(
            card_id=uuid.UUID(candidate.card_id),
            platform="pc",
            discovered_at=now,
            last_scored_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
            status="needs_verification" if candidate.requires_execution_verification and action in {"buy", "strong_buy"} else "ranked",
            rank=candidate.rank,
            opportunity_score=Decimal(str(candidate.score)),
            reference_observation_id=ref.id if ref else None,
            expected_acquisition_price=metadata.get("expected_acquisition_price"),
            acquisition_probability=Decimal(str(x.acquisition_probability)) if x.acquisition_probability is not None else None,
            expected_discount_to_reference=Decimal(str(x.expected_discount_to_reference)) if x.expected_discount_to_reference is not None else None,
            profitable_exit_probability=Decimal(str(x.profitable_exit_probability)) if x.profitable_exit_probability is not None else None,
            expected_net_profit=int(x.expected_net_profit) if x.expected_net_profit is not None else None,
            expected_profit_per_hour=Decimal(str(x.expected_profit_per_hour)) if x.expected_profit_per_hour is not None else None,
            expected_holding_seconds=int(x.expected_holding_seconds) if x.expected_holding_seconds is not None else None,
            position_capacity_coins=int(x.position_capacity_coins) if x.position_capacity_coins is not None else None,
            liquidity_score=Decimal(str(x.liquidity_score)) if x.liquidity_score is not None else None,
            sell_through_rate=Decimal(str(x.sell_through_rate)) if x.sell_through_rate is not None else None,
            volatility=Decimal(str(x.volatility)) if x.volatility is not None else None,
            downside_risk=Decimal(str(x.downside_risk)) if x.downside_risk is not None else None,
            catalyst_score=Decimal(str(x.catalyst_score)) if x.catalyst_score is not None else None,
            ea_intervention_risk=Decimal(str(x.ea_intervention_risk)) if x.ea_intervention_risk is not None else None,
            opportunity_cost=Decimal(str(x.opportunity_cost)) if x.opportunity_cost is not None else None,
            requires_manual_verification=candidate.requires_execution_verification,
            action=action,
            max_recommended_buy_price=max_buy,
            target_sell_low=target_low,
            target_sell_high=target_high,
            recommended_quantity=quantity,
            expected_roi=Decimal(str(expected_roi)) if expected_roi is not None else None,
            confidence_score=Decimal(str(confidence)) if confidence is not None else None,
            main_catalyst=metadata.get("main_catalyst") or metadata.get("catalyst"),
            invalidation_condition=metadata.get("invalidation_condition"),
            exit_logic=metadata.get("exit_logic"),
            score_components_json=candidate.components,
            metadata_json=metadata,
        )
        session.add(row)
        session.flush()
        # Persist point-in-time historical-strategy recognition after ranking.
        # This is additive evidence; the card was discovered from the broad market first.
        from fc27trader.services.strategy_intelligence import persist_candidate_strategy_matches
        persist_candidate_strategy_matches(session, row, x)
        rows.append(row)

        old = previous_by_card.get(candidate.card_id)
        if old is None or old.action != action:
            record_activity(
                session,
                category="opportunity",
                severity="success" if action in {"buy", "strong_buy"} else "info",
                title=f"Candidate promoted to {action.upper().replace('_', ' ')}",
                message=f"Rank #{candidate.rank}; opportunity score {candidate.score:.2f}.",
                card_id=row.card_id,
                candidate_id=row.id,
                metadata={"previous_action": old.action if old else None},
            )

        if candidate.requires_execution_verification and action in {"buy", "strong_buy"}:
            uncertainty = max(0.0, min(1.0, x.reference_uncertainty_pct or 0.25))
            expected_profit = max(0.0, float(x.expected_net_profit or 0))
            eiv = verification_value(
                probability_decision_changes=min(1.0, 0.25 + uncertainty),
                expected_profit_if_actionable=expected_profit,
                confidence_gain=min(1.0, 0.20 + uncertainty),
                interruption_cost=float(metadata.get("manual_verification_interrupt_cost_coins", 500)),
            )
            if eiv.should_request:
                latest_reference_price = ref.price if ref else x.reference_price
                threshold = max_buy
                req = ManualVerificationRequest(
                    candidate_id=row.id,
                    card_id=row.card_id,
                    platform="pc",
                    requested_at=now,
                    priority=10 if action == "strong_buy" else 7,
                    status="pending",
                    reason=f"{action.upper().replace('_', ' ')} candidate lacks sufficiently reliable execution data",
                    reference_observation_id=ref.id if ref else None,
                    latest_reference_price=latest_reference_price,
                    reference_timestamp=(ref.provider_timestamp or ref.observed_at) if ref else None,
                    reference_uncertainty_pct=Decimal(str(x.reference_uncertainty_pct)) if x.reference_uncertainty_pct is not None else None,
                    expected_acquisition_min=metadata.get("expected_acquisition_min") or metadata.get("expected_acquisition_price"),
                    expected_acquisition_max=threshold,
                    attractive_at_or_below=threshold,
                    required_information="current lowest 5-10 PC BIN listings for exact card/version",
                    expected_information_value=Decimal(str(eiv.expected_information_value)),
                    expires_at=now + timedelta(minutes=15),
                    metadata_json={"discovery_cycle_at": now.isoformat()},
                )
                session.add(req)
                session.flush()
                create_notification(
                    session,
                    kind="manual_verification",
                    priority=req.priority,
                    title=f"VERIFY — {metadata.get('card_name', 'candidate')}",
                    message=f"Need current lowest 5-10 PC BIN listings. Attractive at or below {threshold:,}." if threshold else "Need current lowest 5-10 PC BIN listings.",
                    card_id=row.card_id,
                    candidate_id=row.id,
                    verification_request_id=req.id,
                    expires_at=req.expires_at,
                )

    session.flush()
    return rows
