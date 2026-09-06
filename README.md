# FC27 Top 100 Trading

Multi-market EA SPORTS FC Ultimate Team intelligence system with the current user execution market set to PC. FC26 is the live rehearsal cycle; FC27 can become the active title without schema redesign.

## First usable application

The repository now includes a responsive Next.js PWA in `web/` backed by the existing FastAPI/PostgreSQL/Celery system.

Normal operation happens through the app, not CSVs, notebooks or database tables.

Main screens:

- **Now** — current best action, capital/Transfer Profit, verification needs, urgent portfolio actions and market/content activity.
- **Opportunities** — actionable PC candidates first, with compatible cross-market research context kept separate.
- **Verify** — submit current lowest PC BIN listings and/or a screenshot; confidence depends on sample quality and age.
- **Portfolio** — manual purchase/sale recording with exact 5% EA tax and realized Transfer Profit accounting.
- **Market** — card/version research with separate PC/PlayStation/provider-console/Switch/UNKNOWN evidence, reference/execution history, mover events and catalysts.
- **Activity** — readable event timeline.
- **Community** — trader calls and measured reputation.
- **Strategies** — historical strategy research, measured FC26 performance, live pattern matches, decay and trader specialization.
- **System** — collector/provider/model/service health.

The fixed 50-card basket in `config/validation_basket_fc26.yaml` remains **provider qualification/testing only**. It is not a production watchlist.

## Vacation-PC first boot

Use Docker Desktop on Windows 11:

```powershell
Copy-Item .env.example .env
docker compose up -d --build
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_app.ps1
```

Open:

```text
http://localhost:3000
```

Full instructions: `docs/VACATION_PC_SETUP_2026-09-04.md`.

## Backend development

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
pytest -q
```

Current Phase-2 validation is recorded in `docs/FC26_REAL_MARKET_PHASE2_2026-09-04.md`; run `pytest -q` for the packaged build count.

## Data roles

Third-party market data is classified by use, not globally accepted/rejected:

- `HOT_REFERENCE`
- `REFERENCE`
- `HISTORICAL`
- `METADATA`
- `CONTENT`
- `MANUAL_BENCHMARK`

Reference prices are valuation/search anchors. Fresh execution observations override them for immediate trade decisions.

## Dynamic trading flow

```text
broad observable PC market
  -> discovery/filtering
  -> opportunity scoring
  -> ranked candidates
  -> execution verification when information value warrants it
  -> trade decision
  -> manual EA execution
  -> portfolio ledger
```

Collection attention is recomputed continuously. Active positions, strong signals, catalysts, rapid movement and unusual volume receive more observation budget; irrelevant cards fall out of the active set.

## Manual verification confidence

Confidence is configurable in `config/manual_verification.yaml` and is no longer hard-coded to 1.0.

Fresh screenshot + 5+ exact listings receives the highest starting confidence; exact manual samples receive slightly less; a single/approximate value receives materially less; all decay with observation age.

## Community / public AI trader

The schema/services now support:

- permitted Community Intelligence ingestion into the core timestamped event stream.
- trader directional/after-tax/alpha/drawdown/timing/category/horizon reputation.
- crowding detection.
- immutable public prediction ledger.
- official X API posting adapter (disabled until a user-authorized token is configured).
- transparent-AI persona continuity and anti-slop preflight.
- `SOCIAL_MARKET_IMPACT` measurements.
- explicit rejection of private portfolio fields from public prediction state.

No unofficial EA Transfer Market buying/selling automation is included.

## RTX 5080 split

24/7 services do not depend on the main PC. The RTX 5080 is reserved for heavy GPU training/sweeps and exports model artifacts back to central storage. See `docs/CLOUD_LOCAL_SPLIT.md` and the vacation-PC setup file.


## Strategy Intelligence

Historical FIFA/EA FC strategies are persisted as evidence/features, not a fixed production playbook. The initial library contains 30 named mechanisms and timestamped source evidence across FIFA22/FIFA23/FC24/FC25/FC26. Source anecdotes never become measured profitability automatically. FC26 PC shadow/backtest outcomes populate performance, temporal decay and strategy-specific trader reputation as data accumulates.

Research docs:

- `docs/STRATEGY_INTELLIGENCE.md`
- `docs/HISTORICAL_STRATEGY_RESEARCH_PLAN_2026-09-04.md`
- `docs/STRATEGY_RESEARCH_INITIAL_FINDINGS_2026-09-04.md`


## FC26 real-market Phase 1

The production Market screen now reads the broad persisted FC26 card universe rather than the 50-card validation basket. Legitimate provider adapters are included for FUT-DB and The Coin Printer, but they remain disabled/no-op until their required API credentials are supplied. Their PC prices are append-only **reference anchors**, never Portfolio executable marks.

See `docs/FC26_REAL_MARKET_PHASE1_2026-09-04.md` for credential requirements, one-shot collector commands, adaptive polling and the current real-run status.


## FC26 real-market Phase 2

Phase 2 makes market segments first-class and adds multi-source/point-in-time data quality infrastructure. Public FUTZIP RSS is collected as immutable event/context data; unknown-platform mover events never become PC reference prices. Parse.bot/FUTBIN is an optional structured reference provider, disabled by default and activated only with `PARSE_FUTBIN_ENABLED=true` plus `PARSE_API_KEY`. FUT-DB and The Coin Printer remain optional.

Useful commands:

```powershell
docker compose exec api python scripts/collect_once.py futzip-movers
docker compose exec api python scripts/collect_once.py futzip-new
docker compose exec api python scripts/collect_once.py futzip-sbc
docker compose exec api python scripts/realdata_status.py
powershell -ExecutionPolicy Bypass -File .\scripts\phase2_runtime_check.ps1
```

## Current Phase-2 build validation

- 86/86 Python tests pass in the packaging environment.
- 77 SQLAlchemy tables.
- Alembic head `0008_fc26_multisource_multimarket`.
- TypeScript/TSX syntax transpilation: 22 files, 0 syntax errors.
- Docker/PostgreSQL/Next production runtime must be validated on the vacation PC because Docker and outbound package networking are unavailable in the packaging sandbox.
- See `docs/BUILD_VALIDATION_2026-09-04.md`, `docs/FC26_REAL_MARKET_PHASE2_2026-09-04.md`, and `docs/FC26_PROVIDER_AUDIT_2026-09-04.md`.
