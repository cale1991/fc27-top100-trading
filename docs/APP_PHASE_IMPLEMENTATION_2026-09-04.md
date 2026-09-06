# FC27 Trading Terminal — Application Phase Implementation (2026-09-04)

## Reused rather than replaced

The application phase keeps the existing working foundation:

- FastAPI/Python backend and PostgreSQL/SQLAlchemy models.
- immutable raw-ingest/provenance layer.
- FC26/FC27 EA official-news collector.
- FUT-DB / The Coin Printer adapters and provider-role validation.
- fixed 50-card provider-validation basket (qualification/testing only).
- `ReferencePriceObservation`, `ExecutionObservation`, dynamic `OpportunityCandidate`, `AttentionAllocation` and empirical acquisition observations.
- manual verification request tables and shadow-execution realism.
- Celery/Redis collection scheduler.
- existing feature/model/evaluation package layout.

## Existing files materially corrected

- `docker-compose.yml`: Docker services now use service DNS (`postgres`, `redis`) rather than invalid container-local `localhost`; migration bootstrap and web service added.
- `src/fc27trader/api/app.py`: replaced the single-purpose verification API with routed application API + live WebSocket refresh channel.
- `src/fc27trader/api/routers/verification.py`: manual evidence confidence is no longer hard-coded to 1.0; screenshot/value quality and age are modeled.
- `src/fc27trader/services/discovery.py`: candidate rows now persist action/buy threshold/sell range/quantity/confidence/explanation fields and create verification requests only when information value is positive.
- `src/fc27trader/scheduler/schedules.py`: `opportunity_discovery` and `attention_reallocation` were previously configured but unmapped and therefore never executed; both now run, plus trader-reputation recalculation.
- `migrations/versions/0004_application_layer.py`: migration is safe both for an older DB and the project's `0001 create_all` fresh-DB behavior.
- `README.md`: updated from backend-only bootstrap to actual application instructions.

## New backend services

- user portfolio ledger and exact EA-tax accounting.
- dashboard/application query layer.
- activity feed and notification persistence.
- quality-aware manual verification confidence.
- broad observable-market input builder.
- scheduled dynamic opportunity discovery and attention reallocation.
- normalized Community Intelligence ingestion into the same event architecture.
- trader reputation scoring and crowding detection.
- public prediction ledger, official-X posting adapter, persona preflight, public-account continuity state and social-market-impact events.
- usable quantitative baselines for liquidity/time-to-sale, regime, anomaly, EA intervention, historical analogues, event response, turnover-aware portfolio allocation and ensemble agreement.

## New application tables

The schema now has 54 tables. Application-phase additions include:

- `trading_accounts`
- `portfolio_positions`
- `portfolio_transactions`
- `activity_feed_items`
- `notifications`
- `service_heartbeats`
- `community_traders`
- `community_content`
- `community_signals`
- `community_signal_outcomes`
- `trader_reputation_snapshots`
- `public_predictions`
- `public_posts`
- `social_market_impacts`
- `persona_state`

`opportunity_candidates` also gained explicit action/execution fields used by the terminal, and `manual_verification_responses` gained quality/confidence fields.

## First application milestone

The Next.js PWA in `web/` implements:

- **Now** dashboard — direct answer to "what should I do right now?"
- **Opportunities** — dynamic ranked candidates, not a permanent watchlist.
- **Opportunity detail** — reference history, execution evidence, forecasts, acquisition evidence, community calls, catalyst/invalidation/exit context.
- **Verify** — current listing input, paste, screenshot upload, confidence calculation and immediate action threshold re-evaluation.
- **Portfolio** — set coin balance, record purchases/additions, partial/full sales, 5% EA tax and realized Transfer Profit.
- **Market** — search any known card/version and inspect reference/execution/history/related-card state.
- **Activity** — human-readable event timeline.
- **Community** — trader reputation and tracked calls.
- **System** — collectors, providers, model runs, workers and data-quality incidents.

Desktop uses a persistent left navigation. Mobile uses a reduced bottom navigation focused on immediate trading actions.

## Live path

`broad observed references -> broad input builder -> dynamic discovery -> opportunity rows -> attention allocation -> optional manual execution verification -> trade decision -> manual EA execution -> portfolio ledger`

The fixed 50-card validation basket never enters that production path.

## External dependencies still requiring user credentials/access

The repository can run without these, but the corresponding source/integration remains inactive until credentials or authorized access are supplied:

- The Coin Printer API key.
- FUT-DB API key.
- any selected Community Intelligence source whose permitted API requires authentication.
- X user-authorized access token for actual posting.

No unofficial EA Transfer Market automation was added.
