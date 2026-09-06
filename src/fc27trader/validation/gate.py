from __future__ import annotations

from pathlib import Path

from .models import ProviderRole, QualificationReport


class ProviderRoleRejected(RuntimeError):
    pass


# Backward-compatible exception name.
HotMarketProviderRejected = ProviderRoleRejected


def require_provider_role(report_path: str | Path, role: ProviderRole) -> QualificationReport:
    report = QualificationReport.model_validate_json(Path(report_path).read_text(encoding="utf-8"))
    if not report.supports(role):
        reasons = "; ".join(report.role_reasons.get(role.value, [])) or report.freshness.reason
        raise ProviderRoleRejected(
            f"{report.provider.key} is not qualified for {role.value}: {reasons}"
        )
    return report


def require_hot_market_qualification(report_path: str | Path) -> QualificationReport:
    return require_provider_role(report_path, ProviderRole.HOT_REFERENCE)
