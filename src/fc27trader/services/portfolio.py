from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import math
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from fc27trader.db.models import (
    Card,
    ExecutionObservation,
    PortfolioPosition,
    PortfolioTransaction,
    TradingAccount,
)
from fc27trader.services.activity import record_activity


EA_TAX_RATE = 0.05


@dataclass(frozen=True, slots=True)
class TradeResult:
    transaction_id: uuid.UUID
    position_id: uuid.UUID
    quantity_remaining: int
    account_coins: int
    realized_profit: int
    ea_tax: int


@dataclass(frozen=True, slots=True)
class SaleProjection:
    gross: int
    ea_tax: int
    net_proceeds: int
    cost_basis: int
    profit_after_tax: int


def project_sale(*, quantity: int, unit_price: int, cost_basis: int, tax_rate: float = EA_TAX_RATE) -> SaleProjection:
    if quantity < 0 or unit_price < 0 or cost_basis < 0:
        raise ValueError("quantity, unit_price and cost_basis must be non-negative")
    gross = int(quantity) * int(unit_price)
    tax = math.floor(gross * tax_rate)
    net = gross - tax
    return SaleProjection(gross=gross, ea_tax=tax, net_proceeds=net, cost_basis=int(cost_basis), profit_after_tax=net - int(cost_basis))


def get_or_create_account(
    session: Session,
    *,
    name: str = "main",
    starting_coins: int = 0,
) -> TradingAccount:
    row = session.scalar(select(TradingAccount).where(TradingAccount.name == name))
    if row:
        return row
    now = datetime.now(UTC)
    row = TradingAccount(
        name=name,
        platform="pc",
        game_year=26,
        starting_coins=starting_coins,
        current_coins=starting_coins,
        realized_profit=0,
        ea_tax_paid=0,
        created_at=now,
        updated_at=now,
        metadata_json={},
    )
    session.add(row)
    session.flush()
    return row


def set_coin_balance(session: Session, account: TradingAccount, coins: int, *, notes: str | None = None) -> PortfolioTransaction:
    now = datetime.now(UTC)
    delta = int(coins) - int(account.current_coins)
    account.current_coins = int(coins)
    account.updated_at = now
    tx = PortfolioTransaction(
        account_id=account.id,
        position_id=None,
        card_id=None,
        transaction_type="coin_adjustment",
        occurred_at=now,
        quantity=0,
        unit_price=None,
        gross_amount=abs(delta),
        ea_tax=0,
        net_coin_flow=delta,
        cost_basis_released=0,
        realized_profit=0,
        notes=notes,
        metadata_json={},
    )
    session.add(tx)
    record_activity(
        session,
        category="portfolio",
        title="Coin balance updated",
        message=f"Available coins set to {coins:,}.",
        metadata={"delta": delta},
    )
    session.flush()
    return tx


def set_desired_listing_price(
    session: Session,
    *,
    position: PortfolioPosition,
    desired_listing_price: int | None,
) -> PortfolioPosition:
    if desired_listing_price is not None and desired_listing_price <= 0:
        raise ValueError("desired_listing_price must be positive or null")
    position.desired_listing_price = int(desired_listing_price) if desired_listing_price is not None else None
    position.updated_at = datetime.now(UTC)
    session.flush()
    return position


def _consume_observed_listings_after_purchase(
    session: Session,
    *,
    card: Card,
    unit_price: int,
    quantity: int,
    purchased_at: datetime,
    market_segment_id=None,
) -> ExecutionObservation | None:
    """Derive the remaining locally observed order book after buying a verified listing.

    The original manual execution observation stays immutable.  If the purchased price was one
    of its observed listings, a new derived observation becomes the latest local execution mark.
    Its source timestamp remains the original market-check time so the UI does not pretend the
    derived book is fresher than the evidence it came from.
    """
    latest = session.scalar(
        select(ExecutionObservation)
        .where(ExecutionObservation.card_id == card.id, ExecutionObservation.platform == "pc",
               *( [ExecutionObservation.market_segment_id == market_segment_id] if market_segment_id is not None else [] ))
        .order_by(ExecutionObservation.observed_at.desc(), ExecutionObservation.id.desc())
        .limit(1)
    )
    if latest is None:
        return None

    listings = [int(x) for x in (latest.listing_prices_json or []) if int(x) > 0]
    if not listings or unit_price not in listings:
        return None

    remaining = list(listings)
    consumed = 0
    for _ in range(quantity):
        try:
            remaining.remove(int(unit_price))
            consumed += 1
        except ValueError:
            break
    if consumed == 0:
        return None

    evidence_at = latest.source_timestamp or latest.observed_at
    metadata = dict(latest.metadata_json or {})
    metadata.update(
        {
            "derived_from_execution_observation_id": latest.id,
            "derived_reason": "observed_listing_consumed_by_manual_purchase",
            "consumed_unit_price": int(unit_price),
            "consumed_quantity": consumed,
            "original_market_observed_at": evidence_at.isoformat() if evidence_at else None,
        }
    )
    derived = ExecutionObservation(
        observed_at=purchased_at,
        source_timestamp=evidence_at,
        card_id=card.id,
        source_id=latest.source_id,
        raw_ingest_id=latest.raw_ingest_id,
        market_segment_id=market_segment_id or latest.market_segment_id,
        platform="pc",
        inserted_at=datetime.now(UTC),
        observation_type="post_purchase_remaining_listings",
        lowest_bin=min(remaining) if remaining else None,
        best_bid=latest.best_bid,
        listing_prices_json=sorted(remaining),
        listing_count=len(remaining),
        confidence=Decimal(str(latest.confidence)),
        quality_status=getattr(latest, "quality_status", "VALID"),
        expires_at=latest.expires_at,
        manual_verification_request_id=latest.manual_verification_request_id,
        metadata_json=metadata,
    )
    session.add(derived)
    session.flush()
    return derived


def record_purchase(
    session: Session,
    *,
    account: TradingAccount,
    card: Card,
    quantity: int,
    unit_price: int,
    occurred_at: datetime | None = None,
    thesis: str | None = None,
    catalyst: str | None = None,
    notes: str | None = None,
    market_segment_id=None,
) -> TradeResult:
    if quantity <= 0 or unit_price <= 0:
        raise ValueError("quantity and unit_price must be positive")
    now = occurred_at or datetime.now(UTC)
    total = quantity * unit_price
    if account.current_coins < total:
        raise ValueError("insufficient coin balance")

    pos = session.scalar(
        select(PortfolioPosition).where(
            PortfolioPosition.account_id == account.id,
            PortfolioPosition.card_id == card.id,
            *( [PortfolioPosition.market_segment_id == market_segment_id] if market_segment_id is not None else [] ),
        )
    )
    if pos is None:
        pos = PortfolioPosition(
            account_id=account.id,
            card_id=card.id,
            market_segment_id=market_segment_id,
            quantity=0,
            average_acquisition_price=0,
            total_cost_basis=0,
            desired_listing_price=None,
            opened_at=now,
            updated_at=now,
            status="open",
            urgency=0,
            original_thesis=thesis,
            original_catalyst=catalyst,
            thesis_status="active",
            metadata_json={},
        )
        session.add(pos)
        session.flush()
    elif pos.quantity == 0:
        pos.opened_at = now
        pos.original_thesis = thesis or pos.original_thesis
        pos.original_catalyst = catalyst or pos.original_catalyst
        pos.thesis_status = "active"
        pos.status = "open"

    new_cost = pos.total_cost_basis + total
    new_qty = pos.quantity + quantity
    pos.quantity = new_qty
    pos.total_cost_basis = new_cost
    pos.average_acquisition_price = round(new_cost / new_qty)
    pos.updated_at = now
    pos.status = "open"

    account.current_coins -= total
    account.updated_at = now
    tx = PortfolioTransaction(
        account_id=account.id,
        position_id=pos.id,
        market_segment_id=market_segment_id or pos.market_segment_id,
        card_id=card.id,
        transaction_type="buy",
        occurred_at=now,
        quantity=quantity,
        unit_price=unit_price,
        gross_amount=total,
        ea_tax=0,
        net_coin_flow=-total,
        cost_basis_released=0,
        realized_profit=0,
        notes=notes,
        metadata_json={},
    )
    session.add(tx)
    _consume_observed_listings_after_purchase(
        session,
        card=card,
        unit_price=unit_price,
        quantity=quantity,
        purchased_at=now,
        market_segment_id=market_segment_id or pos.market_segment_id,
    )
    record_activity(
        session,
        category="portfolio",
        title=f"Bought {card.name}",
        message=f"{quantity} × {unit_price:,} coins; deployed {total:,}.",
        card_id=card.id,
    )
    session.flush()
    return TradeResult(tx.id, pos.id, pos.quantity, account.current_coins, 0, 0)


def record_sale(
    session: Session,
    *,
    account: TradingAccount,
    card: Card,
    quantity: int,
    unit_price: int,
    occurred_at: datetime | None = None,
    notes: str | None = None,
    tax_rate: float = EA_TAX_RATE,
    market_segment_id=None,
) -> TradeResult:
    if quantity <= 0 or unit_price <= 0:
        raise ValueError("quantity and unit_price must be positive")
    pos = session.scalar(
        select(PortfolioPosition).where(
            PortfolioPosition.account_id == account.id,
            PortfolioPosition.card_id == card.id,
            *( [PortfolioPosition.market_segment_id == market_segment_id] if market_segment_id is not None else [] ),
        )
    )
    if pos is None or pos.quantity < quantity:
        raise ValueError("sale quantity exceeds open position")

    now = occurred_at or datetime.now(UTC)
    basis = pos.average_acquisition_price * quantity
    projection = project_sale(quantity=quantity, unit_price=unit_price, cost_basis=basis, tax_rate=tax_rate)

    pos.quantity -= quantity
    pos.total_cost_basis = pos.average_acquisition_price * pos.quantity
    pos.updated_at = now
    if pos.quantity == 0:
        pos.average_acquisition_price = 0
        pos.total_cost_basis = 0
        pos.desired_listing_price = None
        pos.status = "closed"
        pos.thesis_status = "closed"

    account.current_coins += projection.net_proceeds
    account.realized_profit += projection.profit_after_tax
    account.ea_tax_paid += projection.ea_tax
    account.updated_at = now

    tx = PortfolioTransaction(
        account_id=account.id,
        position_id=pos.id,
        market_segment_id=market_segment_id or pos.market_segment_id,
        card_id=card.id,
        transaction_type="sell",
        occurred_at=now,
        quantity=quantity,
        unit_price=unit_price,
        gross_amount=projection.gross,
        ea_tax=projection.ea_tax,
        net_coin_flow=projection.net_proceeds,
        cost_basis_released=basis,
        realized_profit=projection.profit_after_tax,
        notes=notes,
        metadata_json={},
    )
    session.add(tx)
    record_activity(
        session,
        category="portfolio",
        severity="success" if projection.profit_after_tax >= 0 else "warning",
        title=f"Sold {card.name}",
        message=f"{quantity} × {unit_price:,}; tax {projection.ea_tax:,}; realized {projection.profit_after_tax:+,}.",
        card_id=card.id,
    )
    session.flush()
    return TradeResult(
        tx.id,
        pos.id,
        pos.quantity,
        account.current_coins,
        projection.profit_after_tax,
        projection.ea_tax,
    )
