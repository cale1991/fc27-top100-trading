# Phase 2 Runtime Validation — 2026-09-04

## Packaging environment

Available and run:
- Python test suite.
- Python compilation.
- Alembic revision-chain/head inspection.
- SQLAlchemy metadata/schema generation.
- YAML/Compose parsing.
- TypeScript/TSX syntax transpilation with TypeScript 5.8.3.
- release ZIP secret/install-regression validation.

Unavailable in this environment:
- Docker / Podman.
- local PostgreSQL client/server.
- outbound runtime DNS for collector code.
- npm dependency download required for a true Next.js production build.

A direct `FutzipCollector` attempt for `movers`, `new`, and `sbc` was executed in this environment. All three failed before receiving HTTP because DNS resolution was unavailable (`ConnectError: Temporary failure in name resolution`). No live FUTZIP rows are claimed from this environment.

Therefore this environment does **not** claim a successful live FUTZIP or Parse response and does not claim a Docker/PostgreSQL runtime gate that it cannot execute.

## Required vacation-PC runtime command

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\phase2_runtime_check.ps1
```

Expected high-level result:
- `migrate` exits successfully after Alembic head `0008_fc26_multisource_multimarket` and seed scripts.
- PostgreSQL, Redis, API, worker, Beat and web report running/healthy.
- existing `smoke_app.ps1` reports all application endpoints/front-end healthy.
- FUTZIP one-shot collectors either report actual item counts or a source-specific error while all other services remain running.
- `realdata_status.py` reports REAL and DEMO data separately by market segment/provider.

Use `docker compose logs migrate api worker beat web --tail 200` if a runtime check fails.

## r1 vacation-PC blocker patch

The r1 release fixes the runtime issues found during the first real Phase 2 rehearsal:

- JSON/JSONB metadata is recursively normalized at persistence boundaries (`datetime`/`date` to ISO-8601, `Decimal` to exact strings, `Enum` to value, nested containers recursively normalized) without altering native timestamp columns.
- FUTZIP collector-run metadata is JSON-safe before flush/commit.
- `phase2_runtime_check.ps1` now waits for API/web readiness, treats smoke and all three FUTZIP one-shot collections as mandatory gates, exits non-zero on any mandatory failure, and prints `PASSED` only when all gates pass.
- Clean-install and Upgrade `.env` behavior is explicit. Upgrade secrets are never searched/copied automatically; users intentionally preserve the previous `.env` if desired.

Docker/PostgreSQL runtime validation must still be run on the vacation PC because Docker is unavailable in the build sandbox.
