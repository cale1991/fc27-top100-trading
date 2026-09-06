from __future__ import annotations

from datetime import UTC, datetime
from sqlalchemy import func, select

from fc27trader.db.models import (
    CardSourceId, ContentEvent, ExecutionObservation, MarketSegment, ProviderBudgetState,
    ProviderFeedEvent, ProviderHealth, ReferencePriceObservation, Source,
)
from fc27trader.db.session import SessionLocal
from fc27trader.settings import get_settings

SEGMENTS = ("PC", "PLAYSTATION", "CONSOLE_GENERIC", "CONSOLE_SHARED", "SWITCH", "UNKNOWN")
DEMO_SOURCE_KEYS = {"demo", "demo_reference", "demo_manual"}

def count(session, stmt): return int(session.scalar(stmt) or 0)

def age_seconds(ts):
    if not ts: return None
    if ts.tzinfo is None: ts=ts.replace(tzinfo=UTC)
    return max(0.0,(datetime.now(UTC)-ts).total_seconds())

with SessionLocal() as session:
    settings=get_settings()
    segments={x.segment_key:x for x in session.scalars(select(MarketSegment).where(MarketSegment.game_year==26))}
    sources={x.id:x.key for x in session.scalars(select(Source))}
    demo_ids={sid for sid,key in sources.items() if key in DEMO_SOURCE_KEYS or key.startswith("demo")}
    print("FC26 REAL DATA STATUS")
    for key in SEGMENTS:
        seg=segments.get(key)
        if not seg:
            print({"market":key,"status":"segment_not_seeded"}); continue
        refs=list(session.scalars(select(ReferencePriceObservation).where(ReferencePriceObservation.market_segment_id==seg.id)))
        execs=list(session.scalars(select(ExecutionObservation).where(ExecutionObservation.market_segment_id==seg.id)))
        real_refs=[x for x in refs if x.source_id not in demo_ids]
        demo_refs=[x for x in refs if x.source_id in demo_ids]
        real_execs=[x for x in execs if x.source_id not in demo_ids]
        demo_execs=[x for x in execs if x.source_id in demo_ids]
        print({
            "market":key,"executable_by_user":seg.executable_by_user,
            "real":{"cards_covered":len({x.card_id for x in real_refs+real_execs}),"providers":len({x.source_id for x in real_refs}),"reference_observations":len(real_refs),"execution_observations":len(real_execs),"manual_ladders":sum(1 for x in real_execs if (x.listing_count or 0)>1)},
            "demo":{"reference_observations":len(demo_refs),"execution_observations":len(demo_execs)},
        })

    futzip=session.scalar(select(Source).where(Source.key=="futzip"))
    if futzip:
        for feed in ("movers","new","sbc"):
            events=list(session.scalars(select(ProviderFeedEvent).where(ProviderFeedEvent.source_id==futzip.id,ProviderFeedEvent.feed_key==feed)))
            newest=max((x.provider_timestamp for x in events if x.provider_timestamp),default=None)
            print({"provider":"futzip","feed":feed,"events":len(events),"unique_provider_ids":len({x.provider_card_id for x in events if x.provider_card_id}),"latest_age_seconds":age_seconds(newest),"unknown_market":sum(1 for x in events if (segments.get("UNKNOWN") and x.market_segment_id==segments["UNKNOWN"].id)),"quarantined":sum(1 for x in events if x.quality_status=="QUARANTINED")})
    else: print({"provider":"futzip","status":"not_collected_yet"})

    print({"provider":"ea","content_events":count(session,select(func.count(ContentEvent.id)))})
    for row in session.scalars(select(ProviderHealth).order_by(ProviderHealth.provider_key,ProviderHealth.provider_role,ProviderHealth.platform)):
        print({"provider":row.provider_key,"role":row.provider_role,"market":row.platform,"status":row.status,"last_success":row.last_success_at,"last_error":row.last_error,"requests":row.requests_total,"errors":row.requests_failed,"error_rate":row.error_rate,"items_seen":row.items_seen,"items_ingested":row.items_ingested,"duplicates":row.duplicates_skipped,"quarantined":row.quarantined_observations,"cards_covered":row.cards_covered,"latest_age_seconds":row.latest_observation_age_seconds,"latency_ms":row.last_latency_ms,"rate_limit_remaining":row.rate_limit_remaining,"gap_status":row.gap_status})

    parse_src=session.scalar(select(Source).where(Source.key=="parse_futbin"))
    parse_maps=count(session,select(func.count(CardSourceId.id)).where(CardSourceId.source_id==parse_src.id)) if parse_src else 0
    parse_refs={}
    for k in ("PC","PLAYSTATION"):
        seg=segments.get(k)
        parse_refs[k]=count(session,select(func.count(ReferencePriceObservation.id)).where(ReferencePriceObservation.source_id==parse_src.id,ReferencePriceObservation.market_segment_id==seg.id)) if parse_src and seg else 0
    parse_health=session.scalar(select(ProviderHealth).where(ProviderHealth.provider_key=="parse_futbin").order_by(ProviderHealth.updated_at.desc()).limit(1))
    parse_budget=session.scalar(select(ProviderBudgetState).where(ProviderBudgetState.provider_key=="parse_futbin").order_by(ProviderBudgetState.updated_at.desc()).limit(1))
    print({"provider":"parse_futbin","enabled":settings.parse_futbin_enabled,"credential_configured":bool(settings.parse_api_key),"status":parse_health.status if parse_health else ("DISABLED" if not settings.parse_futbin_enabled else "NO_CREDENTIALS" if not settings.parse_api_key else "CONFIGURED_NOT_TESTED"),"provider_identities":parse_maps,"pc_reference_observations":parse_refs["PC"],"playstation_reference_observations":parse_refs["PLAYSTATION"],"cards_covered":parse_health.cards_covered if parse_health else 0,"latest_age_seconds":parse_health.latest_observation_age_seconds if parse_health else None,"last_success":parse_health.last_success_at if parse_health else None,"last_error":parse_health.last_error if parse_health else None,"requests_used":parse_budget.requests_used if parse_budget else 0,"credits_used":float(parse_budget.credits_used or 0) if parse_budget else 0})

    def ids(key):
        seg=segments.get(key)
        return set(session.scalars(select(ReferencePriceObservation.card_id).where(ReferencePriceObservation.market_segment_id==seg.id,ReferencePriceObservation.quality_status=="VALID").distinct())) if seg else set()
    sets={k:ids(k) for k in SEGMENTS[:-1]}
    console_union=sets["PLAYSTATION"]|sets["CONSOLE_GENERIC"]|sets["CONSOLE_SHARED"]
    print({"cross_market":{"pc_console":len(sets["PC"]&console_union),"pc_playstation":len(sets["PC"]&sets["PLAYSTATION"]),"pc_switch":len(sets["PC"]&sets["SWITCH"]),"pc_console_switch":len(sets["PC"]&console_union&sets["SWITCH"])}})
