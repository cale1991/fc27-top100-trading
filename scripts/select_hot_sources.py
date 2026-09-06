#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from fc27trader.validation.models import ProviderRole, QualificationReport
from fc27trader.validation.select import rank_providers_for_role, select_provider_pair


def main() -> int:
    ap = argparse.ArgumentParser(description="Rank providers for a role; redundancy is optional")
    ap.add_argument("reports", nargs="+", help="Qualification report JSON files")
    ap.add_argument("--role", default="hot_reference", choices=[r.value for r in ProviderRole])
    ap.add_argument("--policy", default="config/provider_validation.yaml")
    args = ap.parse_args()

    reports = [QualificationReport.model_validate(json.loads(Path(p).read_text(encoding="utf-8"))) for p in args.reports]
    role = ProviderRole(args.role)
    ranked = rank_providers_for_role(reports, role)
    print(f"role={role.value}")
    print("ranked=" + ",".join(r.provider.key for r in ranked))

    policy = yaml.safe_load(Path(args.policy).read_text(encoding="utf-8"))
    independence = policy.get("fallback_independence", {})
    pair = select_provider_pair(
        reports,
        role=role,
        require_known_upstream_provenance=independence.get("require_known_upstream_provenance", True),
        require_different_upstream=independence.get("require_different_upstream", True),
    )
    if pair:
        print(f"primary={pair.primary.provider.key}")
        print(f"fallback={pair.fallback.provider.key}")
    else:
        print("primary=" + (ranked[0].provider.key if ranked else "UNRESOLVED"))
        print("fallback=UNRESOLVED")
        print("note=no independent fallback qualified for this role; this does not block other roles/system development")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
