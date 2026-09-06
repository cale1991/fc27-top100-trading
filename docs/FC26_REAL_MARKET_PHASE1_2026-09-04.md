# FC26 PC Real Market Data — Phase 1

## Status

This phase replaces the demo-only universe path with credential-ready ingestion for a broad FC26 card universe and append-only PC **reference** observations. It does **not** claim that third-party reference prices are executable Transfer Market listings.

### Provider roles

- **FUT-DB — METADATA**: documented FC26 player/entity API. Requires `FUTDB_API_KEY`. Base database access is available with an API key; some fields are premium.
- **FUT-DB — REFERENCE**: documented per-player PC price endpoint. Requires `FUTDB_API_KEY` plus Premium access and `FUTDB_PREMIUM_PRICES_ENABLED=true`. Provider `pc.priceUpdate` is persisted separately from retrieval time.
- **The Coin Printer — METADATA / REFERENCE**: documented read-only approved-partner player search API. Requires a paid/issued `THECOINPRINTER_API_KEY`. `pc_price` and `updated_at` are persisted as reference evidence.
- **EA official news — CONTENT**: existing official EA collector retained.
- FUTBIN/FUT.GG/FUTWIZ remain manual/licensed research surfaces only; no prohibited scraper or reverse-engineered private endpoint was added.

## Card universe

FUT-DB is the primary broad-universe seed when credentials are configured. Stored fields include provider ID, EA resource ID where supplied, FUTBIN/FUTWIZ cross IDs supplied by FUT-DB, name, rating, positions, league, club, nation, rarity/version, attributes, PlayStyles/PlayStyle+, image identifiers/URLs, and provider identity confidence.

Cross-provider mapping order is conservative:

1. existing provider ID;
2. exact EA resource ID;
3. unique exact identity fingerprint;
4. otherwise create a distinct provider card rather than silently merging versions.

The fixed 50-card basket remains qualification/testing-only and is not used to define the production universe.

## Reference observation semantics

Each retrieval appends an observation containing:

- canonical card;
- platform `pc`;
- provider/source;
- provider role;
- price;
- provider timestamp when supplied;
- our retrieval/observation timestamp;
- age at retrieval;
- raw-ingest provenance;
- evidence class;
- uncertainty/confidence metadata;
- immutable market/content context snapshot.

Reprocessing the exact same retrieval is idempotent. Polling the same unchanged provider price later creates a new time-series row because the later retrieval time itself is evidence about persistence/staleness.

`ReferencePriceObservation` is never converted into `ExecutionObservation` by these collectors. Portfolio liquidation marks still require execution evidence such as a trusted fresh execution feed or manual lowest-BIN verification.

## Adaptive collection

FUT-DB price requests are selected dynamically from:

1. active portfolio positions;
2. dynamic attention targets;
3. active opportunities;
4. missing/stale reference coverage.

There is no permanent production watchlist.

Default cadence is deliberately below provider limits:

- FUT-DB universe refresh: every 6 hours;
- FUT-DB reference selection: every 30 minutes, up to `FUTDB_PRICE_REQUESTS_PER_CYCLE` adaptive targets;
- The Coin Printer recent pages: every 30 minutes when credentials exist;
- EA content: every 2 minutes.

These are scheduler request cadences, **not** claims about provider-side data freshness.

## Provider health

`provider_health` records last request/success/error, request/error counts, card coverage, provider timestamp, dynamically computed observation age, request latency, and rate-limit state. System shows credential-missing/configured-not-tested states before the first successful response.

## Phase-1 opportunity gate

The application does not manufacture BUY calls from a reference quote alone. Current production discovery requires real reference history plus measured predictive/acquisition/exit evidence before a card can be promoted. When future evidence supports an attractive candidate but execution price is uncertain, the existing `MANUAL_VERIFICATION_REQUEST` flow supplies the current 5–10 PC BIN ladder.

## Setup

Add credentials to `.env` only when obtained legitimately:

```dotenv
FUTDB_API_KEY=
FUTDB_PREMIUM_PRICES_ENABLED=false
THECOINPRINTER_API_KEY=
```

Then run the normal stack. Optional one-shot checks inside the API/worker image:

```bash
python scripts/collect_once.py futdb-universe --max-pages 2
python scripts/collect_once.py futdb-prices
python scripts/collect_once.py tcp
python scripts/realdata_status.py
```

Do not set `FUTDB_PREMIUM_PRICES_ENABLED=true` unless the supplied key actually has premium price access.

## Current build-environment collection result

No FUT-DB or The Coin Printer credentials were present in the build environment, and the build sandbox has no outbound DNS for the Python/container runtime. Therefore this build has **not** claimed a successful card/price API response and has not fabricated FC26 observations. Actual card/priced-card counts from the build run are zero. The next successful run must occur on the vacation PC/cloud host after credentials are supplied.
