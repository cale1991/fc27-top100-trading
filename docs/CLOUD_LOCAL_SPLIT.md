# Cloud vs Local Responsibilities

## Must run 24/7 independently of the main PC

- PostgreSQL/Timescale central database.
- Redis job broker.
- Celery Beat scheduler.
- Collector workers: EA content + all licensed market/reference APIs.
- Raw object storage (S3-compatible/R2/B2/S3).
- Event normalization and event-triggered reevaluation queue.
- Shadow portfolio state/fills.
- FastAPI read API/health endpoints.
- Logging, source freshness and collector health alerts.
- Lightweight feature materialization and CPU inference needed for live signals.

These components must survive the RTX 5080 PC being powered off.

## RTX 5080 main PC

- Global neural time-series model training.
- Large historical feature builds/backfills.
- GPU XGBoost when useful.
- Hyperparameter sweeps that are too expensive for the cloud collector host.
- Batch embedding/graph/neural experiments.
- Model evaluation on large historical windows.
- Export validated model artifacts to central object storage/model registry.

The local PC never owns canonical market data. It downloads training windows from the central DB/object store and uploads artifacts/metrics.

## Deployment shape

Production target:
1. Managed PostgreSQL/Timescale (preferred) or dedicated persistent DB VM.
2. Small always-on Linux container host for Redis + scheduler + collector/API workers.
3. S3-compatible object storage for raw payloads and model artifacts.
4. GitHub/GitLab private repository for code/CI.

The Docker Compose file is the local/dev topology; production services can be split without code changes through environment variables.
