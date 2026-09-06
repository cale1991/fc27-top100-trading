from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def uuid_pk() -> uuid.UUID:
    return uuid.uuid4()


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    source_class: Mapped[str] = mapped_column(String(32))
    automation_policy: Mapped[str] = mapped_column(String(64))
    training_policy: Mapped[str] = mapped_column(String(64))
    terms_url: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class RawIngest(Base):
    __tablename__ = "raw_ingests"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    source_kind: Mapped[str] = mapped_column(String(64), index=True)
    request_url: Mapped[str] = mapped_column(Text)
    request_method: Mapped[str] = mapped_column(String(16), default="GET")
    http_status: Mapped[int | None] = mapped_column(Integer)
    content_type: Mapped[str | None] = mapped_column(String(128))
    source_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    checksum_sha256: Mapped[str] = mapped_column(String(64), index=True)
    etag: Mapped[str | None] = mapped_column(String(256))
    last_modified: Mapped[str | None] = mapped_column(String(256))
    storage_uri: Mapped[str] = mapped_column(Text)
    payload_size: Mapped[int] = mapped_column(BigInteger)
    parser_version: Mapped[str | None] = mapped_column(String(64))
    schema_version: Mapped[str | None] = mapped_column(String(64))
    inserted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        UniqueConstraint("source_id", "checksum_sha256", name="uq_raw_source_checksum"),
    )


class Card(Base):
    __tablename__ = "cards"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    game_year: Mapped[int] = mapped_column(Integer, index=True)
    ea_asset_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    ea_resource_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    rating: Mapped[int | None] = mapped_column(Integer, index=True)
    rarity: Mapped[str | None] = mapped_column(String(96), index=True)
    primary_position: Mapped[str | None] = mapped_column(String(16), index=True)
    league: Mapped[str | None] = mapped_column(String(128), index=True)
    club: Mapped[str | None] = mapped_column(String(128), index=True)
    nation: Mapped[str | None] = mapped_column(String(128), index=True)
    promo: Mapped[str | None] = mapped_column(String(128), index=True)
    image_id: Mapped[str | None] = mapped_column(String(256))
    image_url: Mapped[str | None] = mapped_column(Text)
    tradeable: Mapped[bool | None] = mapped_column(Boolean)
    in_packs: Mapped[bool | None] = mapped_column(Boolean, index=True)
    attributes_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    playstyles_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    roles_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("game_year", "ea_resource_id", name="uq_card_game_resource"),
    )


class CardSourceId(Base):
    __tablename__ = "card_source_ids"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id", ondelete="CASCADE"), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(160))
    source_url: Mapped[str | None] = mapped_column(Text)
    mapping_method: Mapped[str | None] = mapped_column(String(64))
    mapping_confidence: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    mapping_status: Mapped[str | None] = mapped_column(String(32), index=True)
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_card_source_external"),
    )


class ProviderEntity(Base):
    """Named provider-side entities used to resolve player metadata IDs."""
    __tablename__ = "provider_entities"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    entity_type: Mapped[str] = mapped_column(String(32), index=True)
    external_id: Mapped[str] = mapped_column(String(160))
    name: Mapped[str | None] = mapped_column(String(160), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (
        UniqueConstraint("source_id", "entity_type", "external_id", name="uq_provider_entity"),
    )


class CollectionTarget(Base):
    __tablename__ = "collection_targets"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(16), default="pc", index=True)
    tier: Mapped[str] = mapped_column(String(32), index=True)
    target_interval_seconds: Mapped[int] = mapped_column(Integer)
    priority: Mapped[int] = mapped_column(Integer, default=100, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    next_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        UniqueConstraint("card_id", "platform", name="uq_collection_card_platform"),
    )


class CardRelationshipEdge(Base):
    __tablename__ = "card_relationship_edges"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    source_card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id", ondelete="CASCADE"), index=True)
    target_card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id", ondelete="CASCADE"), index=True)
    edge_type: Mapped[str] = mapped_column(String(64), index=True)
    weight: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        UniqueConstraint("source_card_id", "target_card_id", "edge_type", name="uq_card_relationship"),
    )


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    raw_ingest_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("raw_ingests.id"))
    platform: Mapped[str] = mapped_column(String(16), index=True)
    lowest_bin: Mapped[int | None] = mapped_column(Integer)
    best_bid: Mapped[int | None] = mapped_column(Integer)
    active_listings: Mapped[int | None] = mapped_column(Integer)
    sales_5m: Mapped[int | None] = mapped_column(Integer)
    sales_15m: Mapped[int | None] = mapped_column(Integer)
    spread_abs: Mapped[int | None] = mapped_column(Integer)
    spread_pct: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    price_min: Mapped[int | None] = mapped_column(Integer)
    price_max: Mapped[int | None] = mapped_column(Integer)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    quality_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_market_card_platform_time", "card_id", "platform", "observed_at"),
    )


class MarketIndexSnapshot(Base):
    __tablename__ = "market_index_snapshots"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    platform: Mapped[str] = mapped_column(String(16), index=True)
    index_key: Mapped[str] = mapped_column(String(128), index=True)
    value: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    constituent_count: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class MarketListingObservation(Base):
    __tablename__ = "market_listing_observations"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    platform: Mapped[str] = mapped_column(String(16), index=True)
    external_trade_id: Mapped[str | None] = mapped_column(String(128), index=True)
    current_bid: Mapped[int | None] = mapped_column(Integer)
    buy_now: Mapped[int | None] = mapped_column(Integer)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_ingest_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("raw_ingests.id"))


class CompletedSaleObservation(Base):
    __tablename__ = "completed_sale_observations"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    sold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    platform: Mapped[str] = mapped_column(String(16), index=True)
    price: Mapped[int] = mapped_column(Integer)
    external_trade_id: Mapped[str | None] = mapped_column(String(128), index=True)
    raw_ingest_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("raw_ingests.id"))


class ContentEvent(Base):
    __tablename__ = "content_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    event_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    game_year: Mapped[int] = mapped_column(Integer, index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    evidence_class: Mapped[str] = mapped_column(String(32), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    raw_ingest_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("raw_ingests.id"))
    external_id: Mapped[str | None] = mapped_column(String(160), index=True)
    title: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source_url: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class EventImpact(Base):
    __tablename__ = "event_impacts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("content_events.id", ondelete="CASCADE"), index=True)
    card_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cards.id"), index=True)
    segment_key: Mapped[str | None] = mapped_column(String(160), index=True)
    impact_type: Mapped[str] = mapped_column(String(64), index=True)
    direction: Mapped[str | None] = mapped_column(String(16))
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    reason: Mapped[str | None] = mapped_column(Text)


class Sbc(Base):
    __tablename__ = "sbcs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    external_id: Mapped[str | None] = mapped_column(String(160), index=True)
    game_year: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    category: Mapped[str | None] = mapped_column(String(64), index=True)
    repeatable_count: Mapped[int | None] = mapped_column(Integer)
    refresh_seconds: Mapped[int | None] = mapped_column(Integer)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    reward_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class SbcRequirement(Base):
    __tablename__ = "sbc_requirements"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    sbc_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sbcs.id", ondelete="CASCADE"), index=True)
    squad_name: Mapped[str | None] = mapped_column(String(160))
    requirement_type: Mapped[str] = mapped_column(String(64), index=True)
    operator: Mapped[str | None] = mapped_column(String(16))
    value_numeric: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    value_text: Mapped[str | None] = mapped_column(String(160), index=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class Evolution(Base):
    __tablename__ = "evolutions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    external_id: Mapped[str | None] = mapped_column(String(160), index=True)
    game_year: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    coin_cost: Mapped[int | None] = mapped_column(Integer)
    fc_point_cost: Mapped[int | None] = mapped_column(Integer)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    upgrades_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class EvolutionRequirement(Base):
    __tablename__ = "evolution_requirements"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    evolution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evolutions.id", ondelete="CASCADE"), index=True)
    requirement_type: Mapped[str] = mapped_column(String(64), index=True)
    operator: Mapped[str | None] = mapped_column(String(16))
    value_numeric: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    value_text: Mapped[str | None] = mapped_column(String(160), index=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class Pack(Base):
    __tablename__ = "packs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    external_id: Mapped[str | None] = mapped_column(String(160), index=True)
    game_year: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    coin_price: Mapped[int | None] = mapped_column(Integer)
    fc_point_price: Mapped[int | None] = mapped_column(Integer)
    available_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    available_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class PackProbability(Base):
    __tablename__ = "pack_probabilities"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    pack_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("packs.id", ondelete="CASCADE"), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    category: Mapped[str] = mapped_column(String(160), index=True)
    minimum_probability: Mapped[Decimal] = mapped_column(Numeric(8, 6))
    raw_ingest_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("raw_ingests.id"))


class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), index=True)
    platform: Mapped[str] = mapped_column(String(16), index=True)
    model_key: Mapped[str] = mapped_column(String(128), index=True)
    model_version: Mapped[str] = mapped_column(String(128), index=True)
    horizon_seconds: Mapped[int] = mapped_column(Integer, index=True)
    current_price: Mapped[int | None] = mapped_column(Integer)
    future_sell_price: Mapped[int | None] = mapped_column(Integer)
    profitable_exit_probability: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    expected_net_profit: Mapped[int | None] = mapped_column(Integer)
    expected_time_to_sale_seconds: Mapped[int | None] = mapped_column(Integer)
    expected_profit_per_hour: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    expected_profit_per_capital: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    max_position_size: Mapped[int | None] = mapped_column(Integer)
    downside_risk: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    catalyst_failure_probability: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    payload_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class Signal(Base):
    __tablename__ = "signals"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), index=True)
    prediction_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("predictions.id"), index=True)
    signal_type: Mapped[str] = mapped_column(String(32), index=True)
    current_pc_price: Mapped[int] = mapped_column(Integer)
    max_buy_price: Mapped[int] = mapped_column(Integer)
    recommended_quantity: Mapped[int] = mapped_column(Integer)
    total_capital_required: Mapped[int] = mapped_column(BigInteger)
    target_sell_price: Mapped[int] = mapped_column(Integer)
    minimum_sell_price: Mapped[int] = mapped_column(Integer)
    expected_ea_tax: Mapped[int] = mapped_column(Integer)
    expected_net_profit: Mapped[int] = mapped_column(Integer)
    expected_roi: Mapped[Decimal] = mapped_column(Numeric(12, 8))
    expected_holding_seconds: Mapped[int] = mapped_column(Integer)
    expected_profit_per_hour: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    liquidity_score: Mapped[Decimal] = mapped_column(Numeric(8, 6))
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(8, 6))
    main_catalyst: Mapped[str | None] = mapped_column(Text)
    historical_analogue: Mapped[str | None] = mapped_column(Text)
    ea_intervention_risk: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    invalidating_condition: Mapped[str | None] = mapped_column(Text)
    exit_condition: Mapped[str | None] = mapped_column(Text)


class ShadowAccount(Base):
    __tablename__ = "shadow_accounts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    platform: Mapped[str] = mapped_column(String(16), default="pc")
    starting_coins: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    rules_version: Mapped[str] = mapped_column(String(64))


class ShadowOrder(Base):
    __tablename__ = "shadow_orders"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shadow_accounts.id"), index=True)
    signal_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("signals.id"), index=True)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), index=True)
    side: Mapped[str] = mapped_column(String(8), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    decision_price: Mapped[int | None] = mapped_column(Integer)
    limit_price: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), index=True)
    strategy_key: Mapped[str | None] = mapped_column(String(128), index=True)
    reason: Mapped[str | None] = mapped_column(Text)
    source_snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("market_snapshots.id"))


class ShadowFill(Base):
    __tablename__ = "shadow_fills"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shadow_orders.id", ondelete="CASCADE"), index=True)
    filled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[int] = mapped_column(Integer)
    ea_tax: Mapped[int] = mapped_column(Integer, default=0)
    source_snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("market_snapshots.id"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class ShadowTrade(Base):
    __tablename__ = "shadow_trades"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shadow_accounts.id"), index=True)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), index=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    average_buy_price: Mapped[int] = mapped_column(Integer)
    average_sell_price: Mapped[int | None] = mapped_column(Integer)
    ea_tax_paid: Mapped[int] = mapped_column(Integer, default=0)
    predicted_profit: Mapped[int | None] = mapped_column(Integer)
    realized_profit: Mapped[int | None] = mapped_column(Integer)
    holding_seconds: Mapped[int | None] = mapped_column(Integer)
    model_confidence: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    strategy_key: Mapped[str | None] = mapped_column(String(128), index=True)
    entry_reason: Mapped[str | None] = mapped_column(Text)
    exit_reason: Mapped[str | None] = mapped_column(Text)


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shadow_accounts.id"), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    available_coins: Mapped[int] = mapped_column(BigInteger)
    invested_coins: Mapped[int] = mapped_column(BigInteger)
    unrealized_profit: Mapped[int] = mapped_column(BigInteger)
    realized_profit: Mapped[int] = mapped_column(BigInteger)
    ea_tax_paid: Mapped[int] = mapped_column(BigInteger)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class ModelRun(Base):
    __tablename__ = "model_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    model_key: Mapped[str] = mapped_column(String(128), index=True)
    model_version: Mapped[str] = mapped_column(String(128), index=True)
    run_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    run_finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    train_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    train_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    validation_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    validation_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    artifact_uri: Mapped[str | None] = mapped_column(Text)
    config_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    metrics_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), index=True)


class CollectorRun(Base):
    __tablename__ = "collector_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    collector_key: Mapped[str] = mapped_column(String(128), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), index=True)
    records_seen: Mapped[int] = mapped_column(Integer, default=0)
    records_written: Mapped[int] = mapped_column(Integer, default=0)
    raw_ingest_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class ProviderHealth(Base):
    """Current operational health for each provider/role/platform combination."""
    __tablename__ = "provider_health"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    provider_key: Mapped[str] = mapped_column(String(64), index=True)
    provider_role: Mapped[str] = mapped_column(String(32), index=True)
    platform: Mapped[str] = mapped_column(String(32), default="pc", index=True)
    status: Mapped[str | None] = mapped_column(String(32), index=True)
    access_type: Mapped[str | None] = mapped_column(String(32), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    supported_segments_json: Mapped[list] = mapped_column(JSONB, default=list)
    last_request_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_error: Mapped[str | None] = mapped_column(Text)
    requests_total: Mapped[int] = mapped_column(BigInteger, default=0)
    requests_failed: Mapped[int] = mapped_column(BigInteger, default=0)
    cards_covered: Mapped[int] = mapped_column(Integer, default=0)
    latest_observation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    latest_provider_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    latest_observation_age_seconds: Mapped[Decimal | None] = mapped_column(Numeric(16, 3))
    last_latency_ms: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))
    error_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 8))
    rate_limit_remaining: Mapped[int | None] = mapped_column(Integer)
    rate_limit_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retry_after_seconds: Mapped[int | None] = mapped_column(Integer)
    items_seen: Mapped[int] = mapped_column(BigInteger, default=0)
    items_ingested: Mapped[int] = mapped_column(BigInteger, default=0)
    duplicates_skipped: Mapped[int] = mapped_column(BigInteger, default=0)
    quarantined_observations: Mapped[int] = mapped_column(BigInteger, default=0)
    parsing_failures: Mapped[int] = mapped_column(BigInteger, default=0)
    normalization_failures: Mapped[int] = mapped_column(BigInteger, default=0)
    identity_failures: Mapped[int] = mapped_column(BigInteger, default=0)
    last_poll_duration_ms: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))
    gap_status: Mapped[str | None] = mapped_column(String(32), index=True)
    platform_certainty: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (
        UniqueConstraint("provider_key", "provider_role", "platform", name="uq_provider_health_role_platform"),
    )


class DataQualityIncident(Base):
    __tablename__ = "data_quality_incidents"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sources.id"), index=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    incident_type: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class ProviderValidationRun(Base):
    __tablename__ = "provider_validation_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    provider_key: Mapped[str] = mapped_column(String(64), index=True)
    benchmark_source: Mapped[str] = mapped_column(String(64), default="futbin_manual", index=True)
    platform: Mapped[str] = mapped_column(String(16), default="pc", index=True)
    game_year: Mapped[int] = mapped_column(Integer, default=26, index=True)
    basket_version: Mapped[str] = mapped_column(String(64))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    required_cards: Mapped[int] = mapped_column(Integer, default=50)
    paired_cards: Mapped[int] = mapped_column(Integer, default=0)
    config_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    summary_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class ProviderValidationObservation(Base):
    __tablename__ = "provider_validation_observations"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("provider_validation_runs.id", ondelete="CASCADE"), index=True
    )
    provider_key: Mapped[str] = mapped_column(String(64), index=True)
    card_key: Mapped[str] = mapped_column(String(160), index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    provider_price_pc: Mapped[int | None] = mapped_column(Integer)
    benchmark_price_pc: Mapped[int] = mapped_column(Integer)
    provider_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    provider_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    benchmark_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    http_latency_ms: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    provider_age_seconds: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))
    observed_skew_seconds: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    absolute_error_coins: Mapped[int | None] = mapped_column(Integer)
    absolute_pct_error: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    raw_reference: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        UniqueConstraint("run_id", "card_key", name="uq_provider_validation_run_card"),
    )


class ProviderQualification(Base):
    __tablename__ = "provider_qualifications"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    provider_key: Mapped[str] = mapped_column(String(64), index=True)
    platform: Mapped[str] = mapped_column(String(16), default="pc", index=True)
    role: Mapped[str] = mapped_column(String(32), default="reference", index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    hot_market_eligible: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    coverage_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    timestamp_age_p95_seconds: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))
    propagation_delay_p95_seconds: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))
    latency_p95_ms: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))
    median_abs_pct_error: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    rejection_reasons_json: Mapped[list] = mapped_column(JSONB, default=list)
    profile_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    report_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_provider_qualification_role_time", "provider_key", "role", "evaluated_at"),
    )


# --- Production market observation / opportunity layer (2026-09-04 design lock) ---


class ReferencePriceObservation(Base):
    """Approximate fair-value anchor from a third-party price source.

    This row is explicitly not an executable quote. Provider age/error/uncertainty
    are first-class so models can decide how much weight to place on it.
    """
    __tablename__ = "reference_price_observations"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    provider_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    raw_ingest_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("raw_ingests.id"))
    market_segment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("market_segments.id"), index=True)
    platform: Mapped[str] = mapped_column(String(32), default="pc", index=True)
    inserted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    price: Mapped[int] = mapped_column(Integer)
    price_kind: Mapped[str] = mapped_column(String(64), default="prevailing_bin_region", index=True)
    provider_role: Mapped[str] = mapped_column(String(32), default="reference", index=True)
    evidence_class: Mapped[str] = mapped_column(String(32), default="measured_provider", index=True)
    observation_key: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    age_seconds: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))
    historical_provider_error_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    uncertainty_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    quality_status: Mapped[str] = mapped_column(String(32), default="VALID", index=True)
    state_completeness: Mapped[str] = mapped_column(String(32), default="directly_observed", index=True)
    is_backfill: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_reference_card_platform_time", "card_id", "platform", "observed_at"),
    )


class ExecutionObservation(Base):
    """Fresh trade-decision evidence; overrides older reference anchors."""
    __tablename__ = "execution_observations"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    raw_ingest_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("raw_ingests.id"))
    market_segment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("market_segments.id"), index=True)
    platform: Mapped[str] = mapped_column(String(32), default="pc", index=True)
    inserted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    observation_type: Mapped[str] = mapped_column(String(64), index=True)
    lowest_bin: Mapped[int | None] = mapped_column(Integer)
    best_bid: Mapped[int | None] = mapped_column(Integer)
    listing_prices_json: Mapped[list] = mapped_column(JSONB, default=list)
    listing_count: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[Decimal] = mapped_column(Numeric(8, 6), default=Decimal("1.0"))
    quality_status: Mapped[str] = mapped_column(String(32), default="VALID", index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    manual_verification_request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_execution_card_platform_time", "card_id", "platform", "observed_at"),
    )


class OpportunityCandidate(Base):
    """Ephemeral ranked candidate discovered from the broad observable market."""
    __tablename__ = "opportunity_candidates"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), index=True)
    platform: Mapped[str] = mapped_column(String(32), default="pc", index=True)
    market_segment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("market_segments.id"), index=True)
    actionable: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    signal_scope: Mapped[str] = mapped_column(String(32), default="ACTIONABLE", index=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    rank: Mapped[int | None] = mapped_column(Integer, index=True)
    opportunity_score: Mapped[Decimal] = mapped_column(Numeric(16, 8), index=True)
    reference_observation_id: Mapped[int | None] = mapped_column(
        ForeignKey("reference_price_observations.id"), index=True
    )
    execution_observation_id: Mapped[int | None] = mapped_column(
        ForeignKey("execution_observations.id"), index=True
    )
    expected_acquisition_price: Mapped[int | None] = mapped_column(Integer)
    acquisition_probability: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    expected_discount_to_reference: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    profitable_exit_probability: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    expected_net_profit: Mapped[int | None] = mapped_column(Integer)
    expected_profit_per_hour: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    expected_holding_seconds: Mapped[int | None] = mapped_column(Integer)
    position_capacity_coins: Mapped[int | None] = mapped_column(BigInteger)
    liquidity_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    sell_through_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    volatility: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    downside_risk: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    catalyst_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    ea_intervention_risk: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    opportunity_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    requires_manual_verification: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    action: Mapped[str | None] = mapped_column(String(32), index=True)
    max_recommended_buy_price: Mapped[int | None] = mapped_column(Integer)
    target_sell_low: Mapped[int | None] = mapped_column(Integer)
    target_sell_high: Mapped[int | None] = mapped_column(Integer)
    recommended_quantity: Mapped[int | None] = mapped_column(Integer)
    expected_roi: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    main_catalyst: Mapped[str | None] = mapped_column(Text)
    invalidation_condition: Mapped[str | None] = mapped_column(Text)
    exit_logic: Mapped[str | None] = mapped_column(Text)
    score_components_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_opportunity_status_score", "status", "opportunity_score", "last_scored_at"),
    )


class ManualVerificationRequest(Base):
    __tablename__ = "manual_verification_requests"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("opportunity_candidates.id"), index=True)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), index=True)
    platform: Mapped[str] = mapped_column(String(32), default="pc", index=True)
    market_segment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("market_segments.id"), index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    priority: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    reason: Mapped[str] = mapped_column(Text)
    reference_observation_id: Mapped[int | None] = mapped_column(
        ForeignKey("reference_price_observations.id"), index=True
    )
    latest_reference_price: Mapped[int | None] = mapped_column(Integer)
    reference_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reference_uncertainty_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    expected_acquisition_min: Mapped[int | None] = mapped_column(Integer)
    expected_acquisition_max: Mapped[int | None] = mapped_column(Integer)
    attractive_at_or_below: Mapped[int | None] = mapped_column(Integer)
    required_information: Mapped[str] = mapped_column(Text)
    expected_information_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class ManualVerificationResponse(Base):
    __tablename__ = "manual_verification_responses"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("manual_verification_requests.id", ondelete="CASCADE"), index=True
    )
    market_segment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("market_segments.id"), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    listing_prices_json: Mapped[list] = mapped_column(JSONB, default=list)
    lowest_bin: Mapped[int | None] = mapped_column(Integer)
    best_bid: Mapped[int | None] = mapped_column(Integer)
    screenshot_uri: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    input_kind: Mapped[str | None] = mapped_column(String(32), index=True)
    observation_confidence: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    observation_age_seconds: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))
    execution_observation_id: Mapped[int | None] = mapped_column(
        ForeignKey("execution_observations.id"), index=True
    )
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class AttentionAllocation(Base):
    """Time-bounded observation allocation; recomputed continuously."""
    __tablename__ = "attention_allocations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), index=True)
    platform: Mapped[str] = mapped_column(String(16), default="pc", index=True)
    recomputed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    attention_score: Mapped[Decimal] = mapped_column(Numeric(16, 8), index=True)
    tier: Mapped[str] = mapped_column(String(32), index=True)
    target_interval_seconds: Mapped[int] = mapped_column(Integer)
    reasons_json: Mapped[list] = mapped_column(JSONB, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_attention_valid_score", "valid_until", "attention_score"),
    )


class AcquisitionOpportunityObservation(Base):
    """Observed undercut/search outcomes used to learn acquisition distributions."""
    __tablename__ = "acquisition_opportunity_observations"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), index=True)
    platform: Mapped[str] = mapped_column(String(16), default="pc", index=True)
    reference_observation_id: Mapped[int] = mapped_column(
        ForeignKey("reference_price_observations.id"), index=True
    )
    execution_observation_id: Mapped[int | None] = mapped_column(
        ForeignKey("execution_observations.id"), index=True
    )
    search_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    reference_price: Mapped[int] = mapped_column(Integer)
    listing_price: Mapped[int | None] = mapped_column(Integer)
    discount_to_reference: Mapped[Decimal | None] = mapped_column(Numeric(12, 8), index=True)
    time_to_opportunity_seconds: Mapped[int | None] = mapped_column(Integer)
    quantity_available: Mapped[int | None] = mapped_column(Integer)
    acquired: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    context_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class ShadowExecutionAttempt(Base):
    """Separates signal quality from the realism/quality of simulated execution."""
    __tablename__ = "shadow_execution_attempts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("shadow_orders.id"), index=True)
    signal_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("signals.id"), index=True)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), index=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    reference_observation_id: Mapped[int | None] = mapped_column(
        ForeignKey("reference_price_observations.id"), index=True
    )
    execution_observation_id: Mapped[int | None] = mapped_column(
        ForeignKey("execution_observations.id"), index=True
    )
    acquisition_probability: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    expected_acquisition_delay_seconds: Mapped[int | None] = mapped_column(Integer)
    realized_acquisition_delay_seconds: Mapped[int | None] = mapped_column(Integer)
    requested_quantity: Mapped[int] = mapped_column(Integer)
    available_quantity: Mapped[int | None] = mapped_column(Integer)
    filled_quantity: Mapped[int] = mapped_column(Integer, default=0)
    signal_quality_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    execution_quality_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    outcome: Mapped[str] = mapped_column(String(32), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


# --- User application / portfolio / community / public-ledger layer ---


class TradingAccount(Base):
    __tablename__ = "trading_accounts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    platform: Mapped[str] = mapped_column(String(32), default="pc", index=True)
    game_year: Mapped[int] = mapped_column(Integer, default=26, index=True)
    starting_coins: Mapped[int] = mapped_column(BigInteger, default=0)
    current_coins: Mapped[int] = mapped_column(BigInteger, default=0)
    realized_profit: Mapped[int] = mapped_column(BigInteger, default=0)
    ea_tax_paid: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trading_accounts.id", ondelete="CASCADE"), index=True)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), index=True)
    market_segment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("market_segments.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    average_acquisition_price: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_basis: Mapped[int] = mapped_column(BigInteger, default=0)
    desired_listing_price: Mapped[int | None] = mapped_column(Integer)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)
    current_action: Mapped[str | None] = mapped_column(String(32), index=True)
    urgency: Mapped[int] = mapped_column(Integer, default=0, index=True)
    original_thesis: Mapped[str | None] = mapped_column(Text)
    original_catalyst: Mapped[str | None] = mapped_column(Text)
    thesis_status: Mapped[str | None] = mapped_column(String(64), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        UniqueConstraint("account_id", "card_id", "market_segment_id", name="uq_portfolio_account_card_segment"),
        Index("ix_portfolio_open_urgency", "account_id", "status", "urgency"),
    )


class PortfolioTransaction(Base):
    __tablename__ = "portfolio_transactions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trading_accounts.id", ondelete="CASCADE"), index=True)
    position_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("portfolio_positions.id"), index=True)
    market_segment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("market_segments.id"), index=True)
    card_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cards.id"), index=True)
    transaction_type: Mapped[str] = mapped_column(String(32), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    unit_price: Mapped[int | None] = mapped_column(Integer)
    gross_amount: Mapped[int] = mapped_column(BigInteger, default=0)
    ea_tax: Mapped[int] = mapped_column(BigInteger, default=0)
    net_coin_flow: Mapped[int] = mapped_column(BigInteger, default=0)
    cost_basis_released: Mapped[int] = mapped_column(BigInteger, default=0)
    realized_profit: Mapped[int] = mapped_column(BigInteger, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class ActivityFeedItem(Base):
    __tablename__ = "activity_feed_items"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    category: Mapped[str] = mapped_column(String(48), index=True)
    severity: Mapped[str] = mapped_column(String(16), default="info", index=True)
    title: Mapped[str] = mapped_column(Text)
    message: Mapped[str | None] = mapped_column(Text)
    card_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cards.id"), index=True)
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("opportunity_candidates.id"), index=True)
    content_event_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("content_events.id"), index=True)
    source_key: Mapped[str | None] = mapped_column(String(64), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    kind: Mapped[str] = mapped_column(String(48), index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, index=True)
    title: Mapped[str] = mapped_column(Text)
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(24), default="unread", index=True)
    card_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cards.id"), index=True)
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("opportunity_candidates.id"), index=True)
    verification_request_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("manual_verification_requests.id"), index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class ServiceHeartbeat(Base):
    __tablename__ = "service_heartbeats"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    service_key: Mapped[str] = mapped_column(String(128), index=True)
    node_key: Mapped[str] = mapped_column(String(128), index=True)
    service_kind: Mapped[str] = mapped_column(String(48), index=True)
    status: Mapped[str] = mapped_column(String(24), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (UniqueConstraint("service_key", "node_key", name="uq_service_heartbeat_node"),)


class CommunityTrader(Base):
    __tablename__ = "community_traders"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    source_platform: Mapped[str] = mapped_column(String(32), index=True)
    external_author_id: Mapped[str | None] = mapped_column(String(160), index=True)
    handle: Mapped[str] = mapped_column(String(160), index=True)
    display_name: Mapped[str | None] = mapped_column(String(200))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (UniqueConstraint("source_platform", "handle", name="uq_community_trader_handle"),)


class CommunityContent(Base):
    __tablename__ = "community_content"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    trader_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("community_traders.id"), index=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sources.id"), index=True)
    external_id: Mapped[str | None] = mapped_column(String(200), index=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source_url: Mapped[str | None] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    raw_ingest_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("raw_ingests.id"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class CommunitySignal(Base):
    __tablename__ = "community_signals"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    content_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("community_content.id", ondelete="CASCADE"), index=True)
    trader_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("community_traders.id"), index=True)
    card_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cards.id"), index=True)
    category_key: Mapped[str | None] = mapped_column(String(128), index=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    direction: Mapped[str] = mapped_column(String(24), index=True)
    quoted_entry: Mapped[int | None] = mapped_column(Integer)
    target_price: Mapped[int | None] = mapped_column(Integer)
    catalyst: Mapped[str | None] = mapped_column(Text)
    horizon_seconds: Mapped[int | None] = mapped_column(Integer, index=True)
    stated_confidence: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    preceded_market_move: Mapped[bool | None] = mapped_column(Boolean, index=True)
    extraction_confidence: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class CommunitySignalOutcome(Base):
    __tablename__ = "community_signal_outcomes"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    signal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("community_signals.id", ondelete="CASCADE"), unique=True, index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    directional_correct: Mapped[bool | None] = mapped_column(Boolean)
    profitable_after_tax: Mapped[bool | None] = mapped_column(Boolean)
    return_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    benchmark_return_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    alpha_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    max_drawdown_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    timing_quality: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    holding_seconds: Mapped[int | None] = mapped_column(Integer)
    outcome_status: Mapped[str] = mapped_column(String(32), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class TraderReputationSnapshot(Base):
    __tablename__ = "trader_reputation_snapshots"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    trader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("community_traders.id", ondelete="CASCADE"), index=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    directional_accuracy: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    profitable_after_tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    average_return_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    median_return_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    average_alpha_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    max_drawdown_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    average_drawdown_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    timing_quality: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    average_holding_seconds: Mapped[int | None] = mapped_column(Integer)
    recent_form_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    sample_confidence: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    reputation_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 6), index=True)
    category_metrics_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    horizon_metrics_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class PublicPrediction(Base):
    __tablename__ = "public_predictions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    card_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cards.id"), index=True)
    category_key: Mapped[str | None] = mapped_column(String(128), index=True)
    full_post: Mapped[str] = mapped_column(Text)
    market_state_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    prediction: Mapped[str] = mapped_column(Text)
    target_price: Mapped[int | None] = mapped_column(Integer)
    horizon_seconds: Mapped[int | None] = mapped_column(Integer, index=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    catalyst: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    result_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class PublicPost(Base):
    __tablename__ = "public_posts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    prediction_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("public_predictions.id"), index=True)
    platform: Mapped[str] = mapped_column(String(32), default="x", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    external_post_id: Mapped[str | None] = mapped_column(String(200), index=True)
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    preflight_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class SocialMarketImpact(Base):
    __tablename__ = "social_market_impacts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    public_post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("public_posts.id", ondelete="CASCADE"), index=True)
    card_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cards.id"), index=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    price_before: Mapped[int | None] = mapped_column(Integer)
    price_after: Mapped[int | None] = mapped_column(Integer)
    listing_change_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    liquidity_change_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    abnormal_move_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    reach: Mapped[int | None] = mapped_column(BigInteger)
    engagement: Mapped[int | None] = mapped_column(BigInteger)
    impact_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 6), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class PersonaState(Base):
    __tablename__ = "persona_state"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    account_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    recent_style_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    recent_posts_json: Mapped[list] = mapped_column(JSONB, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

# --- Historical Strategy Intelligence layer ---


class StrategyLibrary(Base):
    __tablename__ = "strategy_library"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    canonical_name: Mapped[str] = mapped_column(String(200), index=True)
    explanation: Mapped[str] = mapped_column(Text)
    mechanism: Mapped[str] = mapped_column(Text)
    applicable_card_categories_json: Mapped[list] = mapped_column(JSONB, default=list)
    applicable_market_regimes_json: Mapped[list] = mapped_column(JSONB, default=list)
    catalysts_json: Mapped[list] = mapped_column(JSONB, default=list)
    ideal_entry_conditions_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    exit_logic: Mapped[str | None] = mapped_column(Text)
    invalidation_conditions: Mapped[str | None] = mapped_column(Text)
    typical_capital_requirement_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    scalability_capacity_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    expected_holding_period_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    liquidity_characteristics: Mapped[str | None] = mapped_column(Text)
    ea_tax_sensitivity: Mapped[str | None] = mapped_column(String(32), index=True)
    ea_intervention_risk: Mapped[str | None] = mapped_column(String(32), index=True)
    first_observed_cycle: Mapped[str | None] = mapped_column(String(32), index=True)
    last_observed_cycle: Mapped[str | None] = mapped_column(String(32), index=True)
    evidence_class: Mapped[str] = mapped_column(String(40), default="INCONCLUSIVE", index=True)
    viability_status: Mapped[str] = mapped_column(String(48), default="source_only_unmeasured", index=True)
    measured_status_locked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class StrategyAlias(Base):
    __tablename__ = "strategy_aliases"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    strategy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("strategy_library.id", ondelete="CASCADE"), index=True)
    alias: Mapped[str] = mapped_column(String(200), index=True)
    terminology_source: Mapped[str | None] = mapped_column(String(128))
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (UniqueConstraint("strategy_id", "alias", name="uq_strategy_alias"),)


class StrategyEvidence(Base):
    __tablename__ = "strategy_evidence"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    strategy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("strategy_library.id", ondelete="CASCADE"), index=True)
    game_cycle: Mapped[str] = mapped_column(String(32), index=True)
    source_kind: Mapped[str] = mapped_column(String(64), index=True)
    source_title: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(200), index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    evidence_type: Mapped[str] = mapped_column(String(80), index=True)
    evidence_direction: Mapped[str] = mapped_column(String(32), default="supporting", index=True)
    quality_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    trader_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("community_traders.id"), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (
        Index("ix_strategy_evidence_strategy_cycle", "strategy_id", "game_cycle", "published_at"),
    )


class StrategyCycleAssessment(Base):
    __tablename__ = "strategy_cycle_assessments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    strategy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("strategy_library.id", ondelete="CASCADE"), index=True)
    game_cycle: Mapped[str] = mapped_column(String(32), index=True)
    platform: Mapped[str] = mapped_column(String(16), default="pc", index=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    evidence_weight: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    structural_difference_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    decay_risk: Mapped[Decimal | None] = mapped_column(Numeric(8, 6), index=True)
    viability_status: Mapped[str] = mapped_column(String(48), default="unmeasured", index=True)
    reason: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (
        UniqueConstraint("strategy_id", "game_cycle", "platform", name="uq_strategy_cycle_platform"),
    )


class StrategyBacktestRun(Base):
    __tablename__ = "strategy_backtest_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    strategy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("strategy_library.id", ondelete="CASCADE"), index=True)
    game_cycle: Mapped[str] = mapped_column(String(32), index=True)
    platform: Mapped[str] = mapped_column(String(16), default="pc", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    dataset_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dataset_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), index=True)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    acquisition_attempt_sample_size: Mapped[int] = mapped_column(Integer, default=0)
    code_version: Mapped[str | None] = mapped_column(String(128))
    config_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    metrics_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class StrategyPerformanceSnapshot(Base):
    __tablename__ = "strategy_performance_snapshots"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    strategy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("strategy_library.id", ondelete="CASCADE"), index=True)
    backtest_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("strategy_backtest_runs.id"), index=True)
    game_cycle: Mapped[str] = mapped_column(String(32), index=True)
    platform: Mapped[str] = mapped_column(String(16), default="pc", index=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    sample_size: Mapped[int] = mapped_column(Integer)
    acquisition_attempt_sample_size: Mapped[int] = mapped_column(Integer, default=0)
    total_net_transfer_profit: Mapped[int | None] = mapped_column(BigInteger)
    roi: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    profit_per_hour: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    profit_per_deployed_million: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    capital_turnover: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    hit_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    max_drawdown: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    acquisition_probability: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    profitable_exit_probability: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    median_return_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    median_holding_seconds: Mapped[int | None] = mapped_column(Integer)
    liquidity_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    position_capacity_coins: Mapped[int | None] = mapped_column(BigInteger)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(8, 6), index=True)
    regime_metrics_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    event_metrics_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (
        Index("ix_strategy_perf_strategy_cycle_time", "strategy_id", "game_cycle", "calculated_at"),
    )


class OpportunityStrategyMatch(Base):
    __tablename__ = "opportunity_strategy_matches"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("opportunity_candidates.id", ondelete="CASCADE"), index=True)
    strategy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("strategy_library.id", ondelete="CASCADE"), index=True)
    matched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    similarity: Mapped[Decimal] = mapped_column(Numeric(8, 6), index=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(8, 6), index=True)
    historical_sample_size: Mapped[int] = mapped_column(Integer, default=0)
    historical_success_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    historical_median_net_return: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    expected_holding_seconds: Mapped[int | None] = mapped_column(Integer)
    decay_risk: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    current_conditions_differ: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    matched_reasons_json: Mapped[list] = mapped_column(JSONB, default=list)
    failure_conditions_json: Mapped[list] = mapped_column(JSONB, default=list)
    features_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (
        UniqueConstraint("candidate_id", "strategy_id", name="uq_candidate_strategy_match"),
    )


class StrategyTraderPerformance(Base):
    __tablename__ = "strategy_trader_performance"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    strategy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("strategy_library.id", ondelete="CASCADE"), index=True)
    trader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("community_traders.id", ondelete="CASCADE"), index=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    directional_accuracy: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    profitable_after_tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    average_return_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    median_return_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    average_alpha_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    max_drawdown_pct: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    timing_quality: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    average_holding_seconds: Mapped[int | None] = mapped_column(Integer)
    recent_form_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    sample_confidence: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    reputation_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 6), index=True)
    category_metrics_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    horizon_metrics_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (
        Index("ix_strategy_trader_strategy_trader_time", "strategy_id", "trader_id", "calculated_at"),
    )


class StrategyDiscoveryCandidate(Base):
    __tablename__ = "strategy_discovery_candidates"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    pattern_key: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    first_detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(32), default="observing", index=True)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    effect_size: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(8, 6), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    feature_signature_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    supporting_outcomes_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    review_notes: Mapped[str | None] = mapped_column(Text)
    promoted_strategy_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("strategy_library.id"), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class CommunitySignalStrategyLink(Base):
    __tablename__ = "community_signal_strategy_links"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    signal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("community_signals.id", ondelete="CASCADE"), index=True)
    strategy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("strategy_library.id", ondelete="CASCADE"), index=True)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    match_confidence: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    link_reason: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (
        UniqueConstraint("signal_id", "strategy_id", name="uq_community_signal_strategy"),
    )


# --- Multi-source / multi-market point-in-time intelligence layer (Phase 2) ---

class MarketSegment(Base):
    __tablename__ = "market_segments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    game_year: Mapped[int] = mapped_column(Integer, index=True)
    segment_key: Mapped[str] = mapped_column(String(64), index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    platform: Mapped[str | None] = mapped_column(String(32), index=True)
    platform_group: Mapped[str | None] = mapped_column(String(64), index=True)
    active_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    active_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    executable_by_user: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    provider_support_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    notes: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("game_year", "segment_key", name="uq_market_segment_game_key"),)


class ProviderFeedEvent(Base):
    """Immutable event from a provider feed. Events are not complete market snapshots."""
    __tablename__ = "provider_feed_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    raw_ingest_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("raw_ingests.id"), index=True)
    market_segment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("market_segments.id"), index=True)
    game_year: Mapped[int] = mapped_column(Integer, index=True)
    feed_key: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    provider_event_id: Mapped[str] = mapped_column(String(256))
    provider_card_id: Mapped[str | None] = mapped_column(String(160), index=True)
    card_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cards.id"), index=True)
    identity_status: Mapped[str] = mapped_column(String(32), default="UNRESOLVED", index=True)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    entity_url: Mapped[str | None] = mapped_column(Text)
    provider_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    inserted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    old_price: Mapped[int | None] = mapped_column(Integer)
    new_price: Mapped[int | None] = mapped_column(Integer)
    absolute_change: Mapped[int | None] = mapped_column(Integer)
    percentage_change: Mapped[Decimal | None] = mapped_column(Numeric(14, 8))
    rating: Mapped[int | None] = mapped_column(Integer, index=True)
    card_version: Mapped[str | None] = mapped_column(String(128), index=True)
    observation_semantics: Mapped[str] = mapped_column(String(32), default="MARKET_CONTEXT", index=True)
    state_completeness: Mapped[str] = mapped_column(String(32), default="unknown", index=True)
    quality_status: Mapped[str] = mapped_column(String(32), default="VALID", index=True)
    parser_version: Mapped[str | None] = mapped_column(String(64))
    payload_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (
        UniqueConstraint("source_id", "feed_key", "provider_event_id", name="uq_provider_feed_event_identity"),
        Index("ix_provider_feed_card_time", "card_id", "provider_timestamp"),
    )


class ProviderFeedState(Base):
    __tablename__ = "provider_feed_states"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    feed_key: Mapped[str] = mapped_column(String(64), index=True)
    source_url: Mapped[str] = mapped_column(Text)
    etag: Mapped[str | None] = mapped_column(String(256))
    last_modified: Mapped[str | None] = mapped_column(String(256))
    last_poll_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_http_status: Mapped[int | None] = mapped_column(Integer)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    newest_provider_event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    oldest_provider_event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    inferred_coverage_seconds: Mapped[int | None] = mapped_column(Integer)
    gap_status: Mapped[str] = mapped_column(String(32), default="UNKNOWN_COVERAGE", index=True)
    next_allowed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (UniqueConstraint("source_id", "feed_key", name="uq_provider_feed_state"),)


class ProviderBudgetState(Base):
    __tablename__ = "provider_budget_states"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    provider_key: Mapped[str] = mapped_column(String(64), index=True)
    budget_period: Mapped[str] = mapped_column(String(32), index=True)
    access_mode: Mapped[str] = mapped_column(String(32), default="FULL_UNIVERSE", index=True)
    request_limit: Mapped[int | None] = mapped_column(BigInteger)
    requests_used: Mapped[int] = mapped_column(BigInteger, default=0)
    requests_remaining: Mapped[int | None] = mapped_column(BigInteger)
    credits_limit: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    credits_used: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=0)
    cost_per_credit: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    estimated_daily_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    estimated_monthly_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    resets_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (UniqueConstraint("provider_key", "budget_period", name="uq_provider_budget_period"),)


class ProviderAuditRecord(Base):
    __tablename__ = "provider_audit_records"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    provider_key: Mapped[str] = mapped_column(String(64), index=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    tier: Mapped[str] = mapped_column(String(16), index=True)
    integration_status: Mapped[str] = mapped_column(String(32), index=True)
    capabilities_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    markets_json: Mapped[list] = mapped_column(JSONB, default=list)
    access_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    rights_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    economics_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    source_urls_json: Mapped[list] = mapped_column(JSONB, default=list)
    evidence_notes: Mapped[str | None] = mapped_column(Text)
    blockers_json: Mapped[list] = mapped_column(JSONB, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (Index("ix_provider_audit_provider_time", "provider_key", "checked_at"),)


class DerivedFeatureSnapshot(Base):
    """Versioned derived value with exact point-in-time observation lineage."""
    __tablename__ = "derived_feature_snapshots"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    feature_family: Mapped[str] = mapped_column(String(64), index=True)
    feature_key: Mapped[str] = mapped_column(String(128), index=True)
    algorithm_version: Mapped[str] = mapped_column(String(64), index=True)
    game_year: Mapped[int] = mapped_column(Integer, index=True)
    market_segment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("market_segments.id"), index=True)
    card_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cards.id"), index=True)
    input_cutoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    value_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    source_observation_ids_json: Mapped[list] = mapped_column(JSONB, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (Index("ix_derived_feature_lookup", "feature_family", "card_id", "market_segment_id", "input_cutoff_at"),)


class ProviderReliabilitySnapshot(Base):
    __tablename__ = "provider_reliability_snapshots"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    provider_key: Mapped[str] = mapped_column(String(64), index=True)
    market_segment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("market_segments.id"), index=True)
    card_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cards.id"), index=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    dimensions_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    metrics_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class HistoricalImportBatch(Base):
    __tablename__ = "historical_import_batches"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    provider_key: Mapped[str] = mapped_column(String(64), index=True)
    source_format: Mapped[str] = mapped_column(String(32), index=True)
    source_uri: Mapped[str | None] = mapped_column(Text)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    game_year: Mapped[int] = mapped_column(Integer, index=True)
    market_segment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("market_segments.id"), index=True)
    native_historical: Mapped[bool] = mapped_column(Boolean, default=True)
    reconstructed: Mapped[bool] = mapped_column(Boolean, default=False)
    rows_seen: Mapped[int] = mapped_column(BigInteger, default=0)
    rows_written: Mapped[int] = mapped_column(BigInteger, default=0)
    rows_quarantined: Mapped[int] = mapped_column(BigInteger, default=0)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class RecommendationLedger(Base):
    __tablename__ = "recommendation_ledger"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    decision_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), index=True)
    market_segment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("market_segments.id"), index=True)
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("opportunity_candidates.id"), index=True)
    action: Mapped[str] = mapped_column(String(32), index=True)
    acquisition_min: Mapped[int | None] = mapped_column(Integer)
    acquisition_max: Mapped[int | None] = mapped_column(Integer)
    target_exit_min: Mapped[int | None] = mapped_column(Integer)
    target_exit_max: Mapped[int | None] = mapped_column(Integer)
    expected_net_profit: Mapped[int | None] = mapped_column(BigInteger)
    expected_holding_seconds: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    available_coin_balance: Mapped[int | None] = mapped_column(BigInteger)
    model_version: Mapped[str | None] = mapped_column(String(128), index=True)
    strategy_version: Mapped[str | None] = mapped_column(String(128), index=True)
    input_cutoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    evidence_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    source_observation_ids_json: Mapped[list] = mapped_column(JSONB, default=list)
    user_acted: Mapped[bool | None] = mapped_column(Boolean, index=True)
    execution_transaction_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("portfolio_transactions.id"), index=True)
    outcome_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class AccountConstraint(Base):
    __tablename__ = "account_constraints"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trading_accounts.id", ondelete="CASCADE"), index=True)
    game_year: Mapped[int] = mapped_column(Integer, index=True)
    transfer_list_capacity: Mapped[int | None] = mapped_column(Integer)
    unlisted_capacity: Mapped[int | None] = mapped_column(Integer)
    maximum_desired_exposure: Mapped[int | None] = mapped_column(BigInteger)
    per_card_exposure_limit: Mapped[int | None] = mapped_column(BigInteger)
    strategy_exposure_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    market_segment_exposure_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (UniqueConstraint("account_id", "game_year", name="uq_account_constraint_game"),)


class AccountMarketAccess(Base):
    __tablename__ = "account_market_access"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pk)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trading_accounts.id", ondelete="CASCADE"), index=True)
    market_segment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("market_segments.id", ondelete="CASCADE"), index=True)
    executable: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (UniqueConstraint("account_id", "market_segment_id", name="uq_account_market_access"),)
