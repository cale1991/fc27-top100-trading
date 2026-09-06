from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.community.scoring import TrackedCall, score_trader
from fc27trader.db.models import CommunitySignal, CommunitySignalOutcome, CommunityTrader, TraderReputationSnapshot


def recalculate_trader_reputation(session: Session) -> int:
    traders = list(session.scalars(select(CommunityTrader).where(CommunityTrader.enabled.is_(True))))
    written = 0
    for trader in traders:
        rows = session.execute(
            select(CommunitySignal, CommunitySignalOutcome)
            .join(CommunitySignalOutcome, CommunitySignalOutcome.signal_id == CommunitySignal.id)
            .where(CommunitySignal.trader_id == trader.id)
        ).all()
        calls = [
            TrackedCall(
                occurred_at=signal.extracted_at,
                category=signal.category_key,
                horizon_seconds=signal.horizon_seconds,
                directional_correct=outcome.directional_correct,
                profitable_after_tax=outcome.profitable_after_tax,
                return_pct=float(outcome.return_pct) if outcome.return_pct is not None else None,
                benchmark_return_pct=float(outcome.benchmark_return_pct) if outcome.benchmark_return_pct is not None else None,
                max_drawdown_pct=float(outcome.max_drawdown_pct) if outcome.max_drawdown_pct is not None else None,
                timing_quality=float(outcome.timing_quality) if outcome.timing_quality is not None else None,
                holding_seconds=outcome.holding_seconds,
            )
            for signal, outcome in rows
        ]
        score = score_trader(calls)
        session.add(
            TraderReputationSnapshot(
                trader_id=trader.id,
                calculated_at=datetime.now(UTC),
                sample_size=score.sample_size,
                directional_accuracy=Decimal(str(score.directional_accuracy)) if score.directional_accuracy is not None else None,
                profitable_after_tax_rate=Decimal(str(score.profitable_after_tax_rate)) if score.profitable_after_tax_rate is not None else None,
                average_return_pct=Decimal(str(score.average_return_pct)) if score.average_return_pct is not None else None,
                median_return_pct=Decimal(str(score.median_return_pct)) if score.median_return_pct is not None else None,
                average_alpha_pct=Decimal(str(score.average_alpha_pct)) if score.average_alpha_pct is not None else None,
                max_drawdown_pct=Decimal(str(score.max_drawdown_pct)) if score.max_drawdown_pct is not None else None,
                average_drawdown_pct=Decimal(str(score.average_drawdown_pct)) if score.average_drawdown_pct is not None else None,
                timing_quality=Decimal(str(score.timing_quality)) if score.timing_quality is not None else None,
                average_holding_seconds=score.average_holding_seconds,
                recent_form_score=Decimal(str(score.recent_form_score)) if score.recent_form_score is not None else None,
                sample_confidence=Decimal(str(score.sample_confidence)),
                reputation_score=Decimal(str(score.reputation_score)) if score.reputation_score is not None else None,
                category_metrics_json=score.category_metrics,
                horizon_metrics_json=score.horizon_metrics,
            )
        )
        written += 1
    session.flush()
    return written
