from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from .enums import Platform


class MarketSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    card_external_id: str
    source_key: str
    platform: Platform
    source_timestamp: datetime | None = None
    observed_at: datetime
    lowest_bin: int | None = None
    best_bid: int | None = None
    active_listings: int | None = None
    sales_5m: int | None = None
    sales_15m: int | None = None
    spread: Decimal | None = None
    source_updated_at: datetime | None = None
