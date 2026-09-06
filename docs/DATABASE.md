# Database Schema

PostgreSQL is the source of truth; all timestamps are timezone-aware UTC.

## Provenance/raw
`sources`, `raw_ingests`, `collector_runs`, `data_quality_incidents`.

## Card identity/graph
`cards`, `card_source_ids`, `card_relationship_edges`.

## General market/context
`market_snapshots`, `market_index_snapshots`, `market_listing_observations`, `completed_sale_observations`.

## Observation semantics
- `reference_price_observations` — third-party fair-value anchors with provider timestamp, age, historical provider error, uncertainty and confidence.
- `execution_observations` — fresh current PC market evidence used for immediate execution decisions.
- `acquisition_opportunity_observations` — observed undercut/search outcomes used to learn acquisition probability/price/delay/quantity distributions.

## Dynamic universe/attention
- `opportunity_candidates` — current ephemeral scored/ranked opportunities.
- `attention_allocations` — expiring observation-attention decisions.
- `collection_targets` — materialized current scheduler state; not a permanent watchlist.
- `manual_verification_requests`, `manual_verification_responses` — user-interrupt/response lifecycle and provenance.

## Content/event engine
`content_events`, `event_impacts`, `sbcs`, `sbc_requirements`, `evolutions`, `evolution_requirements`, `packs`, `pack_probabilities`.

## Predictions/signals
`predictions`, `signals`.

## Shadow trading/portfolio
`shadow_accounts`, `shadow_orders`, `shadow_fills`, `shadow_trades`, `shadow_execution_attempts`, `portfolio_snapshots`.

`shadow_execution_attempts` is specifically for separating signal quality from execution quality and recording modeled acquisition probability/delay/quantity plus reference/execution provenance.

## Provider validation
`provider_validation_runs`, `provider_validation_observations`, `provider_qualifications`.

`provider_qualifications.role` now stores one row per role (`hot_reference`, `reference`, `historical`, `metadata`, `content`, `manual_benchmark`) rather than one global hot-market pass/fail.

## Modeling
`model_runs`.

Current SQLAlchemy metadata: **39 tables**. Canonical PostgreSQL DDL is in `docs/schema_postgres.sql`.
