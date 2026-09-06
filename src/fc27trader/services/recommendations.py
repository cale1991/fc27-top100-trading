from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from fc27trader.db.models import RecommendationLedger


def record_recommendation(session: Session, *, decision_at: datetime, card_id, market_segment_id, action: str,
                          input_cutoff_at: datetime, candidate_id=None, acquisition_min=None, acquisition_max=None,
                          target_exit_min=None, target_exit_max=None, expected_net_profit=None,
                          expected_holding_seconds=None, confidence=None, available_coin_balance=None,
                          model_version=None, strategy_version=None, evidence=None, source_observation_ids=None) -> RecommendationLedger:
    row=RecommendationLedger(recorded_at=datetime.now(UTC), decision_at=decision_at, card_id=card_id,
        market_segment_id=market_segment_id, candidate_id=candidate_id, action=action,
        acquisition_min=acquisition_min, acquisition_max=acquisition_max, target_exit_min=target_exit_min,
        target_exit_max=target_exit_max, expected_net_profit=expected_net_profit, expected_holding_seconds=expected_holding_seconds,
        confidence=Decimal(str(confidence)) if confidence is not None else None, available_coin_balance=available_coin_balance,
        model_version=model_version, strategy_version=strategy_version, input_cutoff_at=input_cutoff_at,
        evidence_json=evidence or {}, source_observation_ids_json=source_observation_ids or [], user_acted=None,
        outcome_json={}, metadata_json={})
    session.add(row); session.flush(); return row
