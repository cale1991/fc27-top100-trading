from fastapi import APIRouter

from fc27trader.db.session import SessionLocal
from fc27trader.services.app_queries import community_state

router = APIRouter(prefix="/community", tags=["community"])


@router.get("")
def get_community() -> dict:
    with SessionLocal() as session:
        return community_state(session)
