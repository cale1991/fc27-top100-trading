from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter

import structlog
from sqlalchemy import select

from fc27trader.collectors.ea_official import EAOfficialNewsCollector
from fc27trader.collectors.futdb import FutDbCollector, FutDbNoQuotaError
from fc27trader.collectors.futzip import FUTZIP_FEEDS, FutzipCollector
from fc27trader.collectors.http import ConditionalState
from fc27trader.collectors.thecoinprinter import TheCoinPrinterCollector
from fc27trader.collectors.parse_futbin import ParseBotFutbinCollector, ParseBotFutbinRateLimit
from fc27trader.db.models import Card, CollectorRun, ProviderFeedState, RawIngest, Source
from fc27trader.db.json_safe import to_json_safe
from fc27trader.db.repositories import (
    insert_content_event,
    insert_market_snapshot,
    insert_reference_price_observation,
    record_raw_ingest,
    upsert_external_card,
)
from fc27trader.db.session import SessionLocal
from fc27trader.ingestion.raw_store import build_raw_store
from fc27trader.observability.metrics import collector_duration_seconds, collector_runs_total
from fc27trader.services.provider_health import record_provider_failure, record_provider_success, set_provider_state
from fc27trader.services.provider_budget import record_provider_request_usage
from fc27trader.services.futzip_ingestion import ingest_futzip_feed, mark_futzip_failure, mark_futzip_not_modified
from fc27trader.services.provider_ingestion import ingest_futdb_entity_page, ingest_futdb_player_page, ingest_futdb_price, ingest_thecoinprinter_page
from fc27trader.services.provider_targets import select_futdb_price_targets
from fc27trader.services.parse_futbin_ingestion import ingest_parse_futbin_catalogue_page, ingest_parse_futbin_player_details
from fc27trader.services.parse_futbin_targets import select_parse_futbin_hot_targets
from fc27trader.settings import get_settings

from .celery_app import app

log = structlog.get_logger()
settings = get_settings()
raw_store = build_raw_store(settings)


def _int_or_none(value):
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _futdb_quota_backoff_active(session, role: str) -> bool:
    from datetime import timedelta
    from fc27trader.db.models import ProviderHealth
    row = session.scalar(select(ProviderHealth).where(
        ProviderHealth.provider_key == "futdb",
        ProviderHealth.provider_role == role,
        ProviderHealth.platform == "pc",
    ))
    return bool(row and row.status == "NO_QUOTA" and row.updated_at and row.updated_at > datetime.now(UTC) - timedelta(hours=24))


def _mark_futdb_no_quota(role: str, exc: FutDbNoQuotaError) -> dict:
    with SessionLocal() as health_session:
        set_provider_state(
            health_session, provider_key="futdb", provider_role=role, platform="pc",
            status="NO_QUOTA", access_type="DOCUMENTED_API", enabled=True,
            supported_segments=["PC"], retry_after_seconds=exc.retry_after,
            metadata={"quota_zero": True, "trial_status": "TRIAL_PENDING"},
        )
        health_session.commit()
    return {"collector": f"futdb_{role}", "status": "no_quota", "written": 0, "retry_after": exc.retry_after}


def _collector_run_start(session, key: str) -> CollectorRun:
    run = CollectorRun(
        collector_key=key,
        started_at=datetime.now(UTC),
        status="running",
        records_seen=0,
        records_written=0,
        raw_ingest_count=0,
        metadata_json={},
    )
    session.add(run)
    session.flush()
    return run


def _collector_run_finish(session, run: CollectorRun, status: str, error: str | None = None) -> None:
    run.finished_at = datetime.now(UTC)
    run.status = status
    run.error = error


@app.task(name="fc27.collect_ea_news")
def collect_ea_news(game_year: int) -> dict:
    key = f"ea_news_fc{game_year}"
    started = perf_counter()
    url = settings.ea_news_fc26_url if game_year == 26 else settings.ea_news_fc27_url
    collector = EAOfficialNewsCollector(url, game_year=game_year)
    with SessionLocal() as session:
        run = _collector_run_start(session, key)
        try:
            index_obs = collector.collect()[0]
            stored = raw_store.put(index_obs)
            index_raw = record_raw_ingest(session, index_obs, stored)
            run.raw_ingest_count += 1
            article_urls = collector.discover_article_urls(index_obs.body)
            run.records_seen = len(article_urls)

            for article_url in article_urls:
                prior = session.scalar(
                    select(RawIngest).where(
                        RawIngest.request_url == article_url,
                        RawIngest.source_kind == f"ea_fc{game_year}_news_article",
                    )
                )
                if prior:
                    continue
                article_obs = collector.collect_article(article_url)
                article_stored = raw_store.put(article_obs)
                article_raw = record_raw_ingest(session, article_obs, article_stored)
                event = collector.parse_article_event(article_obs)
                insert_content_event(session, event, raw_ingest_id=article_raw.id)
                run.raw_ingest_count += 1
                run.records_written += 1

            _collector_run_finish(session, run, "success")
            session.commit()
            collector_runs_total.labels(collector=key, status="success").inc()
            log.info("collector_complete", collector=key, records_written=run.records_written)
            return {"collector": key, "articles_seen": len(article_urls), "written": run.records_written}
        except Exception as exc:
            session.rollback()
            collector_runs_total.labels(collector=key, status="error").inc()
            log.exception("collector_failed", collector=key, error=str(exc))
            raise
        finally:
            collector_duration_seconds.labels(collector=key).observe(perf_counter() - started)


@app.task(name="fc27.collect_futzip_feed")
def collect_futzip_feed(feed_key: str) -> dict:
    if feed_key not in FUTZIP_FEEDS:
        raise ValueError(f"unsupported FUTZIP feed: {feed_key}")
    key = f"futzip_{feed_key}"
    started = perf_counter()
    source_url = FUTZIP_FEEDS[feed_key]
    collector = FutzipCollector()
    with SessionLocal() as session:
        run = _collector_run_start(session, key)
        source = session.scalar(select(Source).where(Source.key == "futzip"))
        state = None
        if source is not None:
            state = session.scalar(select(ProviderFeedState).where(
                ProviderFeedState.source_id == source.id, ProviderFeedState.feed_key == feed_key
            ))
        conditional = ConditionalState(etag=state.etag if state else None, last_modified=state.last_modified if state else None)
        try:
            obs = collector.collect_feed(feed_key, conditional)[0]
            elapsed_ms = (perf_counter() - started) * 1000.0
            if obs.status_code == 304:
                mark_futzip_not_modified(
                    session, feed_key=feed_key, source_url=source_url, retrieved_at=obs.observed_at,
                    etag=obs.etag, last_modified=obs.last_modified,
                )
                record_provider_success(
                    session, provider_key="futzip", provider_role="content" if feed_key != "movers" else "context",
                    platform="unknown", status="HEALTHY", access_type="PUBLIC_FEED",
                    supported_segments=["UNKNOWN"], latency_ms=elapsed_ms, poll_duration_ms=elapsed_ms,
                    latest_observation_at=obs.observed_at, platform_certainty=0.0,
                    metadata={"feed_key": feed_key, "http_status": 304},
                )
                _collector_run_finish(session, run, "success")
                session.commit()
                return {"collector": key, "status": "not_modified", "http_status": 304, "items_seen": 0, "new_items": 0}

            stored = raw_store.put(obs)
            raw = record_raw_ingest(session, obs, stored)
            stats = ingest_futzip_feed(
                session, raw_ingest=raw, feed_key=feed_key, body=obs.body, retrieved_at=obs.observed_at,
                source_url=source_url, etag=obs.etag, last_modified=obs.last_modified, game_year=26,
            )
            run.raw_ingest_count = 1
            run.records_seen = stats["items_seen"]
            run.records_written = stats["items_ingested"]
            run.metadata_json = to_json_safe({**stats, "http_status": obs.status_code})
            record_provider_success(
                session, provider_key="futzip", provider_role="content" if feed_key != "movers" else "context",
                platform="unknown", status="HEALTHY" if stats["items_parsed"] > 0 else "DEGRADED",
                access_type="PUBLIC_FEED", supported_segments=["UNKNOWN"], latency_ms=elapsed_ms,
                cards_covered=stats["unique_provider_card_ids"], latest_observation_at=obs.observed_at,
                latest_provider_timestamp=stats["newest_provider_timestamp"], items_seen=stats["items_seen"],
                items_ingested=stats["items_ingested"], duplicates_skipped=stats["duplicates"],
                quarantined_observations=stats["quarantined"], parsing_failures=stats["parse_failures"],
                poll_duration_ms=elapsed_ms, gap_status=stats["gap_status"], platform_certainty=0.0,
                metadata={"feed_key": feed_key, "http_status": obs.status_code, "event_stream": True},
            )
            _collector_run_finish(session, run, "success")
            session.commit()
            return {"collector": key, "status": "success", "http_status": obs.status_code, **stats}
        except Exception as exc:
            elapsed_ms = (perf_counter() - started) * 1000.0
            session.rollback()
            with SessionLocal() as health_session:
                mark_futzip_failure(health_session, feed_key=feed_key, source_url=source_url, retrieved_at=datetime.now(UTC), error=str(exc))
                record_provider_failure(
                    health_session, provider_key="futzip", provider_role="content" if feed_key != "movers" else "context",
                    platform="unknown", error=str(exc), status="DEGRADED", poll_duration_ms=elapsed_ms,
                    metadata={"feed_key": feed_key},
                )
                health_session.commit()
            _collector_run_finish(session, run, "error", str(exc))
            raise


@app.task(name="fc27.collect_futzip_all")
def collect_futzip_all() -> dict:
    results = {}
    for feed_key in ("movers", "new", "sbc"):
        try:
            results[feed_key] = collect_futzip_feed.run(feed_key)
        except Exception as exc:
            results[feed_key] = {"status": "error", "error": str(exc)[:500]}
    return results


@app.task(name="fc27.collect_thecoinprinter_recent")
def collect_thecoinprinter_recent(page: int | None = None, take: int = 50) -> dict:
    if not settings.thecoinprinter_api_key:
        return {"collector": "thecoinprinter_recent", "status": "credential_missing", "written": 0}
    key = "thecoinprinter_recent"
    collector = TheCoinPrinterCollector(settings.thecoinprinter_api_key)
    pages = [page] if page is not None else list(range(1, max(1, settings.thecoinprinter_pages_per_cycle) + 1))
    with SessionLocal() as session:
        run = _collector_run_start(session, key)
        totals = {"seen": 0, "cards_written": 0, "prices_written": 0, "pages": 0}
        latest_provider_timestamp = None
        last_obs = None
        try:
            for page_no in pages:
                obs = collector.search_recent(page=page_no, take=take)[0]
                last_obs = obs
                stored = raw_store.put(obs)
                raw = record_raw_ingest(session, obs, stored)
                result = ingest_thecoinprinter_page(session, obs, raw_ingest_id=raw.id)
                totals["seen"] += result["seen"]
                totals["cards_written"] += result["cards_written"]
                totals["prices_written"] += result["prices_written"]
                totals["pages"] += 1
                run.raw_ingest_count += 1
                ts = result.get("latest_provider_timestamp")
                if ts and (latest_provider_timestamp is None or ts > latest_provider_timestamp):
                    latest_provider_timestamp = ts
                pagination = result.get("pagination") or {}
                total_available = _int_or_none(pagination.get("total"))
                if total_available is not None and page_no * take >= total_available:
                    break
            run.records_seen = totals["seen"]
            run.records_written = totals["cards_written"] + totals["prices_written"]
            run.metadata_json = {**totals, **((last_obs.metadata if last_obs else {}) or {})}
            md = (last_obs.metadata if last_obs else {}) or {}
            record_provider_success(
                session, provider_key="thecoinprinter", provider_role="reference", platform="pc+console",
                access_type="PAID_API", supported_segments=["PC", "CONSOLE_GENERIC"],
                latency_ms=md.get("latency_ms"), cards_covered=totals["seen"],
                latest_observation_at=last_obs.observed_at if last_obs else datetime.now(UTC),
                latest_provider_timestamp=latest_provider_timestamp,
                rate_limit_remaining=_int_or_none(md.get("rate_limit_remaining")),
                metadata={"price_rows": totals["prices_written"], "terms_mode": "approved_partner_api", "pages": totals["pages"]},
            )
            record_provider_success(
                session, provider_key="thecoinprinter", provider_role="metadata", platform="pc+console",
                access_type="PAID_API", supported_segments=["PC", "CONSOLE_GENERIC"],
                latency_ms=md.get("latency_ms"), cards_covered=totals["seen"],
                latest_observation_at=last_obs.observed_at if last_obs else datetime.now(UTC),
                rate_limit_remaining=_int_or_none(md.get("rate_limit_remaining")),
            )
            _collector_run_finish(session, run, "success")
            session.commit()
            return {"collector": key, "status": "success", **totals, "latest_provider_timestamp": latest_provider_timestamp}
        except Exception as exc:
            session.rollback()
            with SessionLocal() as health_session:
                record_provider_failure(health_session, provider_key="thecoinprinter", provider_role="reference", platform="pc+console", error=str(exc))
                health_session.commit()
            raise


@app.task(name="fc27.sync_futdb_universe")
def sync_futdb_universe(max_pages: int | None = None) -> dict:
    if not settings.futdb_api_key:
        return {"collector": "futdb_universe", "status": "credential_missing", "cards_written": 0}
    collector = FutDbCollector(settings.futdb_api_key)
    page_cap = max_pages or settings.futdb_universe_max_pages_per_run
    totals = {"cards_seen": 0, "cards_written": 0, "entity_rows": 0, "pages": 0}
    last_obs = None
    with SessionLocal() as session:
        if _futdb_quota_backoff_active(session, "metadata"):
            return {"collector": "futdb_universe", "status": "no_quota_backoff", "cards_written": 0}
        run = _collector_run_start(session, "futdb_universe")
        try:
            # Resolve names before player ingestion so league/club/nation/rarity are human-readable.
            for entity_type in ("nation", "league", "club", "rarity"):
                page = 1
                while page <= page_cap:
                    obs = collector.collect_entity_page(entity_type, page=page)[0]
                    last_obs = obs
                    stored = raw_store.put(obs); raw = record_raw_ingest(session, obs, stored)
                    result = ingest_futdb_entity_page(session, obs, entity_type=entity_type)
                    totals["entity_rows"] += result["seen"]; totals["pages"] += 1; run.raw_ingest_count += 1
                    page_total = int((result.get("pagination") or {}).get("pageTotal") or 1)
                    if page >= page_total: break
                    page += 1
            page = 1
            total_cards = 0
            while page <= page_cap:
                obs = collector.collect_players(page=page)[0]
                last_obs = obs
                stored = raw_store.put(obs); raw = record_raw_ingest(session, obs, stored)
                result = ingest_futdb_player_page(session, obs)
                totals["cards_seen"] += result["seen"]; totals["cards_written"] += result["written"]; totals["pages"] += 1; run.raw_ingest_count += 1
                pagination = result.get("pagination") or {}
                total_cards = int(pagination.get("countTotal") or total_cards or totals["cards_seen"])
                page_total = int(pagination.get("pageTotal") or 1)
                if page >= page_total: break
                page += 1
            run.records_seen = totals["cards_seen"]
            run.records_written = totals["cards_written"]
            run.metadata_json = {**totals, "provider_total_cards": total_cards}
            record_provider_success(session, provider_key="futdb", provider_role="metadata", latency_ms=((last_obs.metadata or {}).get("latency_ms") if last_obs else None), cards_covered=total_cards or totals["cards_seen"], latest_observation_at=(last_obs.observed_at if last_obs else datetime.now(UTC)), rate_limit_remaining=_int_or_none((last_obs.metadata or {}).get("rate_limit_remaining") if last_obs else None), metadata={"pages": totals["pages"]})
            _collector_run_finish(session, run, "success")
            session.commit()
            return {"collector": "futdb_universe", "status": "success", **totals, "provider_total_cards": total_cards}
        except FutDbNoQuotaError as exc:
            session.rollback()
            return _mark_futdb_no_quota("metadata", exc)
        except Exception as exc:
            session.rollback()
            with SessionLocal() as health_session:
                record_provider_failure(health_session, provider_key="futdb", provider_role="metadata", error=str(exc))
                health_session.commit()
            raise


@app.task(name="fc27.collect_futdb_reference_prices")
def collect_futdb_reference_prices(limit: int | None = None) -> dict:
    if not settings.futdb_api_key:
        return {"collector": "futdb_reference_prices", "status": "credential_missing", "written": 0}
    if not settings.futdb_premium_prices_enabled:
        return {"collector": "futdb_reference_prices", "status": "premium_disabled", "written": 0}
    collector = FutDbCollector(settings.futdb_api_key)
    with SessionLocal() as session:
        if _futdb_quota_backoff_active(session, "reference"):
            return {"collector": "futdb_reference_prices", "status": "no_quota_backoff", "written": 0}
        run = _collector_run_start(session, "futdb_reference_prices")
        written = 0; attempted = 0; latest_provider_ts = None; last_obs = None
        try:
            targets = select_futdb_price_targets(session, limit=limit or settings.futdb_price_requests_per_cycle)
            for external_id in targets:
                attempted += 1
                obs = collector.collect_player_price(external_id)[0]
                last_obs = obs
                stored = raw_store.put(obs); raw = record_raw_ingest(session, obs, stored)
                row = ingest_futdb_price(session, obs, player_id=external_id, raw_ingest_id=raw.id)
                run.raw_ingest_count += 1
                if row is not None:
                    written += 1
                    if row.provider_timestamp and (latest_provider_ts is None or row.provider_timestamp > latest_provider_ts): latest_provider_ts = row.provider_timestamp
            run.records_seen = attempted; run.records_written = written
            record_provider_success(session, provider_key="futdb", provider_role="reference", latency_ms=((last_obs.metadata or {}).get("latency_ms") if last_obs else None), cards_covered=written, latest_observation_at=(last_obs.observed_at if last_obs else datetime.now(UTC)), latest_provider_timestamp=latest_provider_ts, rate_limit_remaining=_int_or_none((last_obs.metadata or {}).get("rate_limit_remaining") if last_obs else None), metadata={"attempted": attempted})
            _collector_run_finish(session, run, "success")
            session.commit()
            return {"collector": "futdb_reference_prices", "status": "success", "attempted": attempted, "written": written}
        except FutDbNoQuotaError as exc:
            session.rollback()
            return _mark_futdb_no_quota("reference", exc)
        except Exception as exc:
            session.rollback()
            with SessionLocal() as health_session:
                record_provider_failure(health_session, provider_key="futdb", provider_role="reference", error=str(exc))
                health_session.commit()
            raise


@app.task(name="fc27.collect_parse_futbin_catalogue")
def collect_parse_futbin_catalogue(max_pages: int | None = None) -> dict:
    if not settings.parse_futbin_enabled:
        return {"collector": "parse_futbin_catalogue", "status": "disabled", "pages": 0, "cards": 0}
    if not settings.parse_api_key:
        with SessionLocal() as session:
            set_provider_state(session, provider_key="parse_futbin", provider_role="reference", platform="multi", status="NO_CREDENTIALS", access_type="OPTIONAL_STRUCTURED_PROVIDER", enabled=True, supported_segments=["PC", "PLAYSTATION"], metadata={"reference_only": True})
            session.commit()
        return {"collector": "parse_futbin_catalogue", "status": "credential_missing", "pages": 0, "cards": 0}
    collector = ParseBotFutbinCollector(settings.parse_api_key, base_url=settings.parse_futbin_base_url)
    page_cap = max(1, int(max_pages or settings.parse_futbin_catalogue_pages_per_cycle))
    totals = {"pages": 0, "cards": 0, "pc_references": 0, "ps_references": 0, "malformed": 0, "quarantined": 0}
    with SessionLocal() as session:
        run = _collector_run_start(session, "parse_futbin_catalogue")
        try:
            for page in range(1, page_cap + 1):
                obs = collector.collect_catalogue_page(page)[0]
                stored = raw_store.put(obs); raw = record_raw_ingest(session, obs, stored)
                result = ingest_parse_futbin_catalogue_page(session, obs, raw_ingest_id=raw.id)
                totals["pages"] += 1; totals["cards"] += result["cards_written"]
                totals["pc_references"] += result["pc_references"]; totals["ps_references"] += result["ps_references"]
                totals["malformed"] += result["malformed"]; totals["quarantined"] += result["quarantined_or_suspect"]
                run.raw_ingest_count += 1
                record_provider_request_usage(session, provider_key="parse_futbin", access_mode="CATALOGUE_BOOTSTRAP", credit_cost=settings.parse_futbin_credit_cost_per_call, requests_remaining=(obs.metadata or {}).get("rate_limit_remaining"), credits_remaining=(obs.metadata or {}).get("credits_remaining_header"), metadata={"last_endpoint": "get_players"})
                # A short page signals the end. Parse documents about 30/page, but does not expose a guaranteed page count.
                returned = result.get("page_count_returned")
                if isinstance(returned, int) and returned == 0:
                    break
            run.records_seen = totals["cards"]; run.records_written = totals["pc_references"] + totals["ps_references"]
            record_provider_success(session, provider_key="parse_futbin", provider_role="reference", platform="multi", status="HEALTHY" if totals["cards"] else "DEGRADED", access_type="OPTIONAL_STRUCTURED_PROVIDER", supported_segments=["PC", "PLAYSTATION"], latency_ms=None, cards_covered=totals["cards"], items_seen=totals["cards"], items_ingested=run.records_written, quarantined_observations=totals["quarantined"], normalization_failures=totals["malformed"], platform_certainty=1.0, metadata={"mode": "CATALOGUE_BOOTSTRAP", "reference_only": True})
            _collector_run_finish(session, run, "success"); session.commit()
            return {"collector": "parse_futbin_catalogue", "status": "success", **totals}
        except ParseBotFutbinRateLimit as exc:
            session.rollback()
            with SessionLocal() as health:
                record_provider_failure(health, provider_key="parse_futbin", provider_role="reference", platform="multi", error=str(exc), status="DEGRADED", retry_after_seconds=exc.retry_after)
                health.commit()
            return {"collector": "parse_futbin_catalogue", "status": "rate_limited", **totals, "retry_after": exc.retry_after}
        except Exception as exc:
            session.rollback()
            with SessionLocal() as health:
                record_provider_failure(health, provider_key="parse_futbin", provider_role="reference", platform="multi", error=str(exc), status="DEGRADED")
                health.commit()
            return {"collector": "parse_futbin_catalogue", "status": "error", **totals, "error": type(exc).__name__}


@app.task(name="fc27.collect_parse_futbin_hot")
def collect_parse_futbin_hot(limit: int | None = None) -> dict:
    if not settings.parse_futbin_enabled:
        return {"collector": "parse_futbin_hot", "status": "disabled", "attempted": 0, "written": 0}
    if not settings.parse_api_key:
        return {"collector": "parse_futbin_hot", "status": "credential_missing", "attempted": 0, "written": 0}
    collector = ParseBotFutbinCollector(settings.parse_api_key, base_url=settings.parse_futbin_base_url)
    with SessionLocal() as session:
        targets = select_parse_futbin_hot_targets(session, limit=int(limit or settings.parse_futbin_hot_requests_per_cycle))
        attempted = 0; written = 0; pc = 0; ps = 0; malformed = 0
        for external_id in targets:
            try:
                obs = collector.collect_player_details(external_id)[0]; attempted += 1
                stored = raw_store.put(obs); raw = record_raw_ingest(session, obs, stored)
                # Keep the immutable raw response even if normalization of one card
                # fails. The SAVEPOINT prevents a bad provider item from poisoning
                # the surrounding hot-set session.
                with session.begin_nested():
                    result = ingest_parse_futbin_player_details(session, obs, raw_ingest_id=raw.id, player_id=external_id)
                    session.flush()
                written += result["pc_references"] + result["ps_references"]; pc += result["pc_references"]; ps += result["ps_references"]; malformed += result["malformed"]
                record_provider_request_usage(session, provider_key="parse_futbin", access_mode="HOT_SET", credit_cost=settings.parse_futbin_credit_cost_per_call, requests_remaining=(obs.metadata or {}).get("rate_limit_remaining"), credits_remaining=(obs.metadata or {}).get("credits_remaining_header"), metadata={"last_endpoint": "get_player_details"})
            except ParseBotFutbinRateLimit as exc:
                record_provider_failure(session, provider_key="parse_futbin", provider_role="reference", platform="multi", error=str(exc), status="DEGRADED", retry_after_seconds=exc.retry_after)
                session.commit(); return {"collector": "parse_futbin_hot", "status": "rate_limited", "attempted": attempted, "written": written, "pc_references": pc, "ps_references": ps}
            except Exception as exc:
                record_provider_failure(session, provider_key="parse_futbin", provider_role="reference", platform="multi", error=str(exc), status="DEGRADED")
                continue
        record_provider_success(session, provider_key="parse_futbin", provider_role="reference", platform="multi", status="HEALTHY" if attempted else "STALE", access_type="OPTIONAL_STRUCTURED_PROVIDER", supported_segments=["PC", "PLAYSTATION"], latency_ms=None, cards_covered=attempted, items_seen=attempted, items_ingested=written, normalization_failures=malformed, platform_certainty=1.0, metadata={"mode": "HOT_SET", "reference_only": True})
        session.commit()
        return {"collector": "parse_futbin_hot", "status": "success", "attempted": attempted, "written": written, "pc_references": pc, "ps_references": ps}


@app.task(name="fc27.run_opportunity_discovery")
def run_opportunity_discovery() -> dict:
    from fc27trader.services.discovery import persist_discovery_cycle
    from fc27trader.services.market_universe import build_observable_market_inputs

    with SessionLocal() as session:
        market = build_observable_market_inputs(session)
        rows = persist_discovery_cycle(session, market)
        session.commit()
        return {"observable_cards": len(market), "ranked_candidates": len(rows)}


@app.task(name="fc27.reallocate_attention")
def reallocate_attention() -> dict:
    from fc27trader.db.models import OpportunityCandidate, PortfolioPosition
    from fc27trader.opportunity.models import OpportunityInputs, RankedOpportunity
    from fc27trader.scheduler.attention_targets import apply_attention_allocations
    from fc27trader.services.attention import allocate_attention

    now = datetime.now(UTC)
    with SessionLocal() as session:
        candidates = list(session.scalars(select(OpportunityCandidate).where(OpportunityCandidate.platform == "pc", OpportunityCandidate.status != "superseded")))
        active_position_ids = set(session.scalars(select(PortfolioPosition.card_id).where(PortfolioPosition.quantity > 0)))
        ranked = []
        inputs_by_card = {}
        for c in candidates:
            card_id = str(c.card_id)
            ranked.append(RankedOpportunity(card_id=card_id, score=float(c.opportunity_score), rank=c.rank or 9999, components=c.score_components_json or {}, requires_execution_verification=c.requires_manual_verification, observed_at=c.last_scored_at))
            inputs_by_card[card_id] = OpportunityInputs(
                card_id=card_id, observed_at=now, reference_price=1, reference_age_seconds=None,
                reference_uncertainty_pct=None, expected_net_profit=c.expected_net_profit,
                acquisition_probability=float(c.acquisition_probability) if c.acquisition_probability is not None else None,
                expected_discount_to_reference=float(c.expected_discount_to_reference) if c.expected_discount_to_reference is not None else None,
                profitable_exit_probability=float(c.profitable_exit_probability) if c.profitable_exit_probability is not None else None,
                liquidity_score=float(c.liquidity_score) if c.liquidity_score is not None else None,
                sell_through_rate=float(c.sell_through_rate) if c.sell_through_rate is not None else None,
                expected_holding_seconds=c.expected_holding_seconds,
                expected_profit_per_hour=float(c.expected_profit_per_hour) if c.expected_profit_per_hour is not None else None,
                position_capacity_coins=c.position_capacity_coins, volatility=float(c.volatility) if c.volatility is not None else None,
                downside_risk=float(c.downside_risk) if c.downside_risk is not None else None, ea_tax=0.05,
                catalyst_score=float(c.catalyst_score) if c.catalyst_score is not None else None,
                ea_intervention_risk=float(c.ea_intervention_risk) if c.ea_intervention_risk is not None else None,
                opportunity_cost=float(c.opportunity_cost) if c.opportunity_cost is not None else None,
                active_position=c.card_id in active_position_ids,
                rapid_movement_score=(c.metadata_json or {}).get("rapid_movement_score"),
                unusual_volume_score=(c.metadata_json or {}).get("unusual_volume_score"),
            )
        decisions = allocate_attention(ranked, inputs_by_card)
        apply_attention_allocations(session, decisions)
        session.commit()
        return {"allocated_cards": len(decisions)}


@app.task(name="fc27.recalculate_trader_reputation")
def recalculate_trader_reputation_task() -> dict:
    from fc27trader.services.reputation import recalculate_trader_reputation
    with SessionLocal() as session:
        count = recalculate_trader_reputation(session)
        session.commit()
        return {"traders_scored": count}


@app.task(name="fc27.run_strategy_backtests")
def run_strategy_backtests_task() -> dict:
    from fc27trader.services.strategy_backtesting import refresh_strategy_backtests
    with SessionLocal() as session:
        results = refresh_strategy_backtests(session)
        session.commit()
        return {"strategies_refreshed": len(results), "results": results}


@app.task(name="fc27.recalculate_strategy_trader_reputation")
def recalculate_strategy_trader_reputation_task() -> dict:
    from fc27trader.services.strategy_trader_reputation import recalculate_strategy_trader_reputation
    with SessionLocal() as session:
        count = recalculate_strategy_trader_reputation(session)
        session.commit()
        return {"strategy_trader_rows": count}
