import uuid

from fastapi import APIRouter, HTTPException

from fc27trader.api.schemas import CoinBalanceIn, DesiredListingPriceIn, PurchaseIn, SaleIn
from fc27trader.db.models import Card, PortfolioPosition
from fc27trader.db.session import SessionLocal
from fc27trader.services.app_queries import portfolio_state
from fc27trader.services.market_segments import get_market_segment
from fc27trader.services.portfolio import get_or_create_account, record_purchase, record_sale, set_coin_balance, set_desired_listing_price

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("")
def get_portfolio() -> dict:
    with SessionLocal() as session:
        return portfolio_state(session)


@router.put("/balance")
def update_balance(payload: CoinBalanceIn) -> dict:
    with SessionLocal() as session:
        account = get_or_create_account(session)
        tx = set_coin_balance(session, account, payload.coins, notes=payload.notes)
        session.commit()
        return {"transaction_id": str(tx.id), "current_coins": account.current_coins}


@router.post("/purchases")
def purchase(payload: PurchaseIn) -> dict:
    with SessionLocal() as session:
        card = session.get(Card, uuid.UUID(payload.card_id))
        if card is None:
            raise HTTPException(status_code=404, detail="card not found")
        account = get_or_create_account(session)
        segment = get_market_segment(session, game_year=account.game_year or 26, segment_key="PC")
        try:
            result = record_purchase(
                session,
                account=account,
                card=card,
                quantity=payload.quantity,
                unit_price=payload.unit_price,
                occurred_at=payload.occurred_at,
                thesis=payload.thesis,
                catalyst=payload.catalyst,
                notes=payload.notes,
                market_segment_id=segment.id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        session.commit()
        return result.__dict__ if hasattr(result, "__dict__") else {
            "transaction_id": str(result.transaction_id),
            "position_id": str(result.position_id),
            "quantity_remaining": result.quantity_remaining,
            "account_coins": result.account_coins,
            "realized_profit": result.realized_profit,
            "ea_tax": result.ea_tax,
        }


@router.put("/positions/{position_id}/desired-listing-price")
def update_desired_listing_price(position_id: uuid.UUID, payload: DesiredListingPriceIn) -> dict:
    with SessionLocal() as session:
        position = session.get(PortfolioPosition, position_id)
        if position is None:
            raise HTTPException(status_code=404, detail="position not found")
        try:
            set_desired_listing_price(
                session,
                position=position,
                desired_listing_price=payload.desired_listing_price,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        session.commit()
        return {
            "position_id": str(position.id),
            "desired_listing_price": position.desired_listing_price,
        }


@router.post("/sales")
def sale(payload: SaleIn) -> dict:
    with SessionLocal() as session:
        card = session.get(Card, uuid.UUID(payload.card_id))
        if card is None:
            raise HTTPException(status_code=404, detail="card not found")
        account = get_or_create_account(session)
        segment = get_market_segment(session, game_year=account.game_year or 26, segment_key="PC")
        try:
            result = record_sale(
                session,
                account=account,
                card=card,
                quantity=payload.quantity,
                unit_price=payload.unit_price,
                occurred_at=payload.occurred_at,
                notes=payload.notes,
                market_segment_id=segment.id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        session.commit()
        return {
            "transaction_id": str(result.transaction_id),
            "position_id": str(result.position_id),
            "quantity_remaining": result.quantity_remaining,
            "account_coins": result.account_coins,
            "realized_profit": result.realized_profit,
            "ea_tax": result.ea_tax,
        }
