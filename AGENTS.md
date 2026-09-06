# Repository instructions for Codex

## Purpose

Work quickly, but keep the user able to understand and supervise consequential decisions. The user is strong at defining goals, spotting suspicious behavior, refining requirements, and judging practical results; do not require them to write code for educational purposes. Explain the system concepts that matter to the task without turning routine work into a programming lesson.

These are repository-wide instructions. Put substantial task-specific requirements and decisions in `docs/tasks/<task-name>.md`, using `docs/tasks/TASK_TEMPLATE.md`.

## Architecture snapshot

Preserve this existing shape unless a task explicitly authorizes redesign:

- Python 3.12 backend under `src/fc27trader/`: FastAPI routers call service/query code, SQLAlchemy models persist to PostgreSQL/TimescaleDB, and Celery workers/Beat use Redis for scheduled collection and processing.
- Provider flow: role-aware collector -> immutable raw payload in filesystem or S3-compatible storage -> `raw_ingests` provenance -> normalization/identity mapping -> market-segment-specific observations/events -> point-in-time features -> discovery/model/shadow/application views.
- `web/` is a separate Next.js 15/React PWA. It calls FastAPI through the `/backend/*` rewrite and refreshes through `/ws/live` with polling fallback. Do not move domain, accounting, provider, or persistence logic into the frontend.
- Alembic migrations in `migrations/versions/` evolve the database. Docker Compose is the local/dev topology for TimescaleDB/PostgreSQL, Redis, migration/seeding, Celery worker, Celery Beat, FastAPI, and the PWA.
- Always-on collection, storage, lightweight features, and live inference must not depend on the RTX 5080 PC. That machine is for heavy training/backfills and exports validated artifacts; it does not own canonical data.

Start with `README.md`, then use the focused documents in `docs/` and the actual code. Some dated documents describe a phase or incident rather than the current whole system; verify current behavior in code, migrations, and tests.

## Locked project invariants

Treat these as architectural constraints, not convenient defaults:

- FC26 is the live rehearsal/data-building cycle. FC27 is the target cycle and should be activated through explicit `game_year`/segment configuration without discarding FC26 data or redesigning the schema. Preserve FC26 history as transition evidence; allow FC27 outcomes to supersede older priors only as measured data accumulates.
- The user's current executable market is FC26 PC. PC, provider-labelled PlayStation, provider-defined console, shared console, Switch, and unknown observations remain separate. `UNKNOWN` or non-PC evidence may provide research context or trigger PC verification, but must never become PC price truth or an executable mark.
- A provider has one or more roles, not a global trusted/untrusted status: `HOT_REFERENCE`, `REFERENCE`, `HISTORICAL`, `METADATA`, `CONTENT`, or `MANUAL_BENCHMARK`. Request cadence/latency is not provider-side freshness.
- Respect provider rights and access boundaries in `config/sources.yaml`, `config/provider_catalog_fc26.yaml`, and `docs/DATA_SOURCES.md`. Do not scrape prohibited surfaces, reverse-engineer private EA Transfer Market endpoints, or assume storage/training/commercial rights. Optional or credential-gated providers must remain optional and must not block startup.
- Reference prices are valuation/search anchors, never executable listings or guaranteed acquisition prices. Immediate portfolio/trade decisions require fresh execution evidence or the separate learned acquisition path. Keep reference confidence, execution-observation confidence, and trade/model confidence distinct.
- Preserve immutable provenance. Successful external responses are stored before parsing; raw payloads and their timestamps/checksums/lineage must remain available. Normalize untrusted provider input conservatively, quarantine or isolate malformed items, and never silently merge uncertain card identities or market segments.
- Use knowledge time for point-in-time features and backtests. Later imports must not appear knowable at an earlier prediction timestamp. No lookahead, random train/test splits, fabricated samples, or source anecdotes presented as measured profitability.
- Production discovery uses the broadest practical observable PC market. The fixed 50-card FC26 basket is only for provider qualification/testing. `opportunity_candidates`, `attention_allocations`, and `collection_targets` are current/expiring state, not a permanent watchlist.
- Historical strategies are evidence/features over the production universe, not a mandatory playbook. Qualitative evidence does not become `PROVEN / REPEATED`, measured performance, or model confidence without timestamped FC26 PC outcomes. Preserve contradictory/failure evidence and structural-decay signals.
- All EA Transfer Market purchases, sales, bids, and listings are manually executed by the user. Do not add autobuyers, autobidders, auto-listing, session scraping, CAPTCHA bypass, evasion, or unofficial market-action automation. The app may recommend, request verification, record manual actions, and run shadow execution.
- PostgreSQL is the source of truth and timestamps are timezone-aware UTC. The local GPU machine, raw files, frontend state, provider responses, and derived artifacts are not alternative canonical stores.
- Portfolio accounting uses the exact 5% EA tax and preserves transaction history, partial-sale cost basis, consumed listing evidence, and the separation between desired listing price, reference value, and current executable liquidation mark.

## Scope and architecture discipline

- Preserve the existing architecture unless the task explicitly authorizes redesign.
- Solve the requested problem end-to-end, but do not expand scope unnecessarily.
- Do not add demo features, placeholder systems, speculative frameworks, new dependencies, or unrelated cleanup.
- Prefer existing domain contracts, services, repositories, configuration, routers, components, and test patterns over parallel abstractions.
- Major architectural or data-semantic decisions must not be made silently. Explain them before or while implementing.
- If a request conflicts with an invariant or existing boundary, explain the conflict and propose the smallest safe solution. Do not quietly weaken the invariant to satisfy the surface request.
- Distinguish a reported symptom from its root cause. Fix the responsible layer, not merely the visible screen or failing assertion.

## Repo-aware planning

For non-trivial work:

1. Inspect the relevant code, current configuration, migrations, tests, and focused docs before proposing a plan.
2. Trace the affected data/control flow across collector, raw storage, normalization, identity, market segment, persistence, feature/model, service/API, and PWA layers as relevant.
3. State the observed symptom, likely/root cause, affected components, and important assumptions.
4. State what will change and what must remain unchanged, especially the locked invariants above.
5. Identify database migration, API contract, backend, frontend, provider/access, persistence/provenance, scheduler/runtime, and test implications where relevant. Say explicitly when a category is not affected.
6. For substantial work, create or update `docs/tasks/<task-name>.md` before implementation. Record requirements, invariants, plan, acceptance criteria, discoveries, review findings, verification, and final outcome there. Keep task-only detail out of this file.

Plans are working records, not ceremony. Small, local, low-risk changes can use a short in-chat plan and skip a task file.

## Learning and explanations

For a non-trivial task, explain in beginner-friendly language:

1. what problem is being solved;
2. why it exists;
3. which part of the system is responsible;
4. the intended approach;
5. why that approach is preferable to reasonable alternatives.

Use technical terms when they improve precision, and explain unfamiliar ones when they become relevant. Do not over-explain obvious syntax or turn every task into a generic tutorial.

Call out important discoveries as they happen, including when:

- the symptom is not the root cause;
- an assumption or existing document is stale or wrong;
- a migration or compatibility path is required;
- an existing abstraction should be reused;
- one subsystem changes another subsystem's behavior;
- provider input, data quality, accounting, or runtime state creates meaningful risk or technical debt.

After non-trivial implementation, include a concise explanation of the root cause, what changed, why it works, the new data/control flow, tests actually run, likely failure modes if the implementation were wrong, and 2–5 useful files to read with what to notice in each. When multiple reasonable approaches exist, name the main alternatives briefly and explain the choice.

## Agent and model routing

The lead agent owns decomposition, integration, consistency, and final verification. The user should not normally need to choose a model or subagent.

Use the least expensive capable option based on ambiguity, risk, context size, and task complexity:

- Lightweight/cheap agents: repository exploration, search, file discovery, documentation lookup, mechanical checks, and repetitive verification.
- Luna: bounded implementation, straightforward bug fixes, tests, migrations, repetitive refactors, cleanup, and fixes from approved review findings.
- Sol: architecture, ambiguous root-cause analysis, repo-grounded planning, cross-system reasoning, integration choices, and important review.
- Astra: exceptional escalation for genuinely frontier-level end-to-end reasoning or after strong prior approaches have failed.

Do not delegate merely to delegate, and do not spawn multiple expensive agents when a cheaper agent can reliably do the work. Parallelize only independent work with clear boundaries. Implementation agents may not redesign architecture silently. If the available Codex environment cannot select the preferred model, follow the intent with the available tools and mention only escalation choices that are useful to the user.

## Database, ingestion, and transaction discipline

- Change SQLAlchemy models and add an Alembic migration together when persisted schema changes. Never edit or delete an applied migration to represent a new change.
- Preserve existing rows and upgrade paths unless destructive migration is explicitly authorized. Test both a fresh database and realistic upgrades from relevant prior heads.
- This repository's `0001` migration calls current `Base.metadata.create_all()`. Later migrations therefore use `checkfirst`/inspection so they work both after a current fresh bootstrap and against older databases. Preserve that compatibility until a task explicitly redesigns the bootstrap strategy.
- Keep descriptive Alembic revision IDs compatible with the widened `alembic_version VARCHAR(255)` setup in `migrations/env.py`, `fc27trader.db.alembic_bootstrap`, and `infra/sql/bootstrap.sql`.
- Avoid destructive downgrade behavior for retained market/history data. Do not reset volumes or recreate a database as an upgrade shortcut.
- Service/repository helpers generally `flush`; API, task, or script boundaries own `commit`. After a database failure, explicitly `rollback` before reusing the session. Use `begin_nested()`/savepoints when one malformed provider item should not poison a larger ingestion batch, and verify that later valid items still commit.
- Make values JSON/JSONB-safe at persistence boundaries, including nested datetimes/dates, decimals, enums, and containers. Redact keys/tokens from errors, logs, metadata, fixtures, and release packages.
- Preserve the repository's idempotence semantics: exact reprocessing can deduplicate, while a later poll of an unchanged provider value can still be a new time-series observation. Do not convert event identity into permanent price overwriting.

## Implementation and verification

- Complete bounded tasks end-to-end. Run relevant checks after changes and fix failures caused by the work.
- Report only checks actually run and their results. State environment limitations plainly; do not turn static inspection into a runtime-success claim.
- Prefer a regression test for a bug that has occurred. Keep existing install/runtime regressions intact, especially migration-chain/fresh-upgrade compatibility, scheduler job mapping, JSON-safe metadata, per-item ingestion isolation, reference-vs-execution separation, market-segment isolation, point-in-time correctness, exact tax/accounting, and release secret scanning.
- Validate external/provider input at the collector/normalization/persistence boundary. A malformed item should be observable and isolated where safe; it must not silently corrupt identities, prices, or the surrounding transaction.
- Backend baseline: `python -m ruff check src tests scripts` and `python -m pytest -q` after relevant Python changes.
- Frontend baseline: from `web/`, run `npm run build` after relevant TypeScript/React/Next.js changes. Also exercise the affected API-to-screen flow when runtime is available.
- Database/runtime changes require proportionate verification: inspect the Alembic chain, run `alembic upgrade head` against the appropriate database path, and use Docker Compose/smoke scripts when available. The Phase 2 vacation-PC gate is `powershell -ExecutionPolicy Bypass -File .\scripts\phase2_runtime_check.ps1`.
- CI currently runs Python 3.12, Ruff, and pytest. Passing unit tests does not prove Docker/PostgreSQL/Redis/Celery/Next/provider runtime behavior.
- Never use live provider calls, paid credits, real social posting, destructive database actions, or Git push unless the task authorizes them and required credentials/approval exist.

## Final handoff

Lead with the outcome. For non-trivial changes, include:

- root cause and the implemented solution;
- important invariants preserved;
- files changed;
- checks run with pass/fail/not-run status and limitations;
- migration/deployment/manual follow-up, if any;
- 2–5 files worth reading and what the user should look for.

Do not claim success for an unrun check. Do not commit or push unless the user asks.
