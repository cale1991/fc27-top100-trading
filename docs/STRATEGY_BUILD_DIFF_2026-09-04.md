# Strategy Intelligence build diff — 2026-09-04

This phase extends `fc27-top100-trading-app-milestone-2026-09-04` in place. The PWA, Docker stack, collectors, dynamic universe, reference/execution distinction, verification workflow, portfolio accounting and `scripts/smoke_app.ps1` remain the baseline.

## Database/schema additions

Ten persistent tables were added, taking current SQLAlchemy metadata from 54 to 64 tables:

- `strategy_library`
- `strategy_aliases`
- `strategy_evidence`
- `strategy_cycle_assessments`
- `strategy_backtest_runs`
- `strategy_performance_snapshots`
- `opportunity_strategy_matches`
- `strategy_trader_performance`
- `strategy_discovery_candidates`
- `community_signal_strategy_links`

Migration: `migrations/versions/0005_strategy_intelligence.py`.

## New backend modules/services

- `src/fc27trader/strategy/models.py` — strategy contexts, definitions, matches and measured outcomes.
- `src/fc27trader/strategy/matching.py` — transparent live pattern recognizer.
- `src/fc27trader/strategy/backtest.py` — after-tax strategy metrics and dimensional breakdowns.
- `src/fc27trader/strategy/features.py` — numeric features/ensemble adapter.
- `src/fc27trader/strategy/decay.py` — cycle weighting and decay logic.
- `src/fc27trader/strategy/risk.py` — strategy-specific risk adjustment.
- `src/fc27trader/services/strategy_research.py` — persistent definitions/source evidence/structural-change seeding.
- `src/fc27trader/services/strategy_intelligence.py` — live matching and opportunity enrichment.
- `src/fc27trader/services/strategy_backtesting.py` — FC26-first measured backtest persistence/reassessment.
- `src/fc27trader/services/strategy_trader_reputation.py` — trader quality conditional on strategy.
- `src/fc27trader/services/strategy_discovery.py` — emerging unnamed quantitative-pattern registry.
- `src/fc27trader/api/routers/strategies.py` — research/active/discovery/detail APIs.
- `scripts/seed_strategies.py` and `scripts/run_strategy_backtests.py`.

## Modified production components

- `src/fc27trader/services/market_universe.py` — enriches the broad observable PC universe with strategy features; does not filter to a strategy list.
- `src/fc27trader/services/discovery.py` — persists point-in-time strategy matches.
- `src/fc27trader/opportunity/models.py` and `scoring.py` — additive Strategy Intelligence signal only.
- `src/fc27trader/features/definitions.py` — strategy similarity/performance/sample/decay features.
- `src/fc27trader/models/portfolio.py` — modest support/decay adjustment under the existing Transfer-Profit/turnover objective.
- `src/fc27trader/community/ingest.py` — links community calls to matching strategies.
- `src/fc27trader/services/app_queries.py` — opportunity detail includes human-readable historical-strategy matches.
- `src/fc27trader/scheduler/tasks.py`, `scheduler/schedules.py`, `config/polling.yaml` — scheduled strategy backtests and strategy-specific trader reputation.
- `docker-compose.yml` — strategy definitions/evidence seed during migration startup.

## Research/config files

- `config/strategies.yaml` — 30 research labels/mechanisms; explicitly not a production watchlist/playbook.
- `config/strategy_research_seed.yaml` — timestamped public source evidence across FIFA22/FIFA23/FC24/FC25/FC26, including supporting, mixed and contradictory observations.
- `config/strategy_structural_changes.yaml` — official rule/market-structure changes used for temporal validity.

Qualitative source evidence can never create a measured `PROVEN / REPEATED` classification. Container reseeding now also refuses to overwrite measured strategy status once performance samples exist.

## PWA changes

- `web/app/strategies/page.tsx` — Strategies / Research screen.
- `web/app/strategies/[slug]/page.tsx` — strategy evidence, measured results, live matches, trader specialization and temporal validity.
- `web/app/opportunities/[id]/page.tsx` — concise `Pattern resembles ...` section.
- `web/app/more/page.tsx` and `web/components/AppShell.tsx` — mobile access without cluttering the primary trading workflow.

## Quantitative integrity

The repository currently contains source/mechanism evidence but not enough long-running FC26 PC observations to truthfully publish historical strategy returns. Empty strategy samples remain `insufficient_data`; no performance snapshot is written. Closed-trade-only samples never fake acquisition probability. The backtester separately joins all strategy-tagged shadow execution attempts—including misses—to estimate acquisition probability, acquisition delay and execution quality; if none exist, those metrics remain null.
