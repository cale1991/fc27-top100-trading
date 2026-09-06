from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc, func, select

from fc27trader.db.models import (
    Card,
    OpportunityCandidate,
    OpportunityStrategyMatch,
    StrategyCycleAssessment,
    StrategyDiscoveryCandidate,
    StrategyEvidence,
    StrategyLibrary,
    StrategyPerformanceSnapshot,
    StrategyTraderPerformance,
    CommunityTrader,
)
from fc27trader.db.session import SessionLocal

router = APIRouter(prefix="/strategies", tags=["strategies"])


def _num(v):
    return float(v) if isinstance(v, Decimal) else v


def _latest_perf(session, sid):
    return session.scalar(select(StrategyPerformanceSnapshot).where(StrategyPerformanceSnapshot.strategy_id == sid).order_by(StrategyPerformanceSnapshot.calculated_at.desc()).limit(1))


def _summary(session, s: StrategyLibrary) -> dict:
    perf = _latest_perf(session, s.id)
    evidence_count = session.scalar(select(func.count()).select_from(StrategyEvidence).where(StrategyEvidence.strategy_id == s.id)) or 0
    active = session.scalar(select(func.count()).select_from(OpportunityStrategyMatch).join(OpportunityCandidate, OpportunityCandidate.id == OpportunityStrategyMatch.candidate_id).where(OpportunityStrategyMatch.strategy_id == s.id, OpportunityCandidate.status != "superseded")) or 0
    return {
        "slug": s.slug, "name": s.canonical_name, "explanation": s.explanation,
        "evidence_class": s.evidence_class, "viability_status": s.viability_status,
        "measured": bool(perf), "sample_size": perf.sample_size if perf else 0,
        "total_net_transfer_profit": perf.total_net_transfer_profit if perf else None,
        "hit_rate": _num(perf.hit_rate) if perf else None,
        "median_return_pct": _num(perf.median_return_pct) if perf else None,
        "profit_per_hour": _num(perf.profit_per_hour) if perf else None,
        "confidence": _num(perf.confidence) if perf else None,
        "evidence_count": int(evidence_count), "active_matches": int(active),
        "last_observed_cycle": s.last_observed_cycle,
    }


@router.get("")
def list_strategies(limit: int = Query(100, ge=1, le=250)) -> list[dict]:
    with SessionLocal() as session:
        rows = list(session.scalars(select(StrategyLibrary).order_by(StrategyLibrary.evidence_class.asc(), StrategyLibrary.canonical_name.asc()).limit(limit)))
        return [_summary(session, x) for x in rows]


@router.get("/active")
def active_strategy_matches(limit: int = Query(50, ge=1, le=200)) -> list[dict]:
    with SessionLocal() as session:
        rows = list(session.execute(
            select(OpportunityStrategyMatch, StrategyLibrary, OpportunityCandidate, Card)
            .join(StrategyLibrary, StrategyLibrary.id == OpportunityStrategyMatch.strategy_id)
            .join(OpportunityCandidate, OpportunityCandidate.id == OpportunityStrategyMatch.candidate_id)
            .join(Card, Card.id == OpportunityCandidate.card_id)
            .where(OpportunityCandidate.status != "superseded")
            .order_by(OpportunityStrategyMatch.similarity.desc(), OpportunityCandidate.rank.asc().nullslast())
            .limit(limit)
        ))
        return [{
            "candidate_id": str(c.id), "card_id": str(card.id), "card": card.name, "card_version": card.rarity,
            "strategy_slug": s.slug, "strategy_name": s.canonical_name,
            "similarity": _num(m.similarity), "confidence": _num(m.confidence),
            "historical_sample_size": m.historical_sample_size,
            "historical_success_rate": _num(m.historical_success_rate),
            "historical_median_net_return": _num(m.historical_median_net_return),
            "expected_holding_seconds": m.expected_holding_seconds, "decay_risk": _num(m.decay_risk),
            "current_conditions_differ": m.current_conditions_differ,
            "reasons": m.matched_reasons_json, "action": c.action, "rank": c.rank,
        } for m,s,c,card in rows]


@router.get("/discoveries")
def discoveries(limit: int = Query(50, ge=1, le=200)) -> list[dict]:
    with SessionLocal() as session:
        rows = list(session.scalars(select(StrategyDiscoveryCandidate).order_by(StrategyDiscoveryCandidate.last_seen_at.desc()).limit(limit)))
        return [{"pattern_key": x.pattern_key, "status": x.status, "sample_size": x.sample_size, "effect_size": _num(x.effect_size), "confidence": _num(x.confidence), "description": x.description, "last_seen_at": x.last_seen_at.isoformat()} for x in rows]


@router.get("/{slug}")
def strategy_detail(slug: str) -> dict:
    with SessionLocal() as session:
        s = session.scalar(select(StrategyLibrary).where(StrategyLibrary.slug == slug))
        if s is None: raise HTTPException(status_code=404, detail="strategy not found")
        evidence = list(session.scalars(select(StrategyEvidence).where(StrategyEvidence.strategy_id == s.id).order_by(StrategyEvidence.published_at.desc().nullslast(), StrategyEvidence.recorded_at.desc()).limit(200)))
        cycles = list(session.scalars(select(StrategyCycleAssessment).where(StrategyCycleAssessment.strategy_id == s.id).order_by(StrategyCycleAssessment.assessed_at.desc())))
        perfs = list(session.scalars(select(StrategyPerformanceSnapshot).where(StrategyPerformanceSnapshot.strategy_id == s.id).order_by(StrategyPerformanceSnapshot.calculated_at.desc()).limit(50)))
        traders = list(session.execute(select(StrategyTraderPerformance, CommunityTrader).join(CommunityTrader, CommunityTrader.id == StrategyTraderPerformance.trader_id).where(StrategyTraderPerformance.strategy_id == s.id).order_by(desc(StrategyTraderPerformance.reputation_score)).limit(20)))
        base = _summary(session, s)
        base.update({
            "mechanism": s.mechanism, "card_categories": s.applicable_card_categories_json,
            "market_regimes": s.applicable_market_regimes_json, "catalysts": s.catalysts_json,
            "entry_conditions": s.ideal_entry_conditions_json, "exit_logic": s.exit_logic,
            "invalidation_conditions": s.invalidation_conditions, "ea_tax_sensitivity": s.ea_tax_sensitivity,
            "ea_intervention_risk": s.ea_intervention_risk,
            "evidence": [{"cycle": e.game_cycle, "source_kind": e.source_kind, "title": e.source_title, "author": e.author, "published_at": e.published_at.isoformat() if e.published_at else None, "url": e.source_url, "direction": e.evidence_direction, "quality_score": _num(e.quality_score), "notes": e.notes} for e in evidence],
            "cycle_assessments": [{"cycle": c.game_cycle, "evidence_weight": _num(c.evidence_weight), "structural_difference_score": _num(c.structural_difference_score), "decay_risk": _num(c.decay_risk), "viability_status": c.viability_status, "reason": c.reason} for c in cycles],
            "performance_history": [{"cycle": p.game_cycle, "calculated_at": p.calculated_at.isoformat(), "sample_size": p.sample_size, "total_net_transfer_profit": p.total_net_transfer_profit, "hit_rate": _num(p.hit_rate), "roi": _num(p.roi), "profit_per_hour": _num(p.profit_per_hour), "acquisition_probability": _num(p.acquisition_probability), "confidence": _num(p.confidence)} for p in perfs],
            "trader_specialists": [{"handle": t.handle, "sample_size": p.sample_size, "reputation_score": _num(p.reputation_score), "profitable_after_tax_rate": _num(p.profitable_after_tax_rate), "average_alpha_pct": _num(p.average_alpha_pct)} for p,t in traders],
        })
        return base
