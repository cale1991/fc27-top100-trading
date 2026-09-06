from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
import json

import httpx
import pytest

from fc27trader.collectors.base import RawObservation
from fc27trader.collectors.futzip import FutzipCollector, parse_futzip_rss
from fc27trader.collectors.http import ConditionalState, PublicHttpClient
from fc27trader.collectors.parse_futbin import ParseBotFutbinCollector, ParseBotFutbinRateLimit
from fc27trader.collectors.registry import build_collectors
from fc27trader.domain.enums import MarketSegmentKey
from fc27trader.features import consensus as consensus_mod
from fc27trader.features import cross_market as cross_mod
from fc27trader.services.market_segments import FC26_SEGMENTS
from fc27trader.services.parse_futbin_ingestion import parse_coin_price
from fc27trader.settings import Settings

MOVER = b'''<?xml version="1.0"?><rss><channel><item><title>Chawinga 97 -11.2%: 134,000 \xe2\x86\x92 119,000</title><link>https://futzip.com/player/67388663/chawinga</link><guid>move-67388663-2026-09-04T15:28:58.493114+00:00</guid><pubDate>Fri, 04 Sep 2026 15:28:58 GMT</pubDate><description>Chawinga moved</description></item></channel></rss>'''
NEW = b'''<rss><channel><item><title>Alex Example 91 added</title><link>https://futzip.com/player/12345678/example</link><guid>new-12345678-1</guid><pubDate>Fri, 04 Sep 2026 15:30:00 GMT</pubDate></item></channel></rss>'''
SBC = b'''<rss><channel><item><title>Icon Upgrade SBC</title><link>https://futzip.com/sbc/icon-upgrade</link><guid>sbc-icon-1</guid><pubDate>Fri, 04 Sep 2026 15:31:00 GMT</pubDate><description>New SBC detected</description></item></channel></rss>'''


def test_futzip_real_format_mover_parses_unknown_market_context():
    rows, failures = parse_futzip_rss(MOVER, "movers")
    assert not failures and len(rows) == 1
    row=rows[0]
    assert row.provider_card_id == "67388663" and row.rating == 97
    assert row.old_price == 134000 and row.new_price == 119000 and row.percentage_change == -11.2


def test_futzip_new_card_and_sbc_parse():
    new, nf=parse_futzip_rss(NEW,"new"); sbc,sf=parse_futzip_rss(SBC,"sbc")
    assert not nf and new[0].provider_card_id=="12345678" and new[0].rating==91
    assert not sf and sbc[0].guid=="sbc-icon-1"


def test_futzip_malformed_item_isolated():
    body=b'<rss><channel><item><title>bad</title></item><item><title>Demb\xc3\xa9l\xc3\xa9 95 -1.3%: 19,750 \xe2\x86\x92 19,500</title><guid>good</guid><pubDate>Fri, 04 Sep 2026 15:30:00 GMT</pubDate></item></channel></rss>'
    rows, failures=parse_futzip_rss(body,"movers")
    assert len(rows)==1 and rows[0].new_price==19500 and len(failures)==1


def test_conditional_http_sends_etag_and_last_modified_and_handles_304():
    seen={}
    def handler(req:httpx.Request):
        seen.update(req.headers)
        return httpx.Response(304,headers={"etag":"newtag","last-modified":"Fri, 04 Sep 2026 15:00:00 GMT"})
    c=PublicHttpClient(max_attempts=1); c.client=httpx.Client(transport=httpx.MockTransport(handler))
    r=c.get("https://example.test/feed", ConditionalState(etag="oldtag",last_modified="oldtime"))
    assert r.status_code==304 and seen.get("if-none-match")=="oldtag" and seen.get("if-modified-since")=="oldtime"


def test_futzip_collector_preserves_unknown_semantics():
    class H:
        def get(self,url,state=None): return httpx.Response(200,content=MOVER,headers={"content-type":"application/rss+xml","etag":"e"})
    obs=FutzipCollector(http=H()).collect_feed("movers")[0]
    assert obs.metadata["market_segment"]=="UNKNOWN" and obs.metadata["observation_semantics"]=="MARKET_CONTEXT"


def test_market_segments_are_configurable_and_pc_only_executable():
    by={x["segment_key"]:x for x in FC26_SEGMENTS}
    assert by["PC"]["executable_by_user"] is True
    for key in ("PLAYSTATION","CONSOLE_GENERIC","CONSOLE_SHARED","SWITCH","UNKNOWN"):
        assert by[key]["executable_by_user"] is False
    assert by["PLAYSTATION"]["platform_group"] != by["CONSOLE_SHARED"]["platform_group"]


def test_parse_disabled_and_missing_key_are_optional():
    settings=Settings(parse_futbin_enabled=False,parse_api_key="")
    assert "parse_futbin" not in build_collectors(settings)
    settings=Settings(parse_futbin_enabled=True,parse_api_key="")
    assert "parse_futbin" not in build_collectors(settings)


def test_parse_collector_requires_key_only_when_instantiated():
    with pytest.raises(ValueError): ParseBotFutbinCollector("")


def test_parse_collector_catalogue_request_and_secret_redaction():
    secret="PARSE_SUPER_SECRET_123456789"
    def ok(req:httpx.Request):
        assert req.headers["X-API-Key"]==secret
        return httpx.Response(200,json={"data":{"players":[{"id":1,"name":"A","price_pc":"101K","price_ps":"98K"}]}})
    client=httpx.Client(transport=httpx.MockTransport(ok))
    c=ParseBotFutbinCollector(secret,client=client,base_url="https://example.test")
    obs=c.collect_catalogue_page(1)[0]
    assert obs.metadata["endpoint"]=="get_players" and secret.encode() not in obs.body
    def bad(req): return httpx.Response(500,text=secret)
    c.client=httpx.Client(transport=httpx.MockTransport(bad))
    with pytest.raises(Exception) as exc: c.collect_catalogue_page(1)
    assert secret not in str(exc.value)


def test_parse_rate_limit_isolated_and_retry_after_exposed():
    c=ParseBotFutbinCollector("not-a-real-secret",client=httpx.Client(transport=httpx.MockTransport(lambda req:httpx.Response(429,headers={"Retry-After":"60"}))),base_url="https://example.test")
    with pytest.raises(ParseBotFutbinRateLimit) as exc: c.collect_catalogue_page(1)
    assert exc.value.retry_after==60

@pytest.mark.parametrize("raw,expected",[("101K",101000),("1.2M",1200000),("98,500",98500),(0,0),(None,None)])
def test_parse_coin_price(raw,expected): assert parse_coin_price(raw)==expected


def test_parse_provider_market_semantics_are_separate_in_source():
    text=Path("src/fc27trader/services/parse_futbin_ingestion.py").read_text()
    assert 'field="price_pc"' in text and 'MarketSegmentKey.PC.value' in text
    assert 'field="price_ps"' in text and 'MarketSegmentKey.PLAYSTATION.value' in text
    assert "ExecutionObservation" not in text


def test_parse_reference_cannot_overwrite_execution_mark():
    from fc27trader.services.app_queries import _portfolio_executable_mark
    assert _portfolio_executable_mark(None) is None
    e=SimpleNamespace(lowest_bin=95500)
    assert _portfolio_executable_mark(e)==95500


def test_point_in_time_queries_use_knowledge_time_and_valid_quality():
    text=Path("src/fc27trader/features/point_in_time.py").read_text()
    assert "inserted_at" in text and "<= cutoff" in text and 'quality_status == "VALID"' in text


def test_consensus_is_segment_scoped_and_preserves_disagreement(monkeypatch):
    now=datetime.now(UTC)
    refs=[SimpleNamespace(id=1,source_id="a",provider_timestamp=now,observed_at=now,price=100000,confidence=.8),SimpleNamespace(id=2,source_id="b",provider_timestamp=now,observed_at=now,price=108000,confidence=.8),SimpleNamespace(id=3,source_id="c",provider_timestamp=now,observed_at=now,price=101000,confidence=.8)]
    monkeypatch.setattr(consensus_mod,"reference_observations_known_at",lambda *a,**k: refs)
    monkeypatch.setattr(consensus_mod,"execution_observations_known_at",lambda *a,**k: [])
    class S:
        def get(self,model,key): return SimpleNamespace(key=key)
    out=consensus_mod.calculate_market_consensus(S(),card_id="c",market_segment_id="PC",cutoff=now)
    assert out["provider_count"]==3 and out["min_reference"]==100000 and out["max_reference"]==108000
    assert out["disagreement_score"]>0 and len(out["source_observation_ids"])==3


def test_consensus_stale_sources_counted_without_mixing_unknown(monkeypatch):
    now=datetime.now(UTC); old=now-timedelta(hours=2)
    refs=[SimpleNamespace(id=1,source_id="a",provider_timestamp=old,observed_at=old,price=100000,confidence=.8)]
    monkeypatch.setattr(consensus_mod,"reference_observations_known_at",lambda *a,**k: refs)
    monkeypatch.setattr(consensus_mod,"execution_observations_known_at",lambda *a,**k: [])
    class S:
        def get(self,model,key): return SimpleNamespace(key=key)
    out=consensus_mod.calculate_market_consensus(S(),card_id="c",market_segment_id="PC",cutoff=now)
    assert out["provider_count"]==1 and out["fresh_provider_count"]==0 and out["stale_source_ratio"]==1


def test_cross_market_calculations_do_not_assume_console_leads(monkeypatch):
    prices={"PC":100000,"PLAYSTATION":115000,"SWITCH":90000}
    monkeypatch.setattr(cross_mod,"calculate_market_consensus",lambda s,card_id,market_segment_id,cutoff:{"weighted_median_reference_price":prices.get(market_segment_id),"source_observation_ids":[]})
    segs={k:SimpleNamespace(id=k) for k in prices}
    out=cross_mod.calculate_cross_market_features(None,card_id="c",game_year=26,segments=segs,cutoff=datetime.now(UTC))
    assert out["pc_console_ratio"]==pytest.approx(100000/115000)
    assert out["lead_lag_seconds"] is None and out["convergence_probability"] is None


def test_unknown_platform_never_becomes_specific_reference_by_futzip_contract():
    ingest=Path("src/fc27trader/services/futzip_ingestion.py").read_text()
    assert "MarketSegmentKey.UNKNOWN.value" in ingest
    assert '"pc_references_created": 0' in ingest and '"console_references_created": 0' in ingest and '"switch_references_created": 0' in ingest


def test_phase2_migration_descends_from_phase1_and_seeds_market_segments():
    text=Path("migrations/versions/0008_fc26_multisource_multimarket.py").read_text()
    assert 'down_revision = "0007_fc26_real_market_phase1"' in text or "down_revision = '0007_fc26_real_market_phase1'" in text
    for key in ("PC","PLAYSTATION","CONSOLE_GENERIC","CONSOLE_SHARED","SWITCH","UNKNOWN"):
        assert key in text


def test_release_validator_keeps_packaging_regressions_and_parse_secret_scan():
    text=Path("scripts/validate_release_package.py").read_text()
    assert "seed_strategy_library" in text and "seed_strategy_research" in text
    assert "ensure_alembic_version_capacity" in text and "PARSE_API_KEY" in text


def test_no_provider_is_required_at_startup():
    settings=Settings(futdb_api_key="",thecoinprinter_api_key="",parse_futbin_enabled=False,parse_api_key="")
    keys=set(build_collectors(settings))
    assert "futdb" not in keys and "thecoinprinter" not in keys and "parse_futbin" not in keys
    assert "ea_news_fc26" in keys

def test_futzip_db_identity_dedupes_guid_but_allows_later_move_same_card():
    from fc27trader.db.models import ProviderFeedEvent
    constraints={c.name:tuple(c.columns.keys()) for c in ProviderFeedEvent.__table__.constraints if getattr(c,"name",None)}
    assert constraints["uq_provider_feed_event_identity"] == ("source_id","feed_key","provider_event_id")
    # Provider card ID is intentionally absent: later GUIDs for the same card append history.
    assert "provider_card_id" not in constraints["uq_provider_feed_event_identity"]


def test_futzip_normalized_event_retains_raw_lineage_contract():
    from fc27trader.db.models import ProviderFeedEvent
    cols=ProviderFeedEvent.__table__.columns
    assert "raw_ingest_id" in cols and "payload_json" in cols and "parser_version" in cols
    assert "retrieved_at" in cols and "provider_timestamp" in cols and "inserted_at" in cols


def test_reference_observation_dedupe_is_event_identity_not_permanent_price_overwrite():
    from fc27trader.db.repositories import reference_observation_key
    from uuid import uuid4
    card,source,seg=uuid4(),uuid4(),uuid4(); t=datetime.now(UTC)
    a=reference_observation_key(card_id=card,source_id=source,platform="pc",market_segment_id=seg,provider_timestamp=None,observed_at=t,price=100000,price_kind="reference")
    b=reference_observation_key(card_id=card,source_id=source,platform="pc",market_segment_id=seg,provider_timestamp=None,observed_at=t,price=100000,price_kind="reference")
    c=reference_observation_key(card_id=card,source_id=source,platform="pc",market_segment_id=seg,provider_timestamp=None,observed_at=t+timedelta(minutes=5),price=101000,price_kind="reference")
    assert a==b and c!=a


def test_non_pc_research_signal_can_create_pc_verification_request(monkeypatch):
    import uuid
    from fc27trader.services import cross_market_verification as mod
    card_id=uuid.uuid4(); source=SimpleNamespace(id=uuid.uuid4(),game_year=26,segment_key="PLAYSTATION",executable_by_user=False)
    pc=SimpleNamespace(id=uuid.uuid4(),game_year=26,segment_key="PC",executable_by_user=True)
    monkeypatch.setattr(mod,"get_market_segment",lambda *a,**k:pc)
    class FakeSession:
        def __init__(self): self.added=[]
        def scalar(self,*a,**k): return None
        def add(self,x): self.added.append(x)
        def flush(self): pass
    session=FakeSession()
    req=mod.create_pc_verification_from_research_signal(session,card_id=card_id,source_market_segment=source,reason="Console moved while PC execution is unknown")
    assert req is session.added[0]
    assert req.market_segment_id==pc.id and req.platform=="pc"
    assert req.metadata_json["source_market_segment"]=="PLAYSTATION"
    assert "5-10 PC BIN" in req.required_information


def test_card_research_exposes_content_events_separately_from_price_evidence():
    text=Path("src/fc27trader/services/app_queries.py").read_text()
    assert '"content_events"' in text
    assert "select(EventImpact, ContentEvent)" in text
    ui=Path("web/app/market/page.tsx").read_text()
    assert "Content & catalysts" in ui
