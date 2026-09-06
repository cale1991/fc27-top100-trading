from fastapi import APIRouter, Query
from sqlalchemy import select

from fc27trader.db.models import Notification
from fc27trader.db.session import SessionLocal
from fc27trader.services.app_queries import activity_feed

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("")
def get_activity(limit: int = Query(100, ge=1, le=300)) -> list[dict]:
    with SessionLocal() as session:
        return activity_feed(session, limit)


@router.get("/notifications")
def notifications(limit: int = Query(50, ge=1, le=100)) -> list[dict]:
    with SessionLocal() as session:
        rows = list(session.scalars(select(Notification).where(Notification.status != "dismissed").order_by(Notification.priority.desc(), Notification.created_at.desc()).limit(limit)))
        return [
            {
                "id": str(x.id),
                "created_at": x.created_at.isoformat(),
                "kind": x.kind,
                "priority": x.priority,
                "title": x.title,
                "message": x.message,
                "status": x.status,
            }
            for x in rows
        ]
