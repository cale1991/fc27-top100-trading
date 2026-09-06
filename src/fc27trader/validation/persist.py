from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from fc27trader.db.models import (
    ProviderQualification,
    ProviderValidationObservation,
    ProviderValidationRun,
)

from .models import ProviderRole, QualificationReport


def persist_report(
    session: Session,
    report: QualificationReport,
    *,
    basket_version: str = "1",
    benchmark_source: str = "futbin_manual",
    game_year: int = 26,
) -> uuid.UUID:
    run_id = uuid.uuid4()
    run = ProviderValidationRun(
        id=run_id,
        provider_key=report.provider.key,
        benchmark_source=benchmark_source,
        platform="pc",
        game_year=game_year,
        basket_version=basket_version,
        started_at=report.tested_at,
        completed_at=datetime.now(UTC),
        status=report.status.value,
        required_cards=report.required_cards,
        paired_cards=report.paired_cards,
        config_json={"purpose": "provider_qualification_only_not_production_universe"},
        summary_json={
            "coverage_pct": report.coverage_pct,
            "freshness": report.freshness.model_dump(mode="json"),
            "qualified_roles": [r.value for r in report.qualified_roles],
            "role_reasons": report.role_reasons,
            "median_abs_pct_error": report.median_abs_pct_error,
            "p90_abs_pct_error": report.p90_abs_pct_error,
            "latency_p50_ms": report.latency_p50_ms,
            "latency_p95_ms": report.latency_p95_ms,
            "rejection_reasons": report.rejection_reasons,
        },
    )
    session.add(run)

    for o in report.observations:
        session.add(
            ProviderValidationObservation(
                run_id=run_id,
                provider_key=report.provider.key,
                card_key=o.card_key,
                category=o.category.value,
                provider_price_pc=o.provider_price_pc,
                benchmark_price_pc=o.benchmark_price_pc,
                provider_timestamp=o.provider_timestamp,
                provider_observed_at=o.provider_observed_at,
                benchmark_observed_at=o.benchmark_observed_at,
                http_latency_ms=Decimal(str(o.http_latency_ms)) if o.http_latency_ms is not None else None,
                provider_age_seconds=(
                    Decimal(str(o.provider_age_seconds)) if o.provider_age_seconds is not None else None
                ),
                observed_skew_seconds=Decimal(str(o.observed_skew_seconds)),
                absolute_error_coins=o.absolute_error_coins,
                absolute_pct_error=(
                    Decimal(str(o.absolute_pct_error)) if o.absolute_pct_error is not None else None
                ),
                raw_reference=o.raw_reference,
                metadata_json={"fields_available": o.fields_available},
            )
        )

    # One row per role makes provider usefulness queryable without treating
    # HOT_REFERENCE as a universal pass/fail gate.
    all_roles = list(ProviderRole)
    for role in all_roles:
        eligible = role in report.qualified_roles
        reasons = report.role_reasons.get(role.value, [])
        session.add(
            ProviderQualification(
                provider_key=report.provider.key,
                platform="pc",
                role=role.value,
                evaluated_at=report.tested_at,
                status="qualified" if eligible else "not_qualified",
                hot_market_eligible=eligible and role == ProviderRole.HOT_REFERENCE,
                coverage_pct=Decimal(str(report.coverage_pct)),
                timestamp_age_p95_seconds=(
                    Decimal(str(report.freshness.timestamp_age_p95_seconds))
                    if report.freshness.timestamp_age_p95_seconds is not None else None
                ),
                propagation_delay_p95_seconds=(
                    Decimal(str(report.freshness.propagation_delay_p95_seconds))
                    if report.freshness.propagation_delay_p95_seconds is not None else None
                ),
                latency_p95_ms=(
                    Decimal(str(report.latency_p95_ms)) if report.latency_p95_ms is not None else None
                ),
                median_abs_pct_error=(
                    Decimal(str(report.median_abs_pct_error))
                    if report.median_abs_pct_error is not None else None
                ),
                rejection_reasons_json=reasons,
                profile_json=report.provider.model_dump(mode="json"),
                report_json=report.model_dump(mode="json", exclude={"observations"}),
            )
        )
    session.commit()
    return run_id
