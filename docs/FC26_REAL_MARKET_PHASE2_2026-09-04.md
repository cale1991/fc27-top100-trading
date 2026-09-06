# FC26 Real Market Phase 2 — Multi-source, Multi-market Intelligence

## Scope

Phase 2 extends the accepted Phase-1 application without replacing its accounting, verification, Strategy Intelligence, API, PWA, Celery or PostgreSQL architecture. The user's current execution market remains FC26 PC; intelligence storage supports multiple title-specific market segments.

## First-class market segments

FC26 seeds `PC`, `PLAYSTATION`, `CONSOLE_GENERIC`, `CONSOLE_SHARED`, `SWITCH`, and `UNKNOWN`. Only FC26 PC is user-executable by default. These are rows in `market_segments`, not universal assumptions about every EA FC title. FC27 receives its own configurable segment rows.

Every price-like observation retains a market-segment foreign key when the provider semantics establish one. Unknown data remains UNKNOWN.

## Evidence semantics

- `EXECUTION_OBSERVATION`: fresh evidence such as a user-entered PC BIN ladder. Portfolio marks can use compatible execution observations only.
- `REFERENCE_PRICE`: provider-specific valuation/reference observations; never silently executable.
- `MARKET_CONTEXT / MARKET_MOVE`: event stream telling us a provider observed a change; not a complete snapshot.
- `CONTENT`: EA/provider catalyst event kept separately.

## FUTZIP

A public-RSS collector handles `movers.xml`, `new.xml`, and `sbc.xml` every five minutes. It supports GUID dedupe, immutable append-only events, raw provenance, parser/schema versioning, ETag/Last-Modified conditional requests, HTTP 304, bounded transient retries, feed state and collection-gap risk.

FUTZIP's public RSS mover items audited during Phase 2 do not encode enough platform identity to map each move to PC/console/Switch. Movers therefore normalize to `UNKNOWN / MARKET_CONTEXT`; they create zero market-specific reference or execution rows. New-card identity resolution remains conservative. SBC feed records are mirrored into content/catalyst architecture below EA official authority.

## Optional Parse.bot/FUTBIN provider

`ParseBotFutbinCollector` is implemented as `OPTIONAL_STRUCTURED_PROVIDER`, disabled by default. It uses Parse's documented authenticated wrapper and never implements direct FUTBIN scraping.

Configuration:

```text
PARSE_API_KEY=
PARSE_FUTBIN_ENABLED=false
```

`price_pc` normalizes to PC `REFERENCE_PRICE`. `price_ps` stays on the provider-labelled PlayStation segment rather than being generalized to shared console. Raw responses, endpoint, retrieval timestamp, provider ID and parser version are retained. Suspicious/invalid prices are quarantined before consensus.

Collection is budget-aware and supports catalogue bootstrap/metadata refresh, deterministic hot-set targeting and on-demand one-page validation. Full-universe high-frequency polling is intentionally absent.

## Point-in-time correctness and lineage

Reference/execution queries used by derived features filter by what was known at the requested cutoff and exclude non-VALID rows. Backfilled provider timestamps do not make an observation available before retrieval/import. Derived consensus snapshots retain algorithm version, input cutoff and source observation IDs. Formula revisions append new derived rows rather than rewriting old ones.

## Event-stream coverage and gaps

`provider_feed_states` retains last poll/success, oldest/newest event currently exposed, inferred coverage window, conditional-HTTP state and gap status (`COMPLETE_WINDOW`, `POSSIBLE_GAP`, `CONFIRMED_GAP`, `UNKNOWN_COVERAGE`). A mover event stream is not treated as a complete market snapshot.

## Data quality

Normalized reference/feed records carry `VALID`, `SUSPECT`, `QUARANTINED` or `REJECTED_NORMALIZATION`. Raw payloads remain preserved. Consensus uses only compatible VALID observations; disagreement remains a feature rather than being silently resolved.

## Multi-provider consensus

Consensus is calculated separately per card + market segment and records provider count, fresh count, median/weighted median, min/max, spread, IQR, age, number within 1/2%, disagreement, stale ratio, observation density, platform certainty, reference/execution divergence and exact source observation IDs.

UNKNOWN observations are excluded from PC/PlayStation/console/Switch consensus.

## Cross-market features

The feature layer can represent PC, provider-labelled PlayStation, generic/shared console and Switch separately. It calculates ratios/spreads where data exists. Lead/lag, rolling correlation and convergence probability deliberately remain unmeasured/NULL until enough historical samples exist; no assumption that console leads PC is encoded.

A non-PC research signal can trigger a request for fresh PC BIN evidence without copying the non-PC quote into PC reference/execution state.

## Provider optionality

No third-party provider is required for startup. FUTZIP, Parse/FUTBIN, FUT-DB and The Coin Printer can fail independently while Portfolio/manual execution observations/application access remain usable.

FUT-DB's observed zero-quota state maps to `NO_QUOTA` and backs off rather than repeatedly hammering the API. The Coin Printer stays optional until a key is supplied.

## Additional information-base tables

Phase 2 adds/uses provider feed events/state, provider budget state, provider rights/audit records, versioned derived features, provider reliability snapshots, historical import batches, recommendation ledger, account constraints and account-market access. Current SQLAlchemy metadata contains 77 tables.

## Release environment limitation

The packaging sandbox has no Docker/Podman/PostgreSQL binary and outbound package/runtime DNS is blocked. Therefore the Python/migration-structure/static frontend/release-package checks can run here, but a real Docker build + PostgreSQL migration + HTTP collection must be run on the vacation PC. No live FUTZIP/Parse ingestion is claimed from this packaging environment.
