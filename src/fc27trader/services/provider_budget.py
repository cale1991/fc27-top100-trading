from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.db.models import ProviderBudgetState


def upsert_provider_budget(session: Session, *, provider_key: str, budget_period: str, access_mode: str,
                           request_limit: int | None = None, requests_remaining: int | None = None,
                           credits_limit: float | None = None, credits_used: float = 0,
                           cost_per_credit: float | None = None, estimated_daily_cost: float | None = None,
                           estimated_monthly_cost: float | None = None, resets_at=None, priority: int = 100,
                           metadata: dict | None = None) -> ProviderBudgetState:
    row = session.scalar(select(ProviderBudgetState).where(
        ProviderBudgetState.provider_key == provider_key,
        ProviderBudgetState.budget_period == budget_period,
    ))
    if row is None:
        row = ProviderBudgetState(provider_key=provider_key, budget_period=budget_period, access_mode=access_mode,
            requests_used=0, credits_used=Decimal("0"), updated_at=datetime.now(UTC), metadata_json={})
        session.add(row)
    row.access_mode=access_mode; row.request_limit=request_limit; row.requests_remaining=requests_remaining
    row.credits_limit=Decimal(str(credits_limit)) if credits_limit is not None else None
    row.credits_used=Decimal(str(credits_used)); row.cost_per_credit=Decimal(str(cost_per_credit)) if cost_per_credit is not None else None
    row.estimated_daily_cost=Decimal(str(estimated_daily_cost)) if estimated_daily_cost is not None else None
    row.estimated_monthly_cost=Decimal(str(estimated_monthly_cost)) if estimated_monthly_cost is not None else None
    row.resets_at=resets_at; row.priority=priority; row.updated_at=datetime.now(UTC)
    row.metadata_json={**(row.metadata_json or {}), **(metadata or {})}
    session.flush(); return row


def can_spend_request(row: ProviderBudgetState | None, *, credit_cost: float = 0) -> bool:
    if row is None: return True
    if row.requests_remaining is not None and row.requests_remaining <= 0: return False
    if row.credits_limit is not None and row.credits_used + Decimal(str(credit_cost)) > row.credits_limit: return False
    return True


def record_provider_request_usage(
    session: Session,
    *,
    provider_key: str,
    budget_period: str = "monthly",
    access_mode: str = "HOT_SET",
    credit_cost: float = 0,
    requests_delta: int = 1,
    requests_remaining: int | None = None,
    credits_remaining: float | None = None,
    metadata: dict | None = None,
) -> ProviderBudgetState:
    """Increment provider usage without fabricating a quota when the vendor does not expose one."""
    row = session.scalar(select(ProviderBudgetState).where(
        ProviderBudgetState.provider_key == provider_key,
        ProviderBudgetState.budget_period == budget_period,
    ))
    if row is None:
        row = ProviderBudgetState(
            provider_key=provider_key,
            budget_period=budget_period,
            access_mode=access_mode,
            requests_used=0,
            credits_used=Decimal("0"),
            updated_at=datetime.now(UTC),
            metadata_json={},
        )
        session.add(row)
    row.access_mode = access_mode
    row.requests_used = int(row.requests_used or 0) + int(requests_delta)
    if requests_remaining is not None:
        row.requests_remaining = requests_remaining
    row.credits_used = Decimal(str(row.credits_used or 0)) + Decimal(str(credit_cost))
    if credits_remaining is not None:
        row.metadata_json = {**(row.metadata_json or {}), "credits_remaining_reported": credits_remaining}
    row.updated_at = datetime.now(UTC)
    row.metadata_json = {**(row.metadata_json or {}), **(metadata or {})}
    session.flush()
    return row
