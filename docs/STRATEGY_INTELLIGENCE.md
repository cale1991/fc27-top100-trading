# Strategy Intelligence

Status: implemented infrastructure; initial source evidence seeded; quantitative historical performance is not yet claimed unless a measured FC26 PC backtest/shadow sample exists.

## Purpose

Strategy Intelligence is an evidence layer over the dynamic production market universe. It does **not** define a fixed watchlist and does not force a candidate into a named playbook.

Production remains:

`broad observable PC market -> discovery/filtering -> opportunity scoring -> ranked candidates -> execution verification -> trade decision`

A strategy match adds historical/context evidence to that flow. A card with no named strategy match remains fully eligible.

## Persistent data

The subsystem adds:

- `strategy_library` — canonical definition, mechanism, regimes/categories, entry/exit/failure fields, EA-tax/EA-intervention sensitivity, first/last observed cycle and viability state.
- `strategy_aliases` — community terminology and alternate names.
- `strategy_evidence` — timestamped public source evidence, direction, source quality, cycle and provenance.
- `strategy_cycle_assessments` — structural differences/rule changes and decay priors by game cycle/platform.
- `strategy_backtest_runs` — immutable execution record for a strategy evaluation dataset/config.
- `strategy_performance_snapshots` — measured performance only; no row is written when no outcomes exist.
- `opportunity_strategy_matches` — point-in-time recognition between a live candidate and one or more strategies.
- `strategy_trader_performance` — trader reputation conditional on strategy, not follower count.
- `strategy_discovery_candidates` — unnamed quantitative patterns awaiting evidence/review.
- `community_signal_strategy_links` — timestamped mapping of community calls to strategy mechanisms.

## Evidence classes

Allowed library labels:

- `PROVEN / REPEATED`
- `STRONG EVIDENCE`
- `PLAUSIBLE`
- `INCONCLUSIVE`
- `OUTDATED`
- `COMMUNITY FOLKLORE`

Public guides, interviews and selected trade examples alone can never create `PROVEN / REPEATED`. The qualitative seeder tops out at `STRONG EVIDENCE`; measured promotion uses FC26 PC outcomes and conservative sample thresholds.

Contradictory/failure observations are persisted rather than discarded. A strategy can therefore carry `mixed_evidence_unmeasured` or later decay to `OUTDATED`.

## Initial strategy universe

`config/strategies.yaml` currently contains 30 named mechanisms, including fodder/SBC/rating bands, out-of-pack scarcity, promo panic/rebound, reward and content supply, weekend/overnight timing, bidding/undercuts/lazy listing/mass bidding, high-volume and high-value flipping, meta/Icon/Hero, chemistry/Evo/substitutes, discard, leaks, early-cycle demand, and pre/post-content patterns.

These 30 definitions are **research labels**, not the production trading universe.

## Live matching

`fc27trader.strategy.matching` provides a transparent baseline recognizer. It compares the current candidate context to historical mechanisms using:

- card category
- market regime
- content/catalyst terms
- in-pack/out-of-pack state
- promo state
- current price movement
- liquidity/demand
- content timing

Each match records similarity, confidence, matched reasons and current structural differences.

`fc27trader.services.strategy_intelligence.enrich_opportunity_inputs()` runs over the broad market input batch. It adds:

- match count
- best similarity/confidence
- measured historical success rate when available
- measured median return when available
- historical sample size
- structural/decay risk
- strategy-specific community intelligence

Qualitative strategy evidence receives only a small recognition prior. Measured performance can earn more weight, but Strategy Intelligence remains one component of opportunity scoring rather than an override.

## Model integration

Numeric feature definitions include:

- `strategy_match_count`
- `strategy_best_similarity`
- `strategy_best_confidence`
- `strategy_weighted_success_rate`
- `strategy_weighted_median_return`
- `strategy_historical_sample_size`
- `strategy_decay_risk`

`strategy_model_signal()` provides an ensemble-compatible adapter. If there is no measured sample, its model confidence is zero; the named historical pattern therefore cannot masquerade as an independently validated predictive model.

The turnover-aware portfolio allocator can use `strategy_support` and `strategy_decay_risk` as modest adjustments, while current expected Transfer Profit, turnover, liquidity, capacity and downside remain primary.

## Backtesting

FC26 PC is the first quantitative target.

`services/strategy_backtesting.py` currently evaluates labeled closed shadow trades. It records:

- total net Transfer Profit
- ROI
- profit/hour
- profit/deployed million
- capital turnover
- hit rate
- drawdown where measured
- profitable-exit probability
- median holding time
- liquidity where measured
- sample-aware confidence
- breakouts by market regime/event when labels are available

Closed-trade samples never estimate acquisition probability by themselves because conditioning on completed trades would falsely imply 100% acquisition. The backtester now joins all strategy-tagged `shadow_execution_attempts` through `shadow_orders`, including misses, and uses that independent sample for acquisition probability, realized acquisition delay and execution-quality diagnostics. If no tagged attempts exist, those acquisition metrics remain null.

The scheduler refreshes a strategy only when its labeled closed-trade sample has grown. Empty datasets produce `insufficient_data` and no performance snapshot. Acquisition-attempt sample size is stored separately so search/fill quality cannot inflate trade hit rate.

## Temporal validity / strategy decay

Default evidence priors are deliberately descending:

`FC26 1.00 > FC25 0.72 > FC24 0.52 > FIFA23 0.36 > FIFA22 0.25`

`config/strategy_structural_changes.yaml` seeds documented structural breaks separately from performance results, including the introduction/expansion of Evolutions and FC26 reward/market-access changes.

`strategy_decay_score()` combines measured deterioration with structural difference. A structural prior is explicitly marked qualitative; it is not a claim that profitability fell by the same percentage.

During FC27, FC27 outcomes should progressively dominate these priors.

## Community link

Community calls are matched to strategy mechanisms at ingestion time. Resolved outcomes then populate `strategy_trader_performance`.

A trader can therefore have low overall reputation but high measured skill in a particular strategy. Live community weighting uses that strategy-specific score, extraction confidence, match confidence and recency. Follower count is intentionally absent.

## Emerging strategies

`record_discovered_pattern()` registers unnamed quantitative patterns in `strategy_discovery_candidates`. A pattern can become `reviewable` after configurable sample/confidence thresholds, but is **never automatically promoted** into the library. Promotion requires evidence/review so transient overfit does not become a permanent strategy label.

## App/API

PWA:

- `/strategies` — strategy research table, active live matches, measured/source-only state, trend/decay and emerging patterns.
- `/strategies/[slug]` — mechanism, evidence, measured results, live matches, trader specialization and temporal validity.
- Opportunity detail — simple `Pattern resembles ...` section with similarity, measured sample and current differences.

API:

- `GET /strategies`
- `GET /strategies/active`
- `GET /strategies/discoveries`
- `GET /strategies/{slug}`

## Current limitation

The repository does not yet contain a sufficiently long FC26 PC historical market dataset to truthfully report strategy profitability. The library therefore starts as source evidence + mechanisms, while FC26 shadow trading builds the measured layer.
