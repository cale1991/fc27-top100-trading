# FC26 PC Provider Validation — 2026-09-04

## Scope

`config/validation_basket_fc26.yaml` is a **fixed 50-card controlled benchmark only**. It covers 12 fodder, 10 meta golds, 14 Icons/Heroes and 14 promos. It is forbidden as the production trading universe.

The benchmark continues to measure PC coverage, timestamp/freshness evidence, FUTBIN price error, request latency, rate limits, fields, cost, terms and upstream provenance.

## Role classification

A provider is no longer globally PASS/FAIL based on <=5-minute freshness. The controlled benchmark assigns useful roles:

- `HOT_REFERENCE` — authorized PC reference feed with effective staleness <=300 seconds under the qualification test.
- `REFERENCE` — approximate current-value anchor; may be older than five minutes and must carry age/error/uncertainty.
- `HISTORICAL` — valid for trend/history/model context.
- `METADATA` — card/market metadata.
- `CONTENT` — event/content data.
- `MANUAL_BENCHMARK` — manual/licensed comparison only; no automated ingestion under current rights.

Request latency is telemetry only. It is never treated as provider data freshness.

## Current provider map

| Provider | Current useful role(s) | HOT_REFERENCE state | Important evidence |
|---|---|---|---|
| FUTBIN | MANUAL_BENCHMARK | manual only | benchmark surface; automated scraping requires permission under current terms |
| FUT.GG | MANUAL_BENCHMARK | not qualified | automated surface access restricted under current terms |
| FUTWIZ public surface | MANUAL_BENCHMARK | not qualified | observed PC ages ranged from seconds/minutes to many hours |
| FUTNext / FC Enhancer | MANUAL_BENCHMARK pending permission | inconclusive | advertises real-time prices but observed endpoint lacks authoritative timestamp/SLA |
| The Coin Printer | REFERENCE, HISTORICAL, METADATA | not qualified | API has PC price + `updated_at`; provider states refresh multiple times/day |
| FUT-DB | REFERENCE, HISTORICAL, METADATA | not qualified | documented price freshness 30 minutes to 24 hours |
| Parse.bot FUTBIN wrapper | none for production | not qualified | wrapper does not solve upstream rights/freshness |
| EA Web/Companion internal market | MANUAL_BENCHMARK/ground truth only | manual only | direct market state, but automated access is outside project boundary |

The original evidence remains in `data/validation/provider_prequalification_2026-09-04.csv`, now with `classified_roles` and `hot_reference_status` columns.

## 50-card test behavior

For price roles, the controlled test still requires all 50 paired cards and category coverage. A stale authorized provider may therefore PASS the controlled benchmark as `REFERENCE`/`HISTORICAL` while failing only `HOT_REFERENCE`.

Missing timestamps do not destroy `REFERENCE` utility. They simply prevent `HOT_REFERENCE` qualification unless repeated propagation tests prove <=300-second effective freshness.

## Redundancy

Two independently sourced `HOT_REFERENCE` providers are desirable but optional. `select_provider_pair()` returns `None` rather than stopping the system when no independent pair exists. Reference/history/model work and manually verified execution remain valid.
