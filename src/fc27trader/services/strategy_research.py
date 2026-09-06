from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import yaml
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fc27trader.db.models import (
    StrategyAlias,
    StrategyCycleAssessment,
    StrategyEvidence,
    StrategyLibrary,
)
from fc27trader.strategy.decay import cycle_weight


def _dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    text = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _load(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def seed_strategy_library(
    session: Session,
    *,
    definitions_path: str | Path = "config/strategies.yaml",
    evidence_path: str | Path = "config/strategy_research_seed.yaml",
    structural_path: str | Path = "config/strategy_structural_changes.yaml",
) -> dict:
    """Idempotently seed definitions and qualitative research evidence.

    Qualitative reseeding never overwrites a measured strategy status.
    """
    now = datetime.now(UTC)
    definitions = _load(definitions_path).get("strategies", [])
    created = 0
    for item in definitions:
        row = session.scalar(select(StrategyLibrary).where(StrategyLibrary.slug == item["slug"]))
        if row is None:
            row = StrategyLibrary(
                slug=item["slug"], canonical_name=item["name"], explanation=item.get("explanation", ""),
                mechanism=item.get("mechanism", ""), created_at=now, updated_at=now,
                evidence_class="INCONCLUSIVE", viability_status="source_only_unmeasured",
                measured_status_locked=False, metadata_json={},
            )
            session.add(row); session.flush(); created += 1
        row.canonical_name = item["name"]
        row.explanation = item.get("explanation", "")
        row.mechanism = item.get("mechanism", "")
        row.applicable_card_categories_json = item.get("card_categories", [])
        row.applicable_market_regimes_json = item.get("market_regimes", [])
        row.catalysts_json = item.get("catalysts", [])
        row.ideal_entry_conditions_json = item.get("rule", {})
        row.exit_logic = item.get("exit_logic")
        row.invalidation_conditions = item.get("invalidation_conditions")
        row.typical_capital_requirement_json = item.get("typical_capital_requirement", {}) or {}
        row.scalability_capacity_json = item.get("scalability_capacity", {}) or {}
        row.expected_holding_period_json = item.get("expected_holding_period", {}) or {}
        row.liquidity_characteristics = item.get("liquidity_characteristics")
        row.ea_tax_sensitivity = item.get("ea_tax_sensitivity")
        row.ea_intervention_risk = item.get("ea_intervention_risk")
        row.updated_at = now
        for alias in item.get("aliases", []):
            exists = session.scalar(select(StrategyAlias).where(StrategyAlias.strategy_id == row.id, StrategyAlias.alias == alias))
            if exists is None:
                session.add(StrategyAlias(strategy_id=row.id, alias=alias, terminology_source="community", metadata_json={}))
    session.flush()

    by_slug = {x.slug: x for x in session.scalars(select(StrategyLibrary)).all()}
    evidence_cfg = _load(evidence_path)
    evidence_added = 0
    for src in evidence_cfg.get("sources", []):
        for slug in src.get("strategies", []):
            strategy = by_slug.get(slug)
            if strategy is None:
                continue
            url = str(src.get("url", ""))
            existing = session.scalar(
                select(StrategyEvidence).where(
                    StrategyEvidence.strategy_id == strategy.id,
                    StrategyEvidence.source_url == url,
                    StrategyEvidence.evidence_type == src.get("evidence_type", "source_evidence"),
                )
            )
            if existing is not None:
                continue
            direction = src.get("direction", "supporting")
            session.add(
                StrategyEvidence(
                    strategy_id=strategy.id,
                    game_cycle=src.get("game_cycle", "unknown"),
                    source_kind=src.get("source_kind", "public_web"),
                    source_title=src.get("title"),
                    source_url=url,
                    author=src.get("author"),
                    published_at=_dt(src.get("published_at")),
                    recorded_at=now,
                    evidence_type=src.get("evidence_type", "source_evidence"),
                    evidence_direction=direction,
                    quality_score=Decimal(str(src.get("quality_score"))) if src.get("quality_score") is not None else None,
                    notes=src.get("notes"),
                    metadata_json={"research_state": evidence_cfg.get("research_state")},
                )
            )
            evidence_added += 1
    session.flush()

    # Qualitative classification tops out at STRONG EVIDENCE and cannot overwrite measured state.
    for strategy in by_slug.values():
        if strategy.measured_status_locked:
            continue
        rows = list(session.scalars(select(StrategyEvidence).where(StrategyEvidence.strategy_id == strategy.id)))
        if not rows:
            strategy.evidence_class = "INCONCLUSIVE"
            strategy.viability_status = "source_only_unmeasured"
            continue
        supporting = [r for r in rows if r.evidence_direction not in {"contradicts", "negative"}]
        contradicting = [r for r in rows if r.evidence_direction in {"contradicts", "negative"}]
        quality = sum(float(r.quality_score or 0) for r in supporting)
        cycles = sorted({r.game_cycle for r in rows})
        strategy.first_observed_cycle = cycles[0] if cycles else None
        strategy.last_observed_cycle = cycles[-1] if cycles else None
        if len(supporting) >= 3 and quality >= 2.0:
            strategy.evidence_class = "STRONG EVIDENCE"
        elif supporting:
            strategy.evidence_class = "PLAUSIBLE"
        else:
            strategy.evidence_class = "INCONCLUSIVE"
        strategy.viability_status = "mixed_evidence_unmeasured" if contradicting else "source_only_unmeasured"

    structural_cfg = _load(structural_path)
    structural_added = 0
    for change in structural_cfg.get("changes", []):
        for slug in change.get("strategies", []):
            strategy = by_slug.get(slug)
            if not strategy:
                continue
            cycle = change["game_cycle"]
            row = session.scalar(select(StrategyCycleAssessment).where(
                StrategyCycleAssessment.strategy_id == strategy.id,
                StrategyCycleAssessment.game_cycle == cycle,
                StrategyCycleAssessment.platform == "pc",
            ))
            diff = float(change.get("difference_score", 0.0))
            if row is None:
                row = StrategyCycleAssessment(
                    strategy_id=strategy.id, game_cycle=cycle, platform="pc", assessed_at=now,
                    evidence_weight=Decimal(str(cycle_weight(cycle))),
                    structural_difference_score=Decimal(str(diff)),
                    decay_risk=Decimal(str(diff * (1.0 - cycle_weight(cycle) * 0.25))),
                    viability_status="structural_prior_only",
                    reason=change.get("note"),
                    metadata_json={"key": change.get("key"), "source": change.get("source")},
                )
                session.add(row); structural_added += 1
            else:
                row.assessed_at = now
                row.evidence_weight = Decimal(str(cycle_weight(cycle)))
                row.structural_difference_score = Decimal(str(diff))
                row.reason = change.get("note")
                row.metadata_json = {"key": change.get("key"), "source": change.get("source")}
    session.flush()
    return {"strategies": len(by_slug), "created": created, "evidence_added": evidence_added, "structural_added": structural_added}
