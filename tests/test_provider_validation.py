from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fc27trader.validation.evaluate import evaluate_provider
from fc27trader.validation.models import (
    BenchmarkQuote, CardCategory, MarketQuote, ProviderProfile, ProviderRole,
    QualificationStatus, TermsState, ValidationCard,
)


def make_data(age_seconds: int | None, n: int = 50):
    now = datetime.now(UTC)
    categories = ([CardCategory.FODDER] * 12 + [CardCategory.META_GOLD] * 10 +
                  [CardCategory.ICON_HERO] * 14 + [CardCategory.PROMO] * 14)
    cards = [ValidationCard(key=f"c{i}", name=f"Card {i}", category=categories[i], version="x") for i in range(n)]
    benchmark = {c.key: BenchmarkQuote(card_key=c.key, price_pc=10000+i*100, observed_at=now) for i,c in enumerate(cards)}
    quotes = {c.key: MarketQuote(provider="test", card_key=c.key, price_pc=10000+i*100,
                provider_timestamp=(now-timedelta(seconds=age_seconds)) if age_seconds is not None else None,
                observed_at=now, http_latency_ms=30) for i,c in enumerate(cards)}
    return cards, benchmark, quotes


def profile(terms=TermsState.ALLOWED):
    return ProviderProfile(key="test", name="Test", endpoint_or_surface="test", pc_supported=True,
                           terms_state=terms, terms_summary="ok",
                           declared_roles=[ProviderRole.REFERENCE, ProviderRole.HISTORICAL, ProviderRole.METADATA])


def test_stale_provider_keeps_reference_but_not_hot_reference():
    cards, benchmark, quotes = make_data(601)
    report = evaluate_provider(profile=profile(), cards=cards, benchmark=benchmark, quotes=quotes)
    assert report.status == QualificationStatus.PASS
    assert report.supports(ProviderRole.REFERENCE)
    assert report.supports(ProviderRole.HISTORICAL)
    assert not report.supports(ProviderRole.HOT_REFERENCE)
    assert report.latency_p50_ms == 30


def test_fresh_provider_adds_hot_reference_role():
    cards, benchmark, quotes = make_data(90)
    report = evaluate_provider(profile=profile(), cards=cards, benchmark=benchmark, quotes=quotes)
    assert report.supports(ProviderRole.HOT_REFERENCE)
    assert report.hot_reference_eligible


def test_missing_timestamp_does_not_destroy_reference_role():
    cards, benchmark, quotes = make_data(None)
    report = evaluate_provider(profile=profile(), cards=cards, benchmark=benchmark, quotes=quotes)
    assert report.supports(ProviderRole.REFERENCE)
    assert not report.supports(ProviderRole.HOT_REFERENCE)


def test_prohibited_provider_can_be_manual_benchmark_only():
    cards, benchmark, quotes = make_data(30)
    p = profile(TermsState.PROHIBITED)
    p.declared_roles = [ProviderRole.MANUAL_BENCHMARK]
    report = evaluate_provider(profile=p, cards=cards, benchmark=benchmark, quotes=quotes)
    assert report.supports(ProviderRole.MANUAL_BENCHMARK)
    assert not report.supports(ProviderRole.REFERENCE)


def test_50_card_coverage_required_for_price_roles():
    cards, benchmark, quotes = make_data(30)
    quotes.pop("c49")
    report = evaluate_provider(profile=profile(), cards=cards, benchmark=benchmark, quotes=quotes)
    assert not report.supports(ProviderRole.REFERENCE)
    assert not report.supports(ProviderRole.HOT_REFERENCE)
    assert report.supports(ProviderRole.METADATA)


def test_hot_reference_pair_is_optional():
    from fc27trader.validation.select import select_hot_market_pair
    assert select_hot_market_pair([]) is None
