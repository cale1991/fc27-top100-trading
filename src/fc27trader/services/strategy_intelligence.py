from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
import uuid

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from fc27trader.db.models import (
    Card,
    OpportunityCandidate,
    OpportunityStrategyMatch,
    StrategyCycleAssessment,
    StrategyLibrary,
    StrategyPerformanceSnapshot,
    StrategyTraderPerformance,
)
from fc27trader.opportunity.models import OpportunityInputs
from fc27trader.strategy.features import aggregate_strategy_features
from fc27trader.strategy.matching import recognize_strategies
from fc27trader.strategy.models import StrategyContext, StrategyDefinition, StrategyMatch


def _definition(row: StrategyLibrary) -> StrategyDefinition:
    return StrategyDefinition(
        slug=row.slug,
        name=row.canonical_name,
        aliases=tuple(),
        explanation=row.explanation,
        mechanism=row.mechanism,
        card_categories=tuple(row.applicable_card_categories_json or []),
        market_regimes=tuple(row.applicable_market_regimes_json or []),
        catalysts=tuple(row.catalysts_json or []),
        rule=row.ideal_entry_conditions_json or {},
        ea_tax_sensitivity=row.ea_tax_sensitivity,
        ea_intervention_risk=row.ea_intervention_risk,
    )


def _latest_performance(session: Session, strategy_id: uuid.UUID) -> StrategyPerformanceSnapshot | None:
    return session.scalar(
        select(StrategyPerformanceSnapshot)
        .where(StrategyPerformanceSnapshot.strategy_id == strategy_id, StrategyPerformanceSnapshot.platform == "pc")
        .order_by(StrategyPerformanceSnapshot.calculated_at.desc())
        .limit(1)
    )


def _latest_cycle_assessment(session: Session, strategy_id: uuid.UUID) -> StrategyCycleAssessment | None:
    return session.scalar(
        select(StrategyCycleAssessment)
        .where(StrategyCycleAssessment.strategy_id == strategy_id, StrategyCycleAssessment.platform == "pc")
        .order_by(StrategyCycleAssessment.assessed_at.desc())
        .limit(1)
    )


def _context(session: Session, item: OpportunityInputs) -> StrategyContext:
    card = session.get(Card, uuid.UUID(item.card_id))
    meta = item.metadata or {}
    catalysts = meta.get("catalysts") or ([meta.get("main_catalyst") or meta.get("catalyst")] if meta.get("main_catalyst") or meta.get("catalyst") else [])
    category = meta.get("card_category")
    if not category and card:
        rarity = (card.rarity or "").lower()
        promo = (card.promo or "").lower()
        if "icon" in rarity: category = "icon"
        elif "hero" in rarity: category = "hero"
        elif promo or (rarity and rarity not in {"gold", "rare gold", "common gold"}): category = "promo"
        elif card.rating and card.rating >= 84: category = "fodder"
        else: category = "gold"
    return StrategyContext(
        card_id=item.card_id,
        observed_at=item.observed_at,
        card_category=category,
        market_regime=meta.get("market_regime"),
        catalysts=tuple(str(x) for x in catalysts if x),
        in_packs=(card.in_packs if card else meta.get("in_packs")),
        promo_active=bool(card.promo) if card else meta.get("promo_active"),
        price_change_1h=meta.get("price_change_1h"),
        price_change_24h=meta.get("price_change_24h"),
        liquidity_score=item.liquidity_score,
        demand_score=meta.get("demand_score") or item.catalyst_score,
        seconds_to_content=meta.get("seconds_to_content"),
        seconds_since_content=meta.get("seconds_since_content"),
        metadata=meta,
    )


def recognize_item(session: Session, item: OpportunityInputs, *, max_matches: int = 5) -> list[StrategyMatch]:
    rows = list(session.scalars(select(StrategyLibrary)))
    if not rows:
        return []
    by_slug = {r.slug: r for r in rows}
    matches = recognize_strategies(_context(session, item), [_definition(r) for r in rows], max_matches=max_matches)
    enriched: list[StrategyMatch] = []
    for match in matches:
        strategy = by_slug[match.slug]
        perf = _latest_performance(session, strategy.id)
        assessment = _latest_cycle_assessment(session, strategy.id)
        decay = float(assessment.decay_risk) if assessment and assessment.decay_risk is not None else 0.0
        enriched.append(replace(
            match,
            historical_sample_size=perf.sample_size if perf else 0,
            historical_success_rate=float(perf.hit_rate) if perf and perf.hit_rate is not None else None,
            historical_median_net_return=float(perf.median_return_pct) if perf and perf.median_return_pct is not None else None,
            expected_holding_seconds=perf.median_holding_seconds if perf else None,
            decay_risk=decay,
            structural_difference_score=(float(assessment.structural_difference_score) if assessment and assessment.structural_difference_score is not None else None),
            current_conditions_differ=match.current_conditions_differ or decay >= 0.55,
            failure_conditions=tuple(filter(None, [strategy.invalidation_conditions])),
        ))
    return enriched


def enrich_opportunity_inputs(session: Session, items: list[OpportunityInputs]) -> list[OpportunityInputs]:
    """Add strategy evidence to the broad universe without filtering any cards."""
    output: list[OpportunityInputs] = []
    for item in items:
        matches = recognize_item(session, item)
        features = aggregate_strategy_features(matches)
        metadata = dict(item.metadata or {})
        metadata["strategy_matches"] = [
            {
                "slug": m.slug, "name": m.name, "similarity": m.similarity, "confidence": m.confidence,
                "historical_sample_size": m.historical_sample_size,
                "historical_success_rate": m.historical_success_rate,
                "historical_median_net_return": m.historical_median_net_return,
                "expected_holding_seconds": m.expected_holding_seconds,
                "decay_risk": m.decay_risk,
                "current_conditions_differ": m.current_conditions_differ,
                "reasons": list(m.reasons),
                "failure_conditions": list(m.failure_conditions),
            }
            for m in matches
        ]
        output.append(replace(item, metadata=metadata, **features))
    return output


def persist_candidate_strategy_matches(session: Session, candidate: OpportunityCandidate, item: OpportunityInputs) -> int:
    matches = recognize_item(session, item)
    strategies = {x.slug: x for x in session.scalars(select(StrategyLibrary)).all()}
    count = 0
    for m in matches:
        row = OpportunityStrategyMatch(
            candidate_id=candidate.id,
            strategy_id=strategies[m.slug].id,
            matched_at=datetime.now(UTC),
            similarity=Decimal(str(m.similarity)),
            confidence=Decimal(str(m.confidence)),
            historical_sample_size=m.historical_sample_size,
            historical_success_rate=Decimal(str(m.historical_success_rate)) if m.historical_success_rate is not None else None,
            historical_median_net_return=Decimal(str(m.historical_median_net_return)) if m.historical_median_net_return is not None else None,
            expected_holding_seconds=m.expected_holding_seconds,
            decay_risk=Decimal(str(m.decay_risk)) if m.decay_risk is not None else None,
            current_conditions_differ=m.current_conditions_differ,
            matched_reasons_json=list(m.reasons),
            failure_conditions_json=list(m.failure_conditions),
            features_json={},
        )
        session.add(row); count += 1
    session.flush()
    return count


def strategy_specific_community_score(session: Session, strategy_ids: list[uuid.UUID]) -> float | None:
    if not strategy_ids:
        return None
    row = session.scalar(
        select(StrategyTraderPerformance)
        .where(StrategyTraderPerformance.strategy_id.in_(strategy_ids), StrategyTraderPerformance.sample_size > 0)
        .order_by(desc(StrategyTraderPerformance.reputation_score), desc(StrategyTraderPerformance.calculated_at))
        .limit(1)
    )
    return float(row.reputation_score) if row and row.reputation_score is not None else None


def link_community_signal_strategies(session: Session, signal, text: str, catalyst: str | None = None) -> int:
    """Lightweight mechanism link for community calls; performance weighting happens after outcomes resolve."""
    from fc27trader.db.models import CommunitySignalStrategyLink, StrategyAlias

    haystack = f"{text} {catalyst or ''}".lower()
    strategies = list(session.scalars(select(StrategyLibrary)))
    aliases = list(session.scalars(select(StrategyAlias)))
    alias_map: dict[uuid.UUID, list[str]] = {}
    for alias in aliases:
        alias_map.setdefault(alias.strategy_id, []).append(alias.alias.lower())
    count = 0
    for strategy in strategies:
        terms = [strategy.canonical_name.lower(), strategy.slug.replace('-', ' ')] + alias_map.get(strategy.id, [])
        catalysts = [str(x).replace('_', ' ').lower() for x in (strategy.catalysts_json or [])]
        matched = [t for t in terms if len(t) >= 4 and t in haystack]
        catalyst_hits = [c for c in catalysts if c and c in haystack]
        if not matched and not catalyst_hits:
            continue
        confidence = min(0.95, 0.45 + 0.15 * len(matched) + 0.08 * len(catalyst_hits))
        exists = session.scalar(select(CommunitySignalStrategyLink).where(
            CommunitySignalStrategyLink.signal_id == signal.id,
            CommunitySignalStrategyLink.strategy_id == strategy.id,
        ))
        if exists is None:
            session.add(CommunitySignalStrategyLink(
                signal_id=signal.id, strategy_id=strategy.id, linked_at=datetime.now(UTC),
                match_confidence=Decimal(str(confidence)),
                link_reason=", ".join((matched + catalyst_hits)[:4]), metadata_json={},
            ))
            count += 1
    session.flush()
    return count
