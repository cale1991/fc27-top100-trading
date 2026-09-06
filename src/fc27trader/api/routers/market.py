import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from fc27trader.db.models import Card
from fc27trader.db.session import SessionLocal
from fc27trader.services.app_queries import card_research

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/search")
def search_market(q: str = Query(min_length=2), limit: int = Query(30, ge=1, le=100)) -> list[dict]:
    with SessionLocal() as session:
        cards = list(session.scalars(select(Card).where(Card.game_year.in_([26, 27]), Card.name.ilike(f"%{q}%")).order_by(Card.rating.desc().nullslast(), Card.name).limit(limit)))
        return [{"id": str(x.id), "name": x.name, "rating": x.rating, "version": x.rarity, "position": x.primary_position, "league": x.league, "club": x.club, "nation": x.nation} for x in cards]


@router.get("/cards/{card_id}")
def research_card(card_id: uuid.UUID) -> dict:
    with SessionLocal() as session:
        result = card_research(session, card_id)
        if result is None:
            raise HTTPException(status_code=404, detail="card not found")
        return result
