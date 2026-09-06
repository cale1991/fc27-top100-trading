from fastapi import APIRouter

from fc27trader.db.session import SessionLocal
from fc27trader.services.app_queries import system_state

router = APIRouter(prefix="/system", tags=["system"])


@router.get("")
def get_system() -> dict:
    with SessionLocal() as session:
        return system_state(session)
