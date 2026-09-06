from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from .enums import Platform


class ObservationKind(StrEnum):
    REFERENCE_PRICE = "reference_price"
    EXECUTION = "execution"
    HISTORICAL_CONTEXT = "historical_context"


class ExecutionObservationType(StrEnum):
    LOWEST_BINS = "lowest_bins"
    LISTING_SAMPLE = "listing_sample"
    BEST_BID = "best_bid"
    MANUAL_SCREENSHOT = "manual_screenshot"
    MANUAL_VALUES = "manual_values"
    TRUSTED_LIVE_FEED = "trusted_live_feed"


class ReferencePriceObservation(BaseModel):
    card_id: str
    provider: str
    platform: Platform = Platform.PC
    provider_timestamp: datetime | None = None
    observed_at: datetime
    price: int
    price_kind: str = "prevailing_bin_region"
    provider_age_seconds: float | None = None
    historical_provider_error_pct: float | None = None
    uncertainty_pct: float | None = None
    confidence: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionObservationInput(BaseModel):
    card_id: str
    source: str
    platform: Platform = Platform.PC
    observation_type: ExecutionObservationType
    observed_at: datetime
    source_timestamp: datetime | None = None
    lowest_bin: int | None = None
    best_bid: int | None = None
    listing_prices: list[int] = Field(default_factory=list)
    listing_count: int | None = None
    confidence: float = 1.0
    manual_verification_request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
