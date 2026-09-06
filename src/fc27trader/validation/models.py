from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class CardCategory(StrEnum):
    FODDER = "fodder"
    META_GOLD = "meta_gold"
    ICON_HERO = "icon_hero"
    PROMO = "promo"


class TermsState(StrEnum):
    ALLOWED = "allowed"
    LICENSE_REQUIRED = "license_required"
    PERMISSION_REQUIRED = "permission_required"
    PROHIBITED = "prohibited"
    UNRESOLVED = "unresolved"


class ProviderRole(StrEnum):
    """A source can be useful without being fresh enough for execution.

    HOT_REFERENCE is the only role that carries the <=300 second qualification.
    It is deliberately not a global prerequisite for trading-system development.
    """

    HOT_REFERENCE = "hot_reference"
    REFERENCE = "reference"
    HISTORICAL = "historical"
    METADATA = "metadata"
    CONTENT = "content"
    MANUAL_BENCHMARK = "manual_benchmark"


class QualificationStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"
    NOT_TESTED = "not_tested"


class ValidationCard(BaseModel):
    key: str
    name: str
    category: CardCategory
    version: str
    rating: int | None = None
    ea_definition_id: int | None = None
    provider_ids: dict[str, str] = Field(default_factory=dict)
    benchmark_url: str | None = None


class MarketQuote(BaseModel):
    provider: str
    card_key: str
    price_pc: int | None
    provider_timestamp: datetime | None = None
    observed_at: datetime
    request_started_at: datetime | None = None
    http_latency_ms: float | None = None
    source_card_id: str | None = None
    fields_available: list[str] = Field(default_factory=list)
    raw_reference: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("price_pc")
    @classmethod
    def nonnegative_price(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("price_pc cannot be negative")
        return value


class BenchmarkQuote(BaseModel):
    card_key: str
    price_pc: int
    observed_at: datetime
    provider_timestamp: datetime | None = None
    source: str = "futbin_manual"
    raw_reference: str | None = None


class ProviderProfile(BaseModel):
    key: str
    name: str
    endpoint_or_surface: str
    pc_supported: bool
    documented_rate_limit: str | None = None
    cost: str | None = None
    fields_available: list[str] = Field(default_factory=list)
    provider_timestamp_field: str | None = None
    documented_freshness: str | None = None
    terms_state: TermsState
    terms_summary: str
    terms_url: str | None = None
    notes: str | None = None
    upstream_provenance: str | None = None
    declared_roles: list[ProviderRole] = Field(default_factory=list)


class PairedObservation(BaseModel):
    provider: str
    card_key: str
    category: CardCategory
    benchmark_price_pc: int
    provider_price_pc: int | None
    benchmark_observed_at: datetime
    provider_observed_at: datetime
    provider_timestamp: datetime | None
    http_latency_ms: float | None
    provider_age_seconds: float | None
    observed_skew_seconds: float
    absolute_error_coins: int | None
    absolute_pct_error: float | None
    fields_available: list[str] = Field(default_factory=list)
    raw_reference: str | None = None


class FreshnessEvidence(BaseModel):
    timestamped_samples: int = 0
    timestamp_age_p50_seconds: float | None = None
    timestamp_age_p95_seconds: float | None = None
    timestamp_age_max_seconds: float | None = None
    propagation_events: int = 0
    propagation_delay_p50_seconds: float | None = None
    propagation_delay_p95_seconds: float | None = None
    freshness_proven: bool = False
    reason: str


class QualificationReport(BaseModel):
    provider: ProviderProfile
    status: QualificationStatus
    qualified_roles: list[ProviderRole] = Field(default_factory=list)
    role_reasons: dict[str, list[str]] = Field(default_factory=dict)
    # Backward-compatible fields. Both now mean HOT_REFERENCE only, not "system may run".
    hot_reference_eligible: bool = False
    hot_market_eligible: bool = False
    tested_at: datetime
    required_cards: int
    paired_cards: int
    coverage_pct: float
    category_counts: dict[str, int]
    freshness: FreshnessEvidence
    latency_p50_ms: float | None = None
    latency_p95_ms: float | None = None
    median_abs_pct_error: float | None = None
    p90_abs_pct_error: float | None = None
    median_abs_error_coins: float | None = None
    rejection_reasons: list[str] = Field(default_factory=list)
    observations: list[PairedObservation] = Field(default_factory=list)

    def supports(self, role: ProviderRole) -> bool:
        return role in self.qualified_roles


class PropagationObservation(BaseModel):
    provider: str
    card_key: str
    benchmark_changed_at: datetime
    benchmark_new_price: int
    provider_matched_at: datetime | None = None
    provider_price_at_match: int | None = None

    @property
    def delay_seconds(self) -> float | None:
        if self.provider_matched_at is None:
            return None
        return (self.provider_matched_at - self.benchmark_changed_at).total_seconds()
