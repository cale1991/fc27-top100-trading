import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from fc27trader.db.models import Card
from fc27trader.db.session import SessionLocal
from fc27trader.services.app_queries import list_opportunities, opportunity_detail

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("")
def opportunities(limit: int = Query(50, ge=1, le=200)) -> list[dict]:
    with SessionLocal() as session:
        return list_opportunities(session, limit)


@router.get("/search/cards")
def search_cards(q: str = Query(min_length=2), limit: int = Query(20, ge=1, le=50)) -> list[dict]:
    with SessionLocal() as session:
        rows = session.execute(
            select(Card)
            .where(Card.game_year.in_([26, 27]), Card.name.ilike(f"%{q}%"))
            .order_by(Card.rating.desc().nullslast(), Card.name.asc())
            .limit(limit)
        ).scalars().all()
        return [
            {
                "id": str(x.id),
                "name": x.name,
                "rating": x.rating,
                "version": x.rarity,
                "position": x.primary_position,
                "league": x.league,
                "club": x.club,
                "nation": x.nation,
            }
            for x in rows
        ]


@router.get("/{candidate_id}")
def opportunity(candidate_id: uuid.UUID) -> dict:
    with SessionLocal() as session:
        result = opportunity_detail(session, candidate_id)
        if result is None:
            raise HTTPException(status_code=404, detail="opportunity not found")
        return result
