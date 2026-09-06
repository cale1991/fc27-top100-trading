# Locked Design Update — 2026-09-04

## Existing files that were incorrect

- `README.md`: incorrectly treated two <=5-minute providers as a global blocker.
- `src/fc27trader/validation/evaluate.py`: stale provider data caused total provider failure instead of role classification.
- `src/fc27trader/validation/select.py`: required two PASS providers and raised when unavailable.
- `src/fc27trader/validation/gate.py`: treated hot-feed qualification as a system-wide permission gate.
- `src/fc27trader/validation/persist.py`: persisted only a single `hot_market` role.
- `scripts/prequalification_report.py` and `scripts/select_hot_sources.py`: non-zero/exception behavior implied the project must stop.
- `config/polling.yaml`: implied a fixed hot/broad watchlist tied to a primary live provider.
- `config/provider_validation.yaml`: used <=300 seconds as a general hard gate rather than HOT_REFERENCE qualification.
- `config/shadow_rules.yaml` and `shadow/execution.py`: buy fills could be interpreted as a quoted market price becoming an achievable acquisition.
- `docs/PROVIDER_VALIDATION_2026-09-04.md`, `DATA_SOURCES.md`, `COLLECTOR_ARCHITECTURE.md`, `SHADOW_TRADING.md`, `FEATURE_PIPELINE.md`, `DATA_LAYERS.md`: documented the old blocker/watchlist assumptions.

## Modified files

The files above were changed. In addition:

- `src/fc27trader/db/models.py`
- `src/fc27trader/db/repositories.py`
- `src/fc27trader/features/definitions.py`
- `src/fc27trader/scheduler/tasks.py`
- `src/fc27trader/api/app.py`
- `config/provider_catalog_fc26.yaml`
- `config/validation_basket_fc26.yaml`
- `tests/test_provider_validation.py`
- `tests/test_shadow_execution.py`

## New implementation

### New tables

- `reference_price_observations`
- `execution_observations`
- `opportunity_candidates`
- `manual_verification_requests`
- `manual_verification_responses`
- `attention_allocations`
- `acquisition_opportunity_observations`
- `shadow_execution_attempts`

### New services/classes

- `opportunity/models.py`: broad-market opportunity input/ranked output contracts.
- `opportunity/scoring.py`: dynamic discovery and quality ranking.
- `opportunity/acquisition.py`: empirical undercut/acquisition distribution model with no universal discount assumption.
- `services/attention.py`: current-state attention scoring and cadence assignment.
- `scheduler/attention_targets.py`: materializes expiring attention decisions into `collection_targets`.
- `services/manual_verification.py`: expected-information-value gate and request drafting.
- `services/verification_repository.py`: request persistence.
- `services/discovery.py`: persists each broad-market discovery cycle and supersedes stale candidates.
- `features/reference_features.py`: converts provider age/error/confidence into explicit uncertainty features.
- `domain/observations.py`: reference and execution observation contracts.

## Provider classification

Provider qualification now assigns one or more roles:

- `HOT_REFERENCE`: controlled basket passes coverage/rights checks and effective staleness <=300s.
- `REFERENCE`: useful approximate PC value anchor even if older than 5 minutes.
- `HISTORICAL`: valid for trend/model/history use.
- `METADATA`: card/market metadata.
- `CONTENT`: content/event feed.
- `MANUAL_BENCHMARK`: manually supplied/licensed benchmark only.

The 50-card basket remains mandatory for controlled price-provider benchmarking, but it is explicitly marked `production_use_forbidden: true`.

## Dynamic production discovery

`persist_discovery_cycle()` receives the broadest currently observable PC market, scores current expected opportunity, writes ranked `opportunity_candidates`, and supersedes prior candidates not retained. There is no permanent candidate allow-list.

Scores combine expected profit, acquisition probability, exit probability, liquidity, sell-through, profit/hour, capacity, catalyst/context, downside, EA intervention risk, uncertainty and opportunity cost. Quality thresholds cap noise rather than forcing a target number of trades.

## Manual verification flow

1. A high-value candidate lacks strong enough execution data.
2. `verification_value()` estimates whether interrupting the user has positive information value.
3. If positive, a `manual_verification_requests` row is created with exact card, reason, reference timestamp/uncertainty, acquisition range, actionable threshold and required BIN sample.
4. User/API response is stored in `manual_verification_responses`.
5. The same data is normalized into a confidence-1.0 `execution_observations` row.
6. The request resolves and the linked candidate is immediately marked actionable/not-actionable against the current threshold or queued for model reevaluation.

## Reference uncertainty features

`derive_reference_features()` emits:

- `reference_price`
- `reference_age_seconds`
- `reference_provider_error_pct`
- `reference_stated_uncertainty_pct`
- `reference_uncertainty_pct`
- `reference_confidence`
- `execution_price`
- `execution_age_seconds`
- `reference_execution_gap_pct`

Older/error-prone anchors receive less weight; a fresh execution observation overrides them for immediate decision logic.

## Shadow execution changes

There are now two buy paths:

1. **Execution-observation path:** fill only from a post-decision executable observation/listing at/below the limit after conservative slippage.
2. **Acquisition-model path:** if only a reference anchor exists, fill probability, expected buy price, delay and quantity come from the learned undercut distribution. Reference uncertainty reduces effective acquisition probability.

`shadow_execution_attempts` records signal quality and execution quality separately.
