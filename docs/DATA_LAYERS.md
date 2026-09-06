# Raw vs Processed Data Contract

## Layer 0 — immutable raw
Every successful public HTTP/API response is written before parsing and tied to `raw_ingests` with source/provider timestamps, observation time, retrieval time, checksum and object URI.

## Layer 1 — normalized observations
Separate semantics are mandatory:

- `reference_price_observations`: approximate fair-value anchors with provider timestamp, observed age, historical provider error, uncertainty and confidence.
- `execution_observations`: fresh current PC market evidence suitable for an immediate decision, including trusted live data or user-supplied BIN samples.
- `market_snapshots` / listing/sale observations: general normalized market history/context.
- content/SBC/Evo/pack/event tables.

Reference observations are never silently promoted to executable quotes.

## Layer 2 — discovery and attention
`opportunity_candidates` represents the current ranked opportunity set discovered from the broadest practical observable PC market. `attention_allocations` is time-bounded and continuously recomputed. `collection_targets` materializes those current priorities for the scheduler.

## Layer 3 — point-in-time features
Features read only observations knowable at the prediction timestamp. Reference age/error/uncertainty and fresh execution evidence remain separate inputs.

## Layer 4 — shadow/model artifacts
Predictions, orders, acquisition attempts, fills and model artifacts remain immutable after outcome observation. `shadow_execution_attempts` separates signal quality from execution quality.
