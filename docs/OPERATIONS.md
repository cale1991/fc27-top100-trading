# Operations

## Required secrets

- `DATABASE_URL`
- `REDIS_URL`
- object-store credentials when `RAW_STORE_MODE=s3`
- `FUTDB_API_KEY` when enabled
- `THECOINPRINTER_API_KEY` when enabled

Never commit `.env`.

## Minimum monitoring

Alert when:
- EA content collector has no successful run for >5 minutes;
- hot market feed has no successful run for >5 minutes once enabled;
- provider `source_timestamp` age exceeds the tier SLA;
- PC coverage drops sharply;
- duplicate/stuck prices exceed expected thresholds;
- a parser starts writing zero records after previously writing records;
- source disagreement exceeds configured thresholds;
- DB/object storage/Redis/queue backlog approaches limits.

Structured JSON logs use `structlog`. Every collector execution writes a `collector_runs` row. Prometheus counters/gauges cover run count, duration and source data age. `data_quality_incidents` persists operational data failures so training can exclude suspect windows.

## First source qualification

After setting `THECOINPRINTER_API_KEY`:

```bash
python scripts/qualify_thecoinprinter.py --pages 10 --take 50
```

The report measures unique PC-price coverage and provider `updated_at` lag, including the ratio within 120 s and 300 s. Do not enable `thecoinprinter_recent` or promote it to primary market data solely because the API responds quickly.

## Environment setup

Core cloud/dev:
- Python 3.12
- PostgreSQL 16 + TimescaleDB
- Redis 7
- Docker / Docker Compose

Collector hosts install core dependencies only. Add `[features,ml,dev]` where feature/model work is performed.

RTX 5080:
- run `scripts/setup_rtx5080.ps1`;
- script installs feature/ML packages and a CUDA PyTorch wheel;
- verify `torch.cuda.is_available()` and GPU name before training.
