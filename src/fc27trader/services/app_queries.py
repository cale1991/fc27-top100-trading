from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from fc27trader.db.models import (
    AcquisitionOpportunityObservation,
    ActivityFeedItem,
    Card,
    CardRelationshipEdge,
    CollectorRun,
    CommunitySignal,
    CommunitySignalOutcome,
    CommunityTrader,
    ContentEvent,
    DataQualityIncident,
    EventImpact,
    ExecutionObservation,
    ManualVerificationRequest,
    ModelRun,
    MarketSegment,
    ProviderFeedEvent,
    ProviderAuditRecord,
    ProviderBudgetState,
    Notification,
    OpportunityCandidate,
    OpportunityStrategyMatch,
    PortfolioPosition,
    PortfolioTransaction,
    Prediction,
    ProviderQualification,
    ProviderHealth,
    ReferencePriceObservation,
    ServiceHeartbeat,
    Source,
    StrategyLibrary,
    TraderReputationSnapshot,
    TradingAccount,
)

from fc27trader.features.cross_market import calculate_cross_market_features
from fc27trader.services.portfolio import project_sale
from fc27trader.settings import get_settings


def _num(value):
    return float(value) if isinstance(value, Decimal) else value


def _iso(value):
    return value.isoformat() if value is not None else None


def _latest_reference(session: Session, card_id: uuid.UUID, market_segment_id=None) -> ReferencePriceObservation | None:
    return session.scalar(
        select(ReferencePriceObservation)
        .where(ReferencePriceObservation.card_id == card_id,
               *( [ReferencePriceObservation.market_segment_id == market_segment_id] if market_segment_id is not None else [ReferencePriceObservation.platform == "pc"] ),
               ReferencePriceObservation.quality_status == "VALID")
        .order_by(ReferencePriceObservation.observed_at.desc())
        .limit(1)
    )


def _latest_execution(session: Session, card_id: uuid.UUID, market_segment_id=None) -> ExecutionObservation | None:
    return session.scalar(
        select(ExecutionObservation)
        .where(ExecutionObservation.card_id == card_id,
               *( [ExecutionObservation.market_segment_id == market_segment_id] if market_segment_id is not None else [ExecutionObservation.platform == "pc"] ),
               ExecutionObservation.quality_status == "VALID")
        .order_by(ExecutionObservation.observed_at.desc())
        .limit(1)
    )


def _portfolio_executable_mark(execution: ExecutionObservation | None) -> int | None:
    """Portfolio liquidation marks come only from execution observations.

    Reference/fair-value observations are deliberately not accepted here.
    """
    return execution.lowest_bin if execution is not None else None


def _active_candidate(session: Session, card_id: uuid.UUID, market_segment_id=None) -> OpportunityCandidate | None:
    return session.scalar(
        select(OpportunityCandidate)
        .where(
            OpportunityCandidate.card_id == card_id,
            *( [OpportunityCandidate.market_segment_id == market_segment_id] if market_segment_id is not None else [OpportunityCandidate.platform == "pc"] ),
            OpportunityCandidate.status != "superseded",
        )
        .order_by(OpportunityCandidate.last_scored_at.desc())
        .limit(1)
    )


def serialize_opportunity(session: Session, row: OpportunityCandidate) -> dict[str, Any]:
    card = session.get(Card, row.card_id)
    ref = session.get(ReferencePriceObservation, row.reference_observation_id) if row.reference_observation_id else _latest_reference(session, row.card_id, row.market_segment_id)
    execution = session.get(ExecutionObservation, row.execution_observation_id) if row.execution_observation_id else _latest_execution(session, row.card_id, row.market_segment_id)
    segment = session.get(MarketSegment, row.market_segment_id) if row.market_segment_id else None
    now = datetime.now(UTC)
    ref_age = None
    if ref:
        anchor = ref.provider_timestamp or ref.observed_at
        ref_age = max(0, (now - anchor).total_seconds())
    metadata = row.metadata_json or {}
    reference_price = ref.price if ref else metadata.get("reference_price")
    target_low = row.target_sell_low or metadata.get("target_sell_low") or metadata.get("target_sell_price")
    target_high = row.target_sell_high or metadata.get("target_sell_high") or target_low
    max_buy = row.max_recommended_buy_price or metadata.get("max_recommended_buy_price") or metadata.get("max_buy_price") or row.expected_acquisition_price
    quantity = row.recommended_quantity or metadata.get("recommended_quantity") or 1
    capital = max_buy * quantity if max_buy else None
    expected_roi = _num(row.expected_roi)
    if expected_roi is None and row.expected_net_profit is not None and capital:
        expected_roi = row.expected_net_profit / capital
    confidence = _num(row.confidence_score)
    if confidence is None:
        uncertainty = _num(ref.uncertainty_pct) if ref and ref.uncertainty_pct is not None else None
        confidence = max(0.0, min(1.0, 1.0 - uncertainty)) if uncertainty is not None else None
    action = row.action or ("verify" if row.requires_manual_verification else metadata.get("action", "watch"))
    return {
        "id": str(row.id),
        "card_id": str(row.card_id),
        "card": card.name if card else "Unknown card",
        "card_version": (card.rarity if card else None) or "Unknown",
        "rating": card.rating if card else None,
        "market_segment": segment.segment_key if segment else row.platform.upper(),
        "actionable": bool(row.actionable),
        "signal_scope": row.signal_scope,
        "action": action.upper(),
        "rank": row.rank,
        "opportunity_score": _num(row.opportunity_score),
        "status": row.status,
        "reference_price": reference_price,
        "reference_source": (session.get(Source, ref.source_id).key if ref and session.get(Source, ref.source_id) else None),
        "reference_age_seconds": ref_age,
        "reference_timestamp": _iso(ref.provider_timestamp or ref.observed_at) if ref else None,
        "reference_uncertainty_pct": _num(ref.uncertainty_pct) if ref else metadata.get("reference_uncertainty_pct"),
        "latest_execution_price": execution.lowest_bin if execution else None,
        "latest_execution_at": _iso((execution.source_timestamp or execution.observed_at) if execution else None),
        "latest_execution_source": (session.get(Source, execution.source_id).key if execution and session.get(Source, execution.source_id) else None),
        "latest_execution_age_seconds": (max(0, (now - (execution.source_timestamp or execution.observed_at)).total_seconds()) if execution else None),
        "execution_confidence": _num(execution.confidence) if execution else None,
        "max_buy_price": max_buy,
        "target_sell_low": target_low,
        "target_sell_high": target_high,
        "recommended_quantity": quantity,
        "capital_required": capital,
        "expected_net_profit": row.expected_net_profit,
        "expected_roi": expected_roi,
        "expected_holding_seconds": row.expected_holding_seconds,
        "expected_profit_per_hour": _num(row.expected_profit_per_hour),
        "liquidity_score": _num(row.liquidity_score),
        "acquisition_probability": _num(row.acquisition_probability),
        "profitable_exit_probability": _num(row.profitable_exit_probability),
        "confidence": confidence,  # compatibility alias: trade/model confidence
        "trade_model_confidence": confidence,
        "ea_intervention_risk": _num(row.ea_intervention_risk),
        "main_catalyst": row.main_catalyst or metadata.get("main_catalyst") or metadata.get("catalyst"),
        "invalidation_condition": row.invalidation_condition or metadata.get("invalidation_condition"),
        "exit_logic": row.exit_logic or metadata.get("exit_logic"),
        "requires_manual_verification": row.requires_manual_verification,
        "last_scored_at": _iso(row.last_scored_at),
        "score_components": row.score_components_json or {},
    }


def list_opportunities(session: Session, limit: int = 50) -> list[dict]:
    now = datetime.now(UTC)
    rows = list(
        session.scalars(
            select(OpportunityCandidate)
            .where(
                OpportunityCandidate.status != "superseded",
                (OpportunityCandidate.expires_at.is_(None) | (OpportunityCandidate.expires_at >= now)),
            )
            .order_by(OpportunityCandidate.actionable.desc(), OpportunityCandidate.rank.asc().nullslast(), OpportunityCandidate.opportunity_score.desc())
            .limit(limit)
        )
    )
    return [serialize_opportunity(session, row) for row in rows]


def opportunity_detail(session: Session, candidate_id: uuid.UUID) -> dict | None:
    row = session.get(OpportunityCandidate, candidate_id)
    if row is None:
        return None
    base = serialize_opportunity(session, row)
    refs = list(
        session.scalars(
            select(ReferencePriceObservation)
            .where(ReferencePriceObservation.card_id == row.card_id)
            .order_by(ReferencePriceObservation.observed_at.desc())
            .limit(200)
        )
    )
    execs = list(
        session.scalars(
            select(ExecutionObservation)
            .where(ExecutionObservation.card_id == row.card_id)
            .order_by(ExecutionObservation.observed_at.desc())
            .limit(50)
        )
    )
    acquisition = list(
        session.scalars(
            select(AcquisitionOpportunityObservation)
            .where(AcquisitionOpportunityObservation.card_id == row.card_id)
            .order_by(AcquisitionOpportunityObservation.observed_at.desc())
            .limit(100)
        )
    )
    predictions = list(
        session.scalars(
            select(Prediction)
            .where(Prediction.card_id == row.card_id)
            .order_by(Prediction.generated_at.desc())
            .limit(40)
        )
    )
    impacts = list(
        session.scalars(
            select(EventImpact)
            .where(EventImpact.card_id == row.card_id)
            .order_by(EventImpact.id.desc())
            .limit(30)
        )
    )
    community = list(
        session.scalars(
            select(CommunitySignal)
            .where(CommunitySignal.card_id == row.card_id)
            .order_by(CommunitySignal.extracted_at.desc())
            .limit(30)
        )
    )
    strategy_matches = list(
        session.execute(
            select(OpportunityStrategyMatch, StrategyLibrary)
            .join(StrategyLibrary, StrategyLibrary.id == OpportunityStrategyMatch.strategy_id)
            .where(OpportunityStrategyMatch.candidate_id == row.id)
            .order_by(OpportunityStrategyMatch.similarity.desc())
            .limit(10)
        )
    )
    forecast_signs = [1 if (x.expected_net_profit or 0) > 0 else -1 if (x.expected_net_profit or 0) < 0 else 0 for x in predictions]
    model_agreement = (max(forecast_signs.count(1), forecast_signs.count(-1), forecast_signs.count(0)) / len(forecast_signs)) if forecast_signs else None
    acquisition_discounts = [_num(x.discount_to_reference) for x in acquisition if x.discount_to_reference is not None]
    acquisition_times = [x.time_to_opportunity_seconds for x in acquisition if x.time_to_opportunity_seconds is not None]
    base.update(
        {
            "model_agreement": model_agreement,
            "historical_analogues": (row.metadata_json or {}).get("historical_analogues", []),
            "acquisition_summary": {
                "sample_size": len(acquisition),
                "mean_discount_to_reference": (sum(acquisition_discounts) / len(acquisition_discounts)) if acquisition_discounts else None,
                "mean_time_to_opportunity_seconds": (sum(acquisition_times) / len(acquisition_times)) if acquisition_times else None,
            },
            "reference_history": [
                {
                    "observed_at": _iso(x.observed_at),
                    "provider_timestamp": _iso(x.provider_timestamp),
                    "price": x.price,
                    "uncertainty_pct": _num(x.uncertainty_pct),
                    "confidence": _num(x.confidence),
                    "source_id": str(x.source_id),
                }
                for x in reversed(refs)
            ],
            "execution_observations": [
                {
                    "observed_at": _iso(x.observed_at),
                    "type": x.observation_type,
                    "lowest_bin": x.lowest_bin,
                    "best_bid": x.best_bid,
                    "listing_prices": x.listing_prices_json,
                    "confidence": _num(x.confidence),
                }
                for x in execs
            ],
            "acquisition_distribution": [
                {
                    "observed_at": _iso(x.observed_at),
                    "discount_to_reference": _num(x.discount_to_reference),
                    "time_to_opportunity_seconds": x.time_to_opportunity_seconds,
                    "quantity_available": x.quantity_available,
                    "acquired": x.acquired,
                }
                for x in acquisition
            ],
            "forecasts": [
                {
                    "generated_at": _iso(x.generated_at),
                    "model": x.model_key,
                    "version": x.model_version,
                    "horizon_seconds": x.horizon_seconds,
                    "future_sell_price": x.future_sell_price,
                    "profitable_exit_probability": _num(x.profitable_exit_probability),
                    "expected_net_profit": x.expected_net_profit,
                    "downside_risk": _num(x.downside_risk),
                }
                for x in predictions
            ],
            "event_relationships": [
                {
                    "event_id": str(x.event_id),
                    "impact_type": x.impact_type,
                    "direction": x.direction,
                    "confidence": _num(x.confidence),
                    "reason": x.reason,
                }
                for x in impacts
            ],
            "community_signals": [
                {
                    "signal_id": str(x.id),
                    "trader_id": str(x.trader_id) if x.trader_id else None,
                    "direction": x.direction,
                    "quoted_entry": x.quoted_entry,
                    "target_price": x.target_price,
                    "catalyst": x.catalyst,
                    "horizon_seconds": x.horizon_seconds,
                    "preceded_market_move": x.preceded_market_move,
                }
                for x in community
            ],
            "strategy_matches": [
                {
                    "strategy_id": str(match.strategy_id),
                    "name": strategy.canonical_name,
                    "slug": strategy.slug,
                    "classification": strategy.evidence_class,
                    "similarity": _num(match.similarity),
                    "confidence": _num(match.confidence),
                    "historical_sample_size": match.historical_sample_size or 0,
                    "historical_success_rate": _num(match.historical_success_rate),
                    "historical_median_net_return": _num(match.historical_median_net_return),
                    "expected_holding_seconds": match.expected_holding_seconds,
                    "decay_risk": _num(match.decay_risk),
                    "current_conditions_differ": bool(match.current_conditions_differ),
                    "matched_reasons": match.matched_reasons_json or [],
                    "failure_conditions": match.failure_conditions_json or [],
                }
                for match, strategy in strategy_matches
            ],
        }
    )
    # Point-in-time cross-market context uses only observations known by this calculation cutoff.
    segments = {seg.segment_key: seg for seg in session.scalars(select(MarketSegment).where(MarketSegment.game_year == (session.get(Card, row.card_id).game_year if session.get(Card, row.card_id) else 26)))}
    base["cross_market_context"] = calculate_cross_market_features(
        session, card_id=row.card_id, game_year=(session.get(Card, row.card_id).game_year if session.get(Card, row.card_id) else 26),
        segments=segments, cutoff=datetime.now(UTC)
    )
    return base


def portfolio_state(session: Session, account_name: str = "main") -> dict:
    account = session.scalar(select(TradingAccount).where(TradingAccount.name == account_name))
    if account is None:
        return {"account": {"name": account_name, "current_coins": 0, "realized_profit": 0, "ea_tax_paid": 0}, "positions": []}
    rows = list(
        session.scalars(
            select(PortfolioPosition)
            .where(PortfolioPosition.account_id == account.id, PortfolioPosition.quantity > 0)
            .order_by(PortfolioPosition.urgency.desc(), PortfolioPosition.updated_at.desc())
        )
    )
    positions = []
    now = datetime.now(UTC)
    for pos in rows:
        card = session.get(Card, pos.card_id)
        ref = _latest_reference(session, pos.card_id, pos.market_segment_id)
        ex = _latest_execution(session, pos.card_id, pos.market_segment_id)
        candidate = _active_candidate(session, pos.card_id, pos.market_segment_id)
        position_segment = session.get(MarketSegment, pos.market_segment_id) if pos.market_segment_id else None
        ref_source = session.get(Source, ref.source_id) if ref else None
        ex_source = session.get(Source, ex.source_id) if ex else None

        # Reference/fair value is intentionally NOT an executable mark.
        reference_at = (ref.provider_timestamp or ref.observed_at) if ref else None
        reference_age = max(0, (now - reference_at).total_seconds()) if reference_at else None

        execution_at = (ex.source_timestamp or ex.observed_at) if ex else None
        execution_age = max(0, (now - execution_at).total_seconds()) if execution_at else None
        current_lowest_bin = _portfolio_executable_mark(ex)

        liquidation = (
            project_sale(quantity=pos.quantity, unit_price=current_lowest_bin, cost_basis=pos.total_cost_basis)
            if current_lowest_bin is not None
            else None
        )
        desired = (
            project_sale(quantity=pos.quantity, unit_price=pos.desired_listing_price, cost_basis=pos.total_cost_basis)
            if pos.desired_listing_price is not None
            else None
        )

        target_low = candidate.target_sell_low if candidate else None
        target_high = candidate.target_sell_high if candidate else None
        holding = int((now - pos.opened_at).total_seconds()) if pos.opened_at else None
        positions.append(
            {
                "position_id": str(pos.id),
                "card_id": str(pos.card_id),
                "card": card.name if card else "Unknown card",
                "card_version": (card.rarity if card else None) or "Unknown",
                "market_segment": position_segment.segment_key if position_segment else "PC",
                "quantity": pos.quantity,
                "average_acquisition_price": pos.average_acquisition_price,
                "capital_deployed": pos.total_cost_basis,

                # Reference/fair-value anchor: useful context, never assumed executable.
                "reference_price": ref.price if ref else None,
                "reference_source": ref_source.key if ref_source else None,
                "reference_at": _iso(reference_at),
                "reference_age_seconds": reference_age,
                "reference_confidence": _num(ref.confidence) if ref else None,
                "reference_uncertainty_pct": _num(ref.uncertainty_pct) if ref else None,

                # Latest execution observation / current known lowest BIN.
                "current_lowest_bin": current_lowest_bin,
                "execution_price": current_lowest_bin,  # compatibility alias
                "execution_mark_source": ex_source.key if ex_source else None,
                "execution_mark_at": _iso(execution_at),
                "execution_at": _iso(execution_at),  # compatibility alias
                "execution_mark_age_seconds": execution_age,
                "execution_observation_confidence": _num(ex.confidence) if ex else None,
                "execution_observation_type": ex.observation_type if ex else None,
                "execution_mark_listing_count": ex.listing_count if ex else None,

                "current_liquidation_profit_after_tax": liquidation.profit_after_tax if liquidation else None,
                "current_liquidation_tax": liquidation.ea_tax if liquidation else None,
                "current_unrealized_result": liquidation.profit_after_tax if liquidation else None,  # compatibility alias

                "desired_listing_price": pos.desired_listing_price,
                "projected_profit_after_tax": desired.profit_after_tax if desired else None,
                "projected_listing_tax": desired.ea_tax if desired else None,

                "expected_sell_low": target_low,
                "expected_sell_high": target_high,
                "holding_seconds": holding,
                "liquidity": _num(candidate.liquidity_score) if candidate else None,
                "trade_model_confidence": _num(candidate.confidence_score) if candidate else None,
                "current_action": (candidate.action if candidate and candidate.action else pos.current_action) or "HOLD",
                "urgency": pos.urgency,
                "original_thesis": pos.original_thesis,
                "original_catalyst": pos.original_catalyst,
                "thesis_status": pos.thesis_status,
            }
        )
    return {
        "account": {
            "id": str(account.id),
            "name": account.name,
            "current_coins": account.current_coins,
            "starting_coins": account.starting_coins,
            "realized_profit": account.realized_profit,
            "ea_tax_paid": account.ea_tax_paid,
        },
        "positions": positions,
    }

def dashboard_state(session: Session) -> dict:
    now = datetime.now(UTC)
    portfolio = portfolio_state(session)
    positions = portfolio["positions"]
    account = portfolio["account"]
    deployed = sum(p["capital_deployed"] for p in positions)
    unrealized = sum(p["current_unrealized_result"] or 0 for p in positions)
    account_id = uuid.UUID(account["id"]) if account.get("id") else None
    today_profit = 0
    week_profit = 0
    if account_id:
        day_start = datetime(now.year, now.month, now.day, tzinfo=UTC)
        week_start = day_start - timedelta(days=day_start.weekday())
        today_profit = session.scalar(
            select(func.coalesce(func.sum(PortfolioTransaction.realized_profit), 0)).where(
                PortfolioTransaction.account_id == account_id,
                PortfolioTransaction.transaction_type == "sell",
                PortfolioTransaction.occurred_at >= day_start,
            )
        ) or 0
        week_profit = session.scalar(
            select(func.coalesce(func.sum(PortfolioTransaction.realized_profit), 0)).where(
                PortfolioTransaction.account_id == account_id,
                PortfolioTransaction.transaction_type == "sell",
                PortfolioTransaction.occurred_at >= week_start,
            )
        ) or 0
    opportunities = list_opportunities(session, 8)
    verification_count = session.scalar(
        select(func.count()).select_from(ManualVerificationRequest).where(ManualVerificationRequest.status == "pending")
    ) or 0
    urgent = [p for p in positions if str(p["current_action"]).lower() in {"sell", "strong_sell", "reduce"} or p["urgency"] >= 7]
    ea_risks = [x.get("ea_intervention_risk") for x in opportunities if x.get("ea_intervention_risk") is not None]
    return {
        "coins": account.get("current_coins", 0),
        "deployed_coins": deployed,
        "available_capital": account.get("current_coins", 0),
        "realized_transfer_profit": account.get("realized_profit", 0),
        "unrealized_expected_profit": unrealized,
        "transfer_profit_today": int(today_profit),
        "transfer_profit_week": int(week_profit),
        "total_transfer_profit": account.get("realized_profit", 0),
        "leaderboard": {"rank": None, "target": "Top 100", "data_available": False},
        "market_regime": "unknown",
        "ea_intervention_risk": max(ea_risks) if ea_risks else None,
        "active_positions": len(positions),
        "verification_requests": int(verification_count),
        "urgent_positions": urgent[:5],
        "top_opportunities": opportunities,
        "generated_at": now.isoformat(),
    }


def activity_feed(session: Session, limit: int = 100) -> list[dict]:
    app_rows = list(session.scalars(select(ActivityFeedItem).order_by(ActivityFeedItem.occurred_at.desc()).limit(limit)))
    content_rows = list(session.scalars(select(ContentEvent).order_by(ContentEvent.detected_at.desc()).limit(limit)))
    items = [
        {
            "id": str(x.id),
            "at": _iso(x.occurred_at),
            "category": x.category,
            "severity": x.severity,
            "title": x.title,
            "message": x.message,
            "card_id": str(x.card_id) if x.card_id else None,
        }
        for x in app_rows
    ]
    items.extend(
        {
            "id": str(x.id),
            "at": _iso(x.detected_at),
            "category": "content",
            "severity": "info",
            "title": x.title,
            "message": x.summary,
            "evidence_class": x.evidence_class,
            "event_type": x.event_type,
        }
        for x in content_rows
    )
    items.sort(key=lambda x: x["at"] or "", reverse=True)
    return items[:limit]


def system_state(session: Session) -> dict:
    collector_rows = list(session.scalars(select(CollectorRun).order_by(CollectorRun.started_at.desc()).limit(100)))
    collectors = {}
    for row in collector_rows:
        collectors.setdefault(row.collector_key, {
            "collector": row.collector_key, "status": row.status, "started_at": _iso(row.started_at),
            "finished_at": _iso(row.finished_at), "records_written": row.records_written, "error": row.error,
        })
    provider_rows = list(session.scalars(select(ProviderQualification).order_by(ProviderQualification.evaluated_at.desc()).limit(100)))
    health_rows = list(session.scalars(select(ProviderHealth).order_by(ProviderHealth.updated_at.desc())))
    system_now = datetime.now(UTC)

    def _live_provider_age(health: ProviderHealth | None):
        if health is None: return None
        ts = health.latest_provider_timestamp or health.latest_observation_at
        if ts is None: return _num(health.latest_observation_age_seconds)
        if ts.tzinfo is None: ts = ts.replace(tzinfo=UTC)
        return max(0.0, (system_now - ts).total_seconds())

    providers: dict[str, dict] = {}
    for h in health_rows:
        key=f"{h.provider_key}:{h.provider_role}:{h.platform}"
        providers[key]={
            "provider":h.provider_key,"role":h.provider_role,"market":h.platform,
            "status":h.status or ("HEALTHY" if h.last_success_at else "DEGRADED"),
            "access_type":h.access_type,"enabled":h.enabled,
            "market_segments_supported":h.supported_segments_json or [],
            "last_success_at":_iso(h.last_success_at),"last_failure_at":_iso(h.last_error_at),"last_error":h.last_error,
            "requests":h.requests_total,"errors":h.requests_failed,"error_rate":_num(h.error_rate),
            "cards_covered":h.cards_covered,"latest_observation_age_seconds":_live_provider_age(h),
            "last_latency_ms":_num(h.last_latency_ms),"rate_limit_remaining":h.rate_limit_remaining,
            "retry_after_seconds":h.retry_after_seconds,"items_seen":h.items_seen,"items_ingested":h.items_ingested,
            "duplicates_skipped":h.duplicates_skipped,"quarantined_observations":h.quarantined_observations,
            "parsing_failures":h.parsing_failures,"normalization_failures":h.normalization_failures,
            "identity_failures":h.identity_failures,"poll_duration_ms":_num(h.last_poll_duration_ms),
            "gap_status":h.gap_status,"platform_certainty":_num(h.platform_certainty),
        }
    # Add validation metrics without overriding operational status.
    for row in provider_rows:
        matches=[v for v in providers.values() if v["provider"]==row.provider_key and v["role"]==row.role]
        for v in matches:
            v.setdefault("evaluated_at",_iso(row.evaluated_at)); v.setdefault("freshness_p95_seconds",_num(row.timestamp_age_p95_seconds)); v.setdefault("median_abs_pct_error",_num(row.median_abs_pct_error))

    settings=get_settings()
    configured=[
        ("futdb","metadata","multi",bool(settings.futdb_api_key),"FUTDB_API_KEY","DOCUMENTED_API"),
        ("futdb","reference","PC",bool(settings.futdb_api_key and settings.futdb_premium_prices_enabled),"FUTDB_API_KEY + FUTDB_PREMIUM_PRICES_ENABLED","PAID_API"),
        ("thecoinprinter","metadata","multi",bool(settings.thecoinprinter_api_key),"THECOINPRINTER_API_KEY","PAID_API"),
        ("thecoinprinter","reference","multi",bool(settings.thecoinprinter_api_key),"THECOINPRINTER_API_KEY","PAID_API"),
        ("futzip","context","UNKNOWN",True,"public RSS","PUBLIC_FEED"),
        ("futzip","content","UNKNOWN",True,"public RSS","PUBLIC_FEED"),
        ("parse_futbin","reference","multi",bool(settings.parse_futbin_enabled and settings.parse_api_key),"PARSE_API_KEY + PARSE_FUTBIN_ENABLED=true","OPTIONAL_STRUCTURED_PROVIDER"),
    ]
    for provider_key,role,market,is_configured,requirement,access in configured:
        existing=next((v for v in providers.values() if v["provider"]==provider_key and v["role"]==role),None)
        if existing:
            existing["credential_configured"]=is_configured; existing["credential_requirement"]=requirement
            if provider_key=="parse_futbin" and not settings.parse_futbin_enabled: existing["status"]="DISABLED"; existing["enabled"]=False
            elif provider_key=="parse_futbin" and settings.parse_futbin_enabled and not settings.parse_api_key: existing["status"]="NO_CREDENTIALS"
            continue
        if provider_key=="parse_futbin":
            status="DISABLED" if not settings.parse_futbin_enabled else ("CONFIGURED_NOT_TESTED" if settings.parse_api_key else "NO_CREDENTIALS")
            enabled=bool(settings.parse_futbin_enabled)
        else:
            status="CONFIGURED_NOT_TESTED" if is_configured else ("HEALTHY" if provider_key=="futzip" else "NO_CREDENTIALS")
            enabled=True
        providers[f"configured:{provider_key}:{role}"]={
            "provider":provider_key,"role":role,"market":market,"status":status,"access_type":access,"enabled":enabled,
            "market_segments_supported":(["PC","PLAYSTATION"] if provider_key=="parse_futbin" else []),
            "credential_configured":is_configured,"credential_requirement":requirement,"last_success_at":None,"last_failure_at":None,
            "last_error":None,"requests":0,"errors":0,"error_rate":None,"cards_covered":0,"latest_observation_age_seconds":None,
            "last_latency_ms":None,"rate_limit_remaining":None,"items_seen":0,"items_ingested":0,"duplicates_skipped":0,
            "quarantined_observations":0,"parsing_failures":0,"normalization_failures":0,"identity_failures":0,"gap_status":None,
            "platform_certainty":None,
        }
    models=list(session.scalars(select(ModelRun).order_by(ModelRun.run_started_at.desc()).limit(30)))
    heartbeats=list(session.scalars(select(ServiceHeartbeat).order_by(ServiceHeartbeat.last_seen_at.desc()).limit(50)))
    incidents=list(session.scalars(select(DataQualityIncident).where(DataQualityIncident.resolved_at.is_(None)).order_by(DataQualityIncident.detected_at.desc()).limit(20)))
    audits=list(session.scalars(select(ProviderAuditRecord).order_by(ProviderAuditRecord.checked_at.desc()).limit(50)))
    budgets=list(session.scalars(select(ProviderBudgetState).order_by(ProviderBudgetState.updated_at.desc()).limit(50)))
    return {
        "collectors":list(collectors.values()),"providers":list(providers.values()),
        "provider_audits":[{"provider":x.provider_key,"tier":x.tier,"integration_status":x.integration_status,"checked_at":_iso(x.checked_at),"markets":x.markets_json,"blockers":x.blockers_json} for x in audits],
        "provider_budgets":[{"provider":x.provider_key,"period":x.budget_period,"access_mode":x.access_mode,"requests_used":x.requests_used,"requests_remaining":x.requests_remaining,"credits_used":_num(x.credits_used),"estimated_daily_cost":_num(x.estimated_daily_cost),"estimated_monthly_cost":_num(x.estimated_monthly_cost),"reset_at":_iso(x.resets_at)} for x in budgets],
        "models":[{"model":x.model_key,"version":x.model_version,"status":x.status,"started_at":_iso(x.run_started_at),"finished_at":_iso(x.run_finished_at),"metrics":x.metrics_json} for x in models],
        "heartbeats":[{"service":x.service_key,"node":x.node_key,"kind":x.service_kind,"status":x.status,"last_seen_at":_iso(x.last_seen_at),"metadata":x.metadata_json} for x in heartbeats],
        "incidents":[{"severity":x.severity,"type":x.incident_type,"description":x.description,"detected_at":_iso(x.detected_at)} for x in incidents],
    }


def community_state(session: Session) -> dict:
    reps = list(session.scalars(select(TraderReputationSnapshot).order_by(TraderReputationSnapshot.calculated_at.desc()).limit(200)))
    latest: dict[uuid.UUID, TraderReputationSnapshot] = {}
    for row in reps:
        latest.setdefault(row.trader_id, row)
    leaderboard = []
    for trader_id, score in latest.items():
        trader = session.get(CommunityTrader, trader_id)
        leaderboard.append({
            "trader_id": str(trader_id),
            "handle": trader.handle if trader else "unknown",
            "platform": trader.source_platform if trader else None,
            "reputation_score": _num(score.reputation_score),
            "sample_size": score.sample_size,
            "directional_accuracy": _num(score.directional_accuracy),
            "profitable_after_tax_rate": _num(score.profitable_after_tax_rate),
            "recent_form_score": _num(score.recent_form_score),
            "category_metrics": score.category_metrics_json,
        })
    leaderboard.sort(key=lambda x: x["reputation_score"] or -1, reverse=True)
    signals = list(session.scalars(select(CommunitySignal).order_by(CommunitySignal.extracted_at.desc()).limit(100)))
    outcomes = {x.signal_id: x for x in session.scalars(select(CommunitySignalOutcome).where(CommunitySignalOutcome.signal_id.in_([s.id for s in signals]))) } if signals else {}
    consensus: dict[str, dict[str, int]] = {}
    for signal in signals:
        key = str(signal.card_id) if signal.card_id else (signal.category_key or "unknown")
        bucket = consensus.setdefault(key, {})
        bucket[signal.direction] = bucket.get(signal.direction, 0) + 1
    calls = []
    for x in signals:
        outcome = outcomes.get(x.id)
        calls.append({
            "id": str(x.id),
            "trader_id": str(x.trader_id) if x.trader_id else None,
            "card_id": str(x.card_id) if x.card_id else None,
            "category": x.category_key,
            "direction": x.direction,
            "entry": x.quoted_entry,
            "target": x.target_price,
            "catalyst": x.catalyst,
            "horizon_seconds": x.horizon_seconds,
            "preceded_market_move": x.preceded_market_move,
            "extracted_at": _iso(x.extracted_at),
            "outcome": None if outcome is None else {
                "directional_correct": outcome.directional_correct,
                "profitable_after_tax": outcome.profitable_after_tax,
                "return_pct": _num(outcome.return_pct),
                "alpha_pct": _num(outcome.alpha_pct),
                "status": outcome.outcome_status,
            },
        })
    return {
        "trader_leaderboard": leaderboard[:30],
        "important_calls": calls[:50],
        "consensus": consensus,
        "awaiting_outcome": [x for x in calls if x["outcome"] is None][:30],
        "recent_resolved": [x for x in calls if x["outcome"] is not None][:30],
    }


def card_research(session: Session, card_id: uuid.UUID) -> dict | None:
    card = session.get(Card, card_id)
    if card is None:
        return None
    segments = list(session.scalars(select(MarketSegment).where(MarketSegment.game_year == card.game_year).order_by(MarketSegment.segment_key)))
    segment_data = {}
    for seg in segments:
        refs = list(session.scalars(select(ReferencePriceObservation).where(
            ReferencePriceObservation.card_id == card_id,
            ReferencePriceObservation.market_segment_id == seg.id,
        ).order_by(ReferencePriceObservation.observed_at.desc()).limit(300)))
        execs = list(session.scalars(select(ExecutionObservation).where(
            ExecutionObservation.card_id == card_id,
            ExecutionObservation.market_segment_id == seg.id,
        ).order_by(ExecutionObservation.observed_at.desc()).limit(100)))
        segment_data[seg.segment_key] = {
            "display_name": seg.display_name,
            "executable_by_user": seg.executable_by_user,
            "reference_prices": [{
                "id": x.id, "at": _iso(x.observed_at), "provider_at": _iso(x.provider_timestamp), "price": x.price,
                "source": (session.get(Source, x.source_id).key if session.get(Source, x.source_id) else None),
                "age_seconds": _num(x.age_seconds), "confidence": _num(x.confidence), "uncertainty_pct": _num(x.uncertainty_pct),
                "quality_status": x.quality_status, "state_completeness": x.state_completeness,
                "semantics": "REFERENCE_PRICE", "raw_ingest_id": str(x.raw_ingest_id) if x.raw_ingest_id else None,
            } for x in refs],
            "execution_observations": [{
                "id": x.id, "at": _iso(x.observed_at), "source_at": _iso(x.source_timestamp), "lowest_bin": x.lowest_bin,
                "listing_prices": x.listing_prices_json, "confidence": _num(x.confidence), "type": x.observation_type,
                "quality_status": x.quality_status, "semantics": "EXECUTION_OBSERVATION",
            } for x in execs],
        }
    moves = list(session.scalars(select(ProviderFeedEvent).where(
        ProviderFeedEvent.card_id == card_id,
        ProviderFeedEvent.event_type == "MARKET_MOVE",
    ).order_by(ProviderFeedEvent.provider_timestamp.desc().nullslast(), ProviderFeedEvent.retrieved_at.desc()).limit(200)))
    content_rows = session.execute(
        select(EventImpact, ContentEvent)
        .join(ContentEvent, ContentEvent.id == EventImpact.event_id)
        .where(EventImpact.card_id == card_id)
        .order_by(ContentEvent.detected_at.desc())
        .limit(100)
    ).all()
    active = _active_candidate(session, card_id)
    return {
        "card": {"id": str(card.id), "name": card.name, "rating": card.rating, "version": card.rarity,
                 "position": card.primary_position, "league": card.league, "club": card.club, "nation": card.nation,
                 "attributes": card.attributes_json, "playstyles": card.playstyles_json, "roles": card.roles_json,
                 "image_id": card.image_id, "image_url": card.image_url, "ea_resource_id": card.ea_resource_id,
                 "game_year": card.game_year},
        "default_market_segment": "PC",
        "market_segments": segment_data,
        "market_moves": [{
            "id": str(x.id), "provider": (session.get(Source, x.source_id).key if session.get(Source, x.source_id) else None),
            "market_segment": (session.get(MarketSegment, x.market_segment_id).segment_key if x.market_segment_id and session.get(MarketSegment, x.market_segment_id) else "UNKNOWN"),
            "old_price": x.old_price, "new_price": x.new_price, "percentage_change": _num(x.percentage_change),
            "provider_timestamp": _iso(x.provider_timestamp), "retrieved_at": _iso(x.retrieved_at),
            "quality_status": x.quality_status, "semantics": x.observation_semantics,
        } for x in moves],
        "content_events": [{
            "event_id": str(event.id),
            "event_type": event.event_type,
            "evidence_class": event.evidence_class,
            "title": event.title,
            "summary": event.summary,
            "published_at": _iso(event.published_at),
            "effective_at": _iso(event.effective_at),
            "detected_at": _iso(event.detected_at),
            "source": (session.get(Source, event.source_id).key if session.get(Source, event.source_id) else None),
            "source_url": event.source_url,
            "impact_type": impact.impact_type,
            "direction": impact.direction,
            "confidence": _num(impact.confidence),
            "reason": impact.reason,
        } for impact, event in content_rows],
        "active_opportunity": serialize_opportunity(session, active) if active else None,
        "reference_warning": "Reference prices are valuation anchors. They are not guaranteed executable BIN listings. Unknown-market events are excluded from PC/console/Switch reference consensus.",
    }
