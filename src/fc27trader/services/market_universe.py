from __future__ import annotations

from datetime import UTC, datetime
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from fc27trader.db.models import Prediction, ReferencePriceObservation
from fc27trader.opportunity.models import OpportunityInputs


def build_observable_market_inputs(session: Session, *, limit: int = 20000) -> list[OpportunityInputs]:
    """Build the broadest practical PC candidate input set from current stored observations.

    This is deliberately driven by what the collectors can currently observe. It is not a
    watchlist and has no fixed card IDs. Latest model predictions enrich rows when available;
    cards without enough evidence can remain unranked until data/model support improves.
    """
    latest_ref = (
        select(
            ReferencePriceObservation.card_id.label("card_id"),
            func.max(ReferencePriceObservation.observed_at).label("max_observed_at"),
        )
        .where(ReferencePriceObservation.platform == "pc")
        .group_by(ReferencePriceObservation.card_id)
        .subquery()
    )
    refs = list(
        session.scalars(
            select(ReferencePriceObservation)
            .join(
                latest_ref,
                and_(
                    ReferencePriceObservation.card_id == latest_ref.c.card_id,
                    ReferencePriceObservation.observed_at == latest_ref.c.max_observed_at,
                ),
            )
            .order_by(ReferencePriceObservation.observed_at.desc())
            .limit(limit)
        )
    )

    reference_evidence = {
        card_id: {"count": int(count), "providers": int(providers)}
        for card_id, count, providers in session.execute(
            select(
                ReferencePriceObservation.card_id,
                func.count(ReferencePriceObservation.id),
                func.count(func.distinct(ReferencePriceObservation.source_id)),
            )
            .where(ReferencePriceObservation.platform == "pc")
            .group_by(ReferencePriceObservation.card_id)
        )
    }

    latest_pred = (
        select(Prediction.card_id.label("card_id"), func.max(Prediction.generated_at).label("max_generated_at"))
        .where(Prediction.platform == "pc")
        .group_by(Prediction.card_id)
        .subquery()
    )
    predictions = list(
        session.scalars(
            select(Prediction).join(
                latest_pred,
                and_(Prediction.card_id == latest_pred.c.card_id, Prediction.generated_at == latest_pred.c.max_generated_at),
            )
        )
    )
    pred_by_card = {p.card_id: p for p in predictions}
    now = datetime.now(UTC)
    result: list[OpportunityInputs] = []
    for ref in refs:
        pred = pred_by_card.get(ref.card_id)
        payload = (pred.payload_json or {}) if pred else {}
        provider_anchor = ref.provider_timestamp or ref.observed_at
        age_seconds = max(0.0, (now - provider_anchor).total_seconds())
        uncertainty = float(ref.uncertainty_pct) if ref.uncertainty_pct is not None else None
        expected_net = pred.expected_net_profit if pred else payload.get("expected_net_profit")
        holding = pred.expected_time_to_sale_seconds if pred else payload.get("expected_holding_seconds")
        profit_per_hour = float(pred.expected_profit_per_hour) if pred and pred.expected_profit_per_hour is not None else payload.get("expected_profit_per_hour")
        evidence = reference_evidence.get(ref.card_id, {"count": 0, "providers": 0})
        modeled_trade_evidence = bool(
            pred is not None
            and expected_net is not None
            and payload.get("acquisition_probability") is not None
            and (
                (pred.profitable_exit_probability is not None)
                or payload.get("profitable_exit_probability") is not None
            )
        )
        metadata = {
            **payload,
            "reference_observation_id": ref.id,
            "reference_price": ref.price,
            "real_reference_observation_count": evidence["count"],
            "real_reference_provider_count": evidence["providers"],
            # Phase 1 refuses to turn reference anchors or source-only strategy priors
            # into invented BUY signals. This becomes true only when an actual measured
            # trade model/rule has sufficient timestamped evidence.
            "production_evidence_sufficient": modeled_trade_evidence and evidence["count"] >= 3,
            "production_evidence_reason": (
                "measured_trade_inputs_present" if modeled_trade_evidence and evidence["count"] >= 3
                else "collecting_fc26_real_evidence"
            ),
        }
        result.append(
            OpportunityInputs(
                card_id=str(ref.card_id),
                observed_at=now,
                reference_price=ref.price,
                reference_age_seconds=age_seconds,
                reference_uncertainty_pct=uncertainty,
                expected_net_profit=float(expected_net) if expected_net is not None else None,
                acquisition_probability=payload.get("acquisition_probability"),
                expected_discount_to_reference=payload.get("expected_discount_to_reference"),
                profitable_exit_probability=(float(pred.profitable_exit_probability) if pred and pred.profitable_exit_probability is not None else payload.get("profitable_exit_probability")),
                liquidity_score=payload.get("liquidity_score"),
                sell_through_rate=payload.get("sell_through_rate"),
                expected_holding_seconds=float(holding) if holding is not None else None,
                expected_profit_per_hour=profit_per_hour,
                position_capacity_coins=float(pred.max_position_size) if pred and pred.max_position_size is not None else payload.get("position_capacity_coins"),
                volatility=payload.get("volatility"),
                downside_risk=float(pred.downside_risk) if pred and pred.downside_risk is not None else payload.get("downside_risk"),
                ea_tax=payload.get("ea_tax", 0.05),
                catalyst_score=payload.get("catalyst_score"),
                ea_intervention_risk=payload.get("ea_intervention_risk"),
                opportunity_cost=payload.get("opportunity_cost"),
                community_intelligence_score=payload.get("community_intelligence_score"),
                historical_analogue_score=payload.get("historical_analogue_score"),
                rapid_movement_score=payload.get("rapid_movement_score"),
                unusual_volume_score=payload.get("unusual_volume_score"),
                metadata=metadata,
            )
        )
    # Historical strategy recognition enriches the same broad observable universe;
    # it never filters cards into a fixed playbook/watchlist.
    from fc27trader.services.strategy_intelligence import enrich_opportunity_inputs
    return enrich_opportunity_inputs(session, result)
