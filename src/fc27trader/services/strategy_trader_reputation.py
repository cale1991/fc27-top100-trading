from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from math import sqrt
from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.db.models import (
    CommunitySignal,
    CommunitySignalOutcome,
    CommunitySignalStrategyLink,
    StrategyLibrary,
    StrategyTraderPerformance,
)


def _mean(values):
    return sum(values) / len(values) if values else None


def recalculate_strategy_trader_reputation(session: Session) -> int:
    links = list(session.execute(
        select(CommunitySignalStrategyLink.strategy_id, CommunitySignal.trader_id)
        .join(CommunitySignal, CommunitySignal.id == CommunitySignalStrategyLink.signal_id)
        .where(CommunitySignal.trader_id.is_not(None))
        .distinct()
    ))
    written = 0
    now = datetime.now(UTC)
    for strategy_id, trader_id in links:
        rows = list(session.execute(
            select(CommunitySignal, CommunitySignalOutcome)
            .join(CommunitySignalStrategyLink, CommunitySignalStrategyLink.signal_id == CommunitySignal.id)
            .join(CommunitySignalOutcome, CommunitySignalOutcome.signal_id == CommunitySignal.id)
            .where(CommunitySignalStrategyLink.strategy_id == strategy_id, CommunitySignal.trader_id == trader_id)
            .order_by(CommunitySignalOutcome.evaluated_at.asc())
        ))
        if not rows:
            continue
        outcomes = [o for _, o in rows]
        returns = [float(o.return_pct) for o in outcomes if o.return_pct is not None]
        alphas = [float(o.alpha_pct) for o in outcomes if o.alpha_pct is not None]
        drawdowns = [float(o.max_drawdown_pct) for o in outcomes if o.max_drawdown_pct is not None]
        timing = [float(o.timing_quality) for o in outcomes if o.timing_quality is not None]
        holding = [o.holding_seconds for o in outcomes if o.holding_seconds is not None]
        directional = [bool(o.directional_correct) for o in outcomes if o.directional_correct is not None]
        profitable = [bool(o.profitable_after_tax) for o in outcomes if o.profitable_after_tax is not None]
        n = len(outcomes)
        sample_conf = min(1.0, sqrt(n / 30.0))
        dir_acc = _mean([1.0 if x else 0.0 for x in directional])
        profit_rate = _mean([1.0 if x else 0.0 for x in profitable])
        recent = outcomes[-min(10, n):]
        recent_rate = _mean([1.0 if bool(o.profitable_after_tax) else 0.0 for o in recent if o.profitable_after_tax is not None]) or 0.5
        score = ((profit_rate or 0.5) * 0.35 + (dir_acc or 0.5) * 0.20 + min(1.0, max(0.0, (_mean(alphas) or 0.0) / 0.10 + 0.5)) * 0.20 + (_mean(timing) or 0.5) * 0.10 + recent_rate * 0.15) * sample_conf
        row = StrategyTraderPerformance(
            strategy_id=strategy_id, trader_id=trader_id, calculated_at=now, sample_size=n,
            directional_accuracy=Decimal(str(dir_acc)) if dir_acc is not None else None,
            profitable_after_tax_rate=Decimal(str(profit_rate)) if profit_rate is not None else None,
            average_return_pct=Decimal(str(_mean(returns))) if returns else None,
            median_return_pct=Decimal(str(median(returns))) if returns else None,
            average_alpha_pct=Decimal(str(_mean(alphas))) if alphas else None,
            max_drawdown_pct=Decimal(str(max(drawdowns))) if drawdowns else None,
            timing_quality=Decimal(str(_mean(timing))) if timing else None,
            average_holding_seconds=int(_mean(holding)) if holding else None,
            recent_form_score=Decimal(str(recent_rate)), sample_confidence=Decimal(str(sample_conf)),
            reputation_score=Decimal(str(score)), category_metrics_json={}, horizon_metrics_json={}, metadata_json={},
        )
        session.add(row); written += 1
    session.flush()
    return written
