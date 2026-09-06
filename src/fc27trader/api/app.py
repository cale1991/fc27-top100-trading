from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, text

from fc27trader.api.routers import activity, community, dashboard, market, opportunities, portfolio, strategies, system, verification
from fc27trader.db.models import ManualVerificationRequest, OpportunityCandidate
from fc27trader.db.session import SessionLocal, engine
from fc27trader.observability.logging import configure_logging
from fc27trader.settings import get_settings

settings = get_settings()
configure_logging(settings.log_level)
app = FastAPI(title="FC27 Top 100 Trading", version="0.5.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in [dashboard.router, opportunities.router, verification.router, portfolio.router, market.router, activity.router, community.router, strategies.router, system.router]:
    app.include_router(router)


@app.get("/health")
def health() -> dict:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "utc": datetime.now(UTC).isoformat()}


@app.get("/ready")
def ready() -> dict:
    return {"status": "ready", "environment": settings.app_env}


@app.websocket("/ws/live")
async def live_updates(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            with SessionLocal() as session:
                pending = session.scalar(
                    select(func.count()).select_from(ManualVerificationRequest).where(ManualVerificationRequest.status == "pending")
                ) or 0
                active = session.scalar(
                    select(func.count()).select_from(OpportunityCandidate).where(OpportunityCandidate.status != "superseded")
                ) or 0
            await websocket.send_json(
                {
                    "type": "refresh",
                    "at": datetime.now(UTC).isoformat(),
                    "pending_verifications": int(pending),
                    "active_opportunities": int(active),
                }
            )
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        return


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
