# Implementation Plan — 2026-09-04

## Today: bootstrap order

1. **Repository + schema** — complete in this bootstrap.
2. **Official EA content collector** — running target: 120s cadence, immutable timestamped captures.
3. **Market API provider adapters** — FUT-DB + The Coin Printer adapters complete; API credentials/provider freshness still external dependencies.
4. **FC26 PC seed universe** — populate canonical card identities/source IDs as soon as an API key is available.
5. **2-minute PC price feed qualification** — measure source `updated_at` lag for every response. A poll every 2 minutes does not count as 2-minute market data if the source timestamp is stale.
6. **Shadow account** — create once market observations are flowing; predictions/decisions are immutable and fills require later observations.
7. **Feature materialization** — start after enough FC26 snapshots exist to create 2m/5m/15m/1h lagged features without backfill leakage.
8. **Model baselines** — naive + LightGBM/XGBoost before global neural training.

## September 5–17 FC26 rehearsal

- Maintain 24/7 cloud collectors/database.
- Timestamp every model prediction before outcomes.
- Evaluate source freshness/coverage every hour.
- Begin shadow trades only on cards whose price observations meet the data-quality threshold.
- Train structured models first; train global neural model on RTX 5080 once enough sequences exist.
- Keep FC26 data immutable as FC27 transition context.

## September 18 FC27 switch

- Add game_year=27 collectors immediately.
- Preserve FC26 pipeline and models.
- Start FC27 calibration weights low and increase with observed FC27 data volume/quality.
- Run regime divergence tests to determine when FC27 evidence overrides historical priors.
