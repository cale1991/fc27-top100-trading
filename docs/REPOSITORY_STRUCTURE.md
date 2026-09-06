# Repository Structure

```text
fc27-top100-trading/
├── config/
│   ├── opportunity.yaml
│   ├── polling.yaml
│   ├── provider_catalog_fc26.yaml
│   ├── provider_validation.yaml
│   ├── shadow_rules.yaml
│   ├── sources.yaml
│   └── validation_basket_fc26.yaml
├── data/
│   ├── imports/
│   ├── raw/
│   └── validation/
├── docs/
│   ├── DESIGN_LOCK_UPDATE_2026-09-04.md
│   ├── PROVIDER_VALIDATION_2026-09-04.md
│   ├── DATABASE.md
│   ├── DATA_LAYERS.md
│   ├── FEATURE_PIPELINE.md
│   ├── COLLECTOR_ARCHITECTURE.md
│   ├── SHADOW_TRADING.md
│   └── schema_postgres.sql
├── migrations/versions/
│   ├── 0001_initial.py
│   ├── 0002_provider_validation.py
│   └── 0003_dynamic_market_universe.py
├── scripts/
│   ├── validate_provider.py
│   ├── select_hot_sources.py
│   ├── prequalification_report.py
│   └── record_manual_execution.py
├── src/fc27trader/
│   ├── api/
│   ├── collectors/
│   ├── db/
│   ├── domain/
│   │   └── observations.py
│   ├── features/
│   │   └── reference_features.py
│   ├── ingestion/
│   ├── models/
│   ├── opportunity/
│   │   ├── acquisition.py
│   │   ├── models.py
│   │   └── scoring.py
│   ├── scheduler/
│   │   └── attention_targets.py
│   ├── services/
│   │   ├── attention.py
│   │   ├── discovery.py
│   │   ├── manual_verification.py
│   │   └── verification_repository.py
│   ├── shadow/
│   └── validation/
└── tests/
    ├── test_provider_validation.py
    ├── test_shadow_execution.py
    ├── test_opportunity_discovery.py
    ├── test_reference_features.py
    └── test_manual_verification.py
```

The fixed 50-card basket lives under `config/` because it is a controlled validation fixture, not a production universe.
