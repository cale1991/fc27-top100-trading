from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from statistics import median

from .metrics import p50, p90, p95
from .models import (
    BenchmarkQuote,
    FreshnessEvidence,
    MarketQuote,
    PairedObservation,
    PropagationObservation,
    ProviderProfile,
    ProviderRole,
    QualificationReport,
    QualificationStatus,
    TermsState,
    ValidationCard,
)

_AUTOMATION_OK = {TermsState.ALLOWED, TermsState.LICENSE_REQUIRED}


def _age_seconds(quote: MarketQuote) -> float | None:
    if quote.provider_timestamp is None:
        return None
    return max(0.0, (quote.observed_at - quote.provider_timestamp).total_seconds())


def pair_observations(
    profile: ProviderProfile,
    cards: list[ValidationCard],
    benchmark: dict[str, BenchmarkQuote],
    quotes: dict[str, MarketQuote],
) -> list[PairedObservation]:
    card_map = {c.key: c for c in cards}
    paired: list[PairedObservation] = []
    for key, bench in benchmark.items():
        card = card_map.get(key)
        quote = quotes.get(key)
        if card is None or quote is None:
            continue
        error = None if quote.price_pc is None else abs(quote.price_pc - bench.price_pc)
        ape = None
        if error is not None and bench.price_pc > 0:
            ape = error / bench.price_pc
        paired.append(
            PairedObservation(
                provider=profile.key,
                card_key=key,
                category=card.category,
                benchmark_price_pc=bench.price_pc,
                provider_price_pc=quote.price_pc,
                benchmark_observed_at=bench.observed_at,
                provider_observed_at=quote.observed_at,
                provider_timestamp=quote.provider_timestamp,
                http_latency_ms=quote.http_latency_ms,
                provider_age_seconds=_age_seconds(quote),
                observed_skew_seconds=abs((quote.observed_at - bench.observed_at).total_seconds()),
                absolute_error_coins=error,
                absolute_pct_error=ape,
                fields_available=quote.fields_available,
                raw_reference=quote.raw_reference,
            )
        )
    return paired


def evaluate_provider(
    *,
    profile: ProviderProfile,
    cards: list[ValidationCard],
    benchmark: dict[str, BenchmarkQuote],
    quotes: dict[str, MarketQuote],
    max_effective_staleness_seconds: int = 300,
    min_cards: int = 50,
    category_minimums: dict[str, int] | None = None,
    propagation: list[PropagationObservation] | None = None,
    min_propagation_events: int = 5,
    max_observation_skew_seconds: int = 120,
) -> QualificationReport:
    """Benchmark a provider and classify the roles it can safely serve.

    The 50-card basket is only a controlled provider benchmark. Failure of the
    <=300 second test removes HOT_REFERENCE; it does *not* invalidate slower
    REFERENCE/HISTORICAL roles or block the rest of the system.
    """
    category_minimums = category_minimums or {
        "fodder": 12,
        "meta_gold": 10,
        "icon_hero": 14,
        "promo": 14,
    }
    observations = pair_observations(profile, cards, benchmark, quotes)
    priced = [o for o in observations if o.provider_price_pc is not None]
    counts = Counter(str(o.category.value) for o in priced)

    coverage_reasons: list[str] = []
    if not profile.pc_supported:
        coverage_reasons.append("provider does not support a distinct PC market")
    if len(priced) < min_cards:
        coverage_reasons.append(f"only {len(priced)} priced paired cards; minimum is {min_cards}")
    for category, minimum in category_minimums.items():
        if counts.get(category, 0) < minimum:
            coverage_reasons.append(
                f"category {category} has {counts.get(category, 0)} paired prices; minimum is {minimum}"
            )

    skews = [o.observed_skew_seconds for o in priced]
    if skews and max(skews) > max_observation_skew_seconds:
        coverage_reasons.append(
            f"benchmark/provider observation skew max={max(skews):.1f}s exceeds {max_observation_skew_seconds}s"
        )

    ages = [o.provider_age_seconds for o in priced if o.provider_age_seconds is not None]
    prop_delays = [p.delay_seconds for p in (propagation or []) if p.delay_seconds is not None]
    timestamp_p95 = p95(ages)
    prop_p95 = p95(prop_delays)

    if ages and len(ages) == len(priced):
        age_max = max(ages)
        freshness_proven = age_max <= max_effective_staleness_seconds
        freshness_reason = (
            "all priced samples carried provider timestamps; "
            f"p95 age={timestamp_p95:.1f}s, max age={age_max:.1f}s"
        )
    elif len(prop_delays) >= min_propagation_events:
        prop_max = max(prop_delays)
        freshness_proven = prop_max <= max_effective_staleness_seconds
        freshness_reason = (
            "provider lacks complete timestamps; freshness inferred from benchmark-change propagation; "
            f"events={len(prop_delays)}, p95 delay={prop_p95:.1f}s, max delay={prop_max:.1f}s"
        )
    else:
        freshness_proven = False
        freshness_reason = (
            "provider does not expose a timestamp for every priced sample and no sufficient "
            "benchmark-change propagation evidence was recorded; HOT_REFERENCE freshness is unproven"
        )

    apes = [o.absolute_pct_error for o in priced if o.absolute_pct_error is not None]
    abs_errors = [float(o.absolute_error_coins) for o in priced if o.absolute_error_coins is not None]
    latencies = [float(o.http_latency_ms) for o in priced if o.http_latency_ms is not None]

    authorized_automation = profile.terms_state in _AUTOMATION_OK
    full_benchmark = not coverage_reasons
    declared = set(profile.declared_roles)
    qualified: set[ProviderRole] = set()
    role_reasons: dict[str, list[str]] = {}

    def deny(role: ProviderRole, *reasons: str) -> None:
        role_reasons[role.value] = [r for r in reasons if r]

    # Manual benchmarking remains a valid classification for sources that must
    # not be automatically ingested (e.g. FUTBIN under current terms).
    if ProviderRole.MANUAL_BENCHMARK in declared:
        qualified.add(ProviderRole.MANUAL_BENCHMARK)

    if authorized_automation:
        if ProviderRole.CONTENT in declared:
            qualified.add(ProviderRole.CONTENT)
        if ProviderRole.METADATA in declared:
            qualified.add(ProviderRole.METADATA)

        if profile.pc_supported and full_benchmark and priced:
            qualified.add(ProviderRole.REFERENCE)
            qualified.add(ProviderRole.HISTORICAL)
            if freshness_proven:
                qualified.add(ProviderRole.HOT_REFERENCE)
            else:
                deny(ProviderRole.HOT_REFERENCE, freshness_reason)
        elif priced:
            deny(ProviderRole.REFERENCE, *coverage_reasons)
            deny(ProviderRole.HISTORICAL, *coverage_reasons)
            deny(ProviderRole.HOT_REFERENCE, *coverage_reasons)
    else:
        automation_reason = (
            f"terms_state={profile.terms_state.value}; automated production use is not currently authorized"
        )
        for role in (ProviderRole.HOT_REFERENCE, ProviderRole.REFERENCE, ProviderRole.HISTORICAL, ProviderRole.METADATA, ProviderRole.CONTENT):
            if role in declared or role in {ProviderRole.HOT_REFERENCE, ProviderRole.REFERENCE, ProviderRole.HISTORICAL}:
                deny(role, automation_reason)

    # Declared non-price roles should not be silently invented from fields.
    # Price roles are derived from the controlled benchmark above.
    hot_reference = ProviderRole.HOT_REFERENCE in qualified
    if qualified:
        status = QualificationStatus.PASS
    elif profile.terms_state in {TermsState.PERMISSION_REQUIRED, TermsState.UNRESOLVED}:
        status = QualificationStatus.INCONCLUSIVE
    else:
        status = QualificationStatus.FAIL

    general_reasons: list[str] = []
    if not qualified:
        general_reasons.extend(coverage_reasons)
        if not authorized_automation:
            general_reasons.append(
                f"terms_state={profile.terms_state.value}; no currently authorized automated role qualified"
            )
        if not freshness_proven:
            general_reasons.append(freshness_reason)

    return QualificationReport(
        provider=profile,
        status=status,
        qualified_roles=sorted(qualified, key=lambda r: r.value),
        role_reasons=role_reasons,
        hot_reference_eligible=hot_reference,
        hot_market_eligible=hot_reference,
        tested_at=datetime.now(UTC),
        required_cards=min_cards,
        paired_cards=len(priced),
        coverage_pct=(len(priced) / max(1, len(cards))) * 100,
        category_counts=dict(counts),
        freshness=FreshnessEvidence(
            timestamped_samples=len(ages),
            timestamp_age_p50_seconds=p50(ages),
            timestamp_age_p95_seconds=timestamp_p95,
            timestamp_age_max_seconds=max(ages) if ages else None,
            propagation_events=len(prop_delays),
            propagation_delay_p50_seconds=p50(prop_delays),
            propagation_delay_p95_seconds=prop_p95,
            freshness_proven=freshness_proven,
            reason=freshness_reason,
        ),
        latency_p50_ms=p50(latencies),
        latency_p95_ms=p95(latencies),
        median_abs_pct_error=float(median(apes)) if apes else None,
        p90_abs_pct_error=p90(apes),
        median_abs_error_coins=float(median(abs_errors)) if abs_errors else None,
        rejection_reasons=general_reasons,
        observations=observations,
    )
