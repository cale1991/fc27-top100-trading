# Real Collection Run — 2026-09-04

## Market-provider run result

This build does **not** claim a successful FUT-DB or The Coin Printer data response.

Build-environment credential state:

- `FUTDB_API_KEY`: not configured
- `FUTDB_PREMIUM_PRICES_ENABLED`: false
- `THECOINPRINTER_API_KEY`: not configured

Build-environment outbound runtime probes also failed at DNS resolution for FUT-DB, The Coin Printer and EA. Therefore the only valid real-ingestion counts for this build environment are:

- successfully tested live FC26 market providers: **0**
- FC26 cards actually ingested from a real market API: **0**
- cards with actually ingested PC reference prices: **0**
- real PC reference observations: **0**
- measured provider update frequency from a successful run: **N/A**
- measured provider staleness from a successful run: **N/A**

Public documentation was verified separately to ensure the adapters target current documented interfaces. Documentation/website figures are deliberately not counted as ingested data.

## Access required for the first real vacation-PC run

### FUT-DB

- Base FC26 database: API key required.
- Current public site advertises API-key access and a large FC26 database.
- Player price endpoint is Premium.
- Current Premium plan shown publicly: €79/month, 20,000 requests/day.
- Provider states price updates range roughly 30 minutes to 24 hours depending on rating/rarity.
- Role in this project: `METADATA`, `REFERENCE`, `HISTORICAL`; never execution evidence.

### The Coin Printer

- API key required; no self-service key.
- Provider documents paid approved-partner access after contact/payment.
- 60 requests/minute per key.
- Player response contains `pc_price` and `updated_at`.
- Provider publicly states prices are refreshed multiple times per day.
- Role: `METADATA`, `REFERENCE`, `HISTORICAL`; not `HOT_REFERENCE` from current freshness evidence.

### EA official content

No credential is required for the existing official-news collector. Its public FC26 news surface was independently reachable during research, but the packaged Python runtime could not be network-smoke-tested inside this sandbox because outbound DNS is blocked.

## First run after credentials are added

On the vacation PC/cloud host:

```powershell
# after adding FUTDB_API_KEY to .env
docker compose exec worker python scripts/collect_once.py futdb-universe --max-pages 2

docker compose exec worker python scripts/realdata_status.py
```

If the sample succeeds, remove `--max-pages 2` for the full universe sync.

For Premium FUT-DB price access:

```dotenv
FUTDB_PREMIUM_PRICES_ENABLED=true
```

Then:

```powershell
docker compose exec worker python scripts/collect_once.py futdb-prices
```

For The Coin Printer after an issued key is added:

```powershell
docker compose exec worker python scripts/collect_once.py tcp
```

System should then show real last-success time, card coverage, latency, rate state and provider-age metrics.
