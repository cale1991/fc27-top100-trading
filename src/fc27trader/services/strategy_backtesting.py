from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.db.models import (
    ShadowExecutionAttempt,
    ShadowOrder,
    ShadowTrade,
    StrategyBacktestRun,
    StrategyLibrary,
    StrategyPerformanceSnapshot,
)
from fc27trader.strategy.backtest import AcquisitionAttempt, TradeOutcome, evaluate_strategy


def _classify_measured(metrics: dict) -> tuple[str, str]:
    n = int(metrics.get("sample_size") or 0)
    hit = metrics.get("hit_rate")
    total = metrics.get("total_net_transfer_profit")
    if n < 10:
        return "INCONCLUSIVE", "measured_insufficient_sample"
    if total is not None and total < 0 and n >= 20:
        return "OUTDATED", "measured_negative"
    if n >= 50 and hit is not None and hit >= 0.58 and (total or 0) > 0:
        return "PROVEN / REPEATED", "measured_viable"
    if n >= 25 and hit is not None and hit >= 0.54 and (total or 0) > 0:
        return "STRONG EVIDENCE", "measured_promising"
    return "INCONCLUSIVE", "measured_mixed"


def run_strategy_backtest(session: Session, strategy: StrategyLibrary, *, game_cycle: str = "FC26", platform: str = "pc") -> dict:
    started = datetime.now(UTC)
    trade_rows = list(session.scalars(
        select(ShadowTrade)
        .where(ShadowTrade.strategy_key == strategy.slug, ShadowTrade.closed_at.is_not(None), ShadowTrade.realized_profit.is_not(None))
        .order_by(ShadowTrade.closed_at.asc())
    ))
    order_ids = list(session.scalars(select(ShadowOrder.id).where(ShadowOrder.strategy_key == strategy.slug)))
    attempt_rows = list(session.scalars(select(ShadowExecutionAttempt).where(ShadowExecutionAttempt.order_id.in_(order_ids)))) if order_ids else []

    trades = [
        TradeOutcome(
            net_profit=float(x.realized_profit or 0),
            capital=float(x.average_buy_price * x.quantity),
            holding_seconds=float(x.holding_seconds or 0),
            return_pct=(float(x.realized_profit or 0) / max(1, x.average_buy_price * x.quantity)),
        )
        for x in trade_rows
    ]
    attempts = [
        AcquisitionAttempt(
            acquired=(x.filled_quantity or 0) > 0,
            delay_seconds=float(x.realized_acquisition_delay_seconds) if x.realized_acquisition_delay_seconds is not None else None,
            execution_quality=float(x.execution_quality_score) if x.execution_quality_score is not None else None,
        )
        for x in attempt_rows
    ]
    metrics = evaluate_strategy(trades, attempts)
    run = StrategyBacktestRun(
        strategy_id=strategy.id, game_cycle=game_cycle, platform=platform, started_at=started,
        finished_at=datetime.now(UTC), status=metrics["status"], sample_size=len(trades),
        acquisition_attempt_sample_size=len(attempts), code_version="strategy-intelligence-v1",
        config_json={"source": "shadow_trades", "execution_attempt_source": "shadow_execution_attempts"},
        metrics_json=metrics, metadata_json={},
    )
    session.add(run); session.flush()
    if not trades:
        return {"strategy": strategy.slug, "status": "insufficient_data", "sample_size": 0, "snapshot_written": False}

    def dec(key):
        v = metrics.get(key)
        return Decimal(str(v)) if v is not None else None

    snapshot = StrategyPerformanceSnapshot(
        strategy_id=strategy.id, backtest_run_id=run.id, game_cycle=game_cycle, platform=platform,
        calculated_at=datetime.now(UTC), sample_size=len(trades), acquisition_attempt_sample_size=len(attempts),
        total_net_transfer_profit=int(round(metrics["total_net_transfer_profit"])), roi=dec("roi"),
        profit_per_hour=dec("profit_per_hour"), profit_per_deployed_million=dec("profit_per_deployed_million"),
        capital_turnover=dec("capital_turnover"), hit_rate=dec("hit_rate"), max_drawdown=dec("max_drawdown"),
        acquisition_probability=dec("acquisition_probability"), profitable_exit_probability=dec("profitable_exit_probability"),
        median_return_pct=dec("median_return_pct"), median_holding_seconds=int(metrics["median_holding_seconds"]) if metrics.get("median_holding_seconds") is not None else None,
        liquidity_score=dec("liquidity_score"), position_capacity_coins=None, confidence=dec("confidence"),
        regime_metrics_json={}, event_metrics_json={}, metadata_json={},
    )
    session.add(snapshot)
    evidence_class, viability = _classify_measured(metrics)
    strategy.evidence_class = evidence_class
    strategy.viability_status = viability
    strategy.measured_status_locked = True
    strategy.updated_at = datetime.now(UTC)
    session.flush()
    return {"strategy": strategy.slug, "status": "measured", "sample_size": len(trades), "snapshot_written": True}


def refresh_strategy_backtests(session: Session, *, game_cycle: str = "FC26") -> list[dict]:
    results = []
    for strategy in session.scalars(select(StrategyLibrary).order_by(StrategyLibrary.slug.asc())).all():
        # Refresh only when labeled closed-trade sample grew since the latest run.
        current_n = session.scalar(select(ShadowTrade).where(
            ShadowTrade.strategy_key == strategy.slug, ShadowTrade.closed_at.is_not(None), ShadowTrade.realized_profit.is_not(None)
        ).with_only_columns(__import__('sqlalchemy').func.count())) or 0
        latest = session.scalar(select(StrategyBacktestRun).where(
            StrategyBacktestRun.strategy_id == strategy.id, StrategyBacktestRun.game_cycle == game_cycle
        ).order_by(StrategyBacktestRun.finished_at.desc()).limit(1))
        if latest is not None and latest.sample_size >= current_n:
            continue
        results.append(run_strategy_backtest(session, strategy, game_cycle=game_cycle))
    return results
