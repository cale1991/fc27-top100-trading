from fastapi import APIRouter

from fc27trader.db.session import SessionLocal
from fc27trader.services.app_queries import dashboard_state

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard() -> dict:
    with SessionLocal() as session:
        return dashboard_state(session)
