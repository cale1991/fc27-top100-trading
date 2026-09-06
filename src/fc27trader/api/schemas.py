from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ManualVerificationResponseIn(BaseModel):
    observed_at: datetime
    listing_prices: list[int] = Field(default_factory=list)
    lowest_bin: int | None = None
    best_bid: int | None = None
    screenshot_uri: str | None = None
    approximate: bool = False
    notes: str | None = None


class CoinBalanceIn(BaseModel):
    coins: int = Field(ge=0)
    notes: str | None = None


class PurchaseIn(BaseModel):
    card_id: str
    quantity: int = Field(gt=0)
    unit_price: int = Field(gt=0)
    occurred_at: datetime | None = None
    thesis: str | None = None
    catalyst: str | None = None
    notes: str | None = None


class SaleIn(BaseModel):
    card_id: str
    quantity: int = Field(gt=0)
    unit_price: int = Field(gt=0)
    occurred_at: datetime | None = None
    notes: str | None = None


class DesiredListingPriceIn(BaseModel):
    desired_listing_price: int | None = Field(default=None, gt=0)
