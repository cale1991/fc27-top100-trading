# Build Validation — FC26 Real Market Phase 2

Packaging-environment validation:

- Python tests: **86 passed, 0 failed**.
- Alembic head: `0008_fc26_multisource_multimarket`.
- SQLAlchemy table count: **77**.
- migration-structure regression: fresh/current schema and Phase-1 `0007` → Phase-2 `0008` simulation PASS.
- permanent Alembic `version_num VARCHAR(255)` regression PASS.
- packaged `seed_strategy_library` regression PASS.
- FUTZIP parser/conditional request/unknown-market/provenance tests PASS.
- Parse/FUTBIN optionality, secret redaction, PC/PlayStation separation and rate-limit tests PASS.
- market-segment, consensus/disagreement, point-in-time, cross-market isolation tests PASS.
- Portfolio execution/reference separation and buy/sell/partial-sale accounting tests PASS.
- Python compilation PASS.
- YAML + Docker Compose syntax parse PASS.
- TypeScript/TSX syntax transpilation: **22 files / 0 syntax errors**.

Environment limitations:

- Docker/Podman unavailable: Docker build/start, real PostgreSQL migration, worker/Beat/web runtime and application smoke cannot be executed here.
- npm external package download unavailable: true `next build` cannot be executed here.
- runtime DNS blocked: no live provider ingestion claimed.

The release contains `scripts/phase2_runtime_check.ps1` to run the unavailable Docker/runtime gates immediately on the vacation PC before treating that machine's deployment as validated.
