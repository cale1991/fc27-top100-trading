from __future__ import annotations

from dataclasses import dataclass

from .models import ProviderRole, QualificationReport


@dataclass(frozen=True)
class ProviderPair:
    primary: QualificationReport
    fallback: QualificationReport


# Backward compatible name; this now explicitly means HOT_REFERENCE only.
HotMarketPair = ProviderPair


def _rank_key(report: QualificationReport, role: ProviderRole) -> tuple[float, float, float, str]:
    accuracy = report.median_abs_pct_error if report.median_abs_pct_error is not None else float("inf")
    freshness = (
        report.freshness.timestamp_age_p95_seconds
        if report.freshness.timestamp_age_p95_seconds is not None
        else report.freshness.propagation_delay_p95_seconds
    )
    freshness = freshness if freshness is not None else float("inf")
    latency = report.latency_p95_ms if report.latency_p95_ms is not None else float("inf")
    if role == ProviderRole.HOT_REFERENCE:
        return (freshness, accuracy, latency, report.provider.key)
    return (accuracy, freshness, latency, report.provider.key)


def rank_providers_for_role(
    reports: list[QualificationReport], role: ProviderRole
) -> list[QualificationReport]:
    eligible = [r for r in reports if r.supports(role)]
    eligible.sort(key=lambda r: _rank_key(r, role))
    return eligible


def select_provider_pair(
    reports: list[QualificationReport],
    *,
    role: ProviderRole,
    require_known_upstream_provenance: bool = True,
    require_different_upstream: bool = True,
) -> ProviderPair | None:
    """Optional redundancy selector for a role.

    Returns None if two independent sources are not available. This is not a
    global system gate; slower/reference/manual paths remain usable.
    """
    eligible = rank_providers_for_role(reports, role)
    if len(eligible) < 2:
        return None
    for i, primary in enumerate(eligible):
        p_up = (primary.provider.upstream_provenance or "").strip().lower()
        if require_known_upstream_provenance and (not p_up or p_up == "unknown"):
            continue
        for fallback in eligible[i + 1:]:
            f_up = (fallback.provider.upstream_provenance or "").strip().lower()
            if require_known_upstream_provenance and (not f_up or f_up == "unknown"):
                continue
            if require_different_upstream and p_up == f_up:
                continue
            return ProviderPair(primary=primary, fallback=fallback)
    return None


def select_hot_market_pair(
    reports: list[QualificationReport],
    *,
    require_known_upstream_provenance: bool = True,
    require_different_upstream: bool = True,
) -> ProviderPair | None:
    """Deprecated compatibility wrapper for HOT_REFERENCE redundancy."""
    return select_provider_pair(
        reports,
        role=ProviderRole.HOT_REFERENCE,
        require_known_upstream_provenance=require_known_upstream_provenance,
        require_different_upstream=require_different_upstream,
    )
