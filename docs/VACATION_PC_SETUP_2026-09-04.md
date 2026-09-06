# Vacation PC setup — 2026-09-04

This is the fastest path to run the complete first application locally on the Windows 11 vacation PC.

## What to install

1. **Docker Desktop for Windows** with WSL2 backend enabled.
2. Extract the project zip to a normal folder, for example `C:\fc27-trader`.

You do not need Python, PostgreSQL, Redis or Node installed separately for the normal Docker path.

## First boot

Open **PowerShell** in the extracted repository folder:

```powershell
Copy-Item .env.example .env

docker compose up -d --build
```

First boot builds the Python and Next.js containers, starts PostgreSQL and Redis, runs Alembic migrations, seeds known data sources and creates the default trading account.

Check status:

```powershell
docker compose ps
```

The `postgres`, `redis`, `worker`, `beat`, `api` and `web` services should be running. `migrate` should show a successful completed/exited state.

Run the bundled smoke test:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_app.ps1
```

Open the app:

```text
http://localhost:3000
```

FastAPI remains visible for development at:

```text
http://localhost:8080/docs
```

## Open it from the iPhone / another PC on the same network

On the vacation PC:

```powershell
ipconfig
```

Find the vacation PC's active adapter **IPv4 Address**, for example `192.168.1.42`.

On the other device open:

```text
http://192.168.1.42:3000
```

If Windows asks whether Docker/Node networking may communicate on the private network, allow **Private networks**. If the page is unreachable, verify Windows Firewall permits inbound TCP 3000 and 8080 on the private network.

The browser application works over local HTTP. Full installable-PWA/service-worker behavior on iPhone should be considered a **cloud/HTTPS deployment step**; do not expose the vacation PC directly to the public internet just to get HTTPS.

## First real use

1. Open **Portfolio**.
2. Set the actual current Ultimate Team coin balance.
3. Leave the collectors running.
4. **Now** shows immediate actions; **Opportunities** shows current ranked candidates.
5. A candidate lacking fresh execution data appears in **Verify**.
6. Paste/enter the lowest 5–10 exact PC BINs and optionally attach a screenshot.
7. The app records confidence and immediately returns `BUY`, `PASS`, `WATCH` or continued `VERIFY` state.
8. After manually buying in EA, use **Portfolio -> MARK BOUGHT / ADD PURCHASE**.
9. On a sale, click **Record sale** and enter quantity/price. The ledger applies the EA 5% tax and updates realized Transfer Profit.

## Optional local UI demo

Only if you want to exercise the complete flow before real provider data is available:

```powershell
docker compose exec api python scripts/seed_demo_app.py
```

This creates an unmistakable `DEMO Market Candidate`, a verification request and 500k demo coins. It refuses to run when `APP_ENV=production`.

Do not run the demo seed against the eventual production database.

## Stop / restart

Stop services without deleting data:

```powershell
docker compose stop
```

Start again:

```powershell
docker compose start
```

Update after code changes:

```powershell
docker compose up -d --build
```

Do **not** run `docker compose down -v` unless you intentionally want to delete the local PostgreSQL volume.

## Things that can run today on the vacation PC

- PostgreSQL / Redis.
- EA content collectors.
- authorized/reference provider collectors once keys are added to `.env`.
- dynamic discovery/attention scheduler.
- FastAPI backend.
- Next.js application.
- portfolio/verification/activity/community/system UI.
- lightweight model inference/baselines.
- shadow trading.

## WAIT FOR RTX 5080 MAIN PC — September 5

Do not spend time configuring these on the vacation PC tonight:

- PyTorch/CUDA global temporal neural model training.
- large XGBoost GPU training/sweeps.
- heavy LightGBM/XGBoost hyperparameter search.
- large historical feature materialization intended for GPU experiments.
- multi-model walk-forward sweeps.
- dedicated GPU worker heartbeat/model-artifact uploader.

The 5080 worker will connect to the same central data/model-artifact architecture. Turning that machine off must never stop collection, portfolio state or the web app.

## FC26 Real Market Phase 2 runtime validation

After updating to the Phase-2 ZIP, the fastest full runtime gate is:

```powershell
Copy-Item .env.example .env -ErrorAction SilentlyContinue
powershell -ExecutionPolicy Bypass -File .\scripts\phase2_runtime_check.ps1
```

This builds Docker images, applies Alembic through `0008_fc26_multisource_multimarket`, starts API/worker/Beat/web, runs the existing application smoke checks, prints provider/data status, and performs small one-shot FUTZIP RSS collection attempts.

### FUTZIP collection

No credential is required:

```powershell
docker compose exec api python scripts/collect_once.py futzip-movers
docker compose exec api python scripts/collect_once.py futzip-new
docker compose exec api python scripts/collect_once.py futzip-sbc
# or
docker compose exec api python scripts/collect_once.py futzip-all

docker compose exec api python scripts/realdata_status.py
```

FUTZIP mover RSS is intentionally stored as `UNKNOWN / MARKET_CONTEXT` unless the feed itself proves a market segment. It must not create a PC executable mark or PC reference consensus value.

### Optional Parse.bot/FUTBIN structured references

Leave disabled unless you want to use Parse credits:

```text
PARSE_API_KEY=
PARSE_FUTBIN_ENABLED=false
```

For a one-page connectivity/shape test, edit `.env` to add your key and set the flag to true, then recreate API/worker/Beat so the environment is reloaded:

```powershell
docker compose up -d --force-recreate api worker beat

docker compose exec api python scripts/collect_once.py parse-futbin-catalogue --max-pages 1
docker compose exec api python scripts/realdata_status.py
```

Selective hot-set refresh:

```powershell
docker compose exec api python scripts/collect_once.py parse-futbin-hot
```

Parse prices remain third-party `REFERENCE_PRICE` observations. `price_pc` is kept under PC; `price_ps` is kept under the provider-labelled PlayStation segment. Neither may overwrite manual PC execution evidence.

### FUT-DB quota-zero state

A FUT-DB account returning HTTP 429 with `x-ratelimit-limit=0` / `x-ratelimit-remaining=0` is recorded as `NO_QUOTA` and backed off. The rest of the app continues normally. If a trial/Premium quota is later enabled, no architecture change is needed.

### Preserve an existing Phase-1 database

Do **not** remove the PostgreSQL volume. Extract/update the application files and run:

```powershell
docker compose up -d --build
```

The migration service upgrades `0007_fc26_real_market_phase1` to `0008_fc26_multisource_multimarket`. Do not use `docker compose down -v` when testing an upgrade because `-v` deletes the database volume.

## Phase 2 r1 runtime validation: clean install vs upgrade

### CLEAN INSTALL
If this is a clean install and `.env` does not exist, the runtime check deliberately creates a blank `.env` from `.env.example`. Credential-free providers such as FUTZIP do not require secrets.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\phase2_runtime_check.ps1 -Mode CleanInstall
```

### UPGRADE
Before validating an upgrade, intentionally copy/preserve the **previous release's `.env`** into the newly extracted repository directory if you want to retain configured provider credentials. The script will never search for, copy, or print secrets automatically.

Example (adjust the old directory path yourself):

```powershell
Copy-Item "C:\path\to\previous-phase2\.env" ".\.env"
powershell -ExecutionPolicy Bypass -File .\scripts\phase2_runtime_check.ps1 -Mode Upgrade
```

If `.env` is still missing in Upgrade mode, the script prints an explicit warning and creates a blank `.env` so credential-free runtime checks can continue. This does not make FUTZIP fail because FUTZIP requires no API key.
