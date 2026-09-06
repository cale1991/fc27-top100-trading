from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .enums import EvidenceClass, EventType


class MarketEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: EventType
    evidence_class: EvidenceClass = EvidenceClass.CONFIRMED
    game_year: int
    source_key: str
    external_id: str | None = None
    title: str
    summary: str | None = None
    published_at: datetime | None = None
    effective_at: datetime | None = None
    expires_at: datetime | None = None
    detected_at: datetime
    source_url: str | None = None
    affected_card_ids: list[str] = Field(default_factory=list)
    affected_segments: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
