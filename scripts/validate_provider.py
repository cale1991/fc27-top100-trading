#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

import yaml

from fc27trader.validation.evaluate import evaluate_provider
from fc27trader.validation.io import (
    load_basket,
    load_benchmark_csv,
    load_provider_catalog,
    load_provider_quotes_csv,
    write_report_csv,
    write_report_json,
)
from fc27trader.validation.providers.futnext import FutNextValidationProvider
from fc27trader.validation.providers.thecoinprinter import TheCoinPrinterValidationProvider


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Benchmark/classify an FC26 PC market-data provider against the fixed FUTBIN qualification basket")
    p.add_argument("--provider", required=True)
    p.add_argument("--benchmark-csv", required=True)
    p.add_argument("--quotes-csv", help="Use captured provider quotes instead of live provider adapter")
    p.add_argument("--basket", default="config/validation_basket_fc26.yaml")
    p.add_argument("--catalog", default="config/provider_catalog_fc26.yaml")
    p.add_argument("--policy", default="config/provider_validation.yaml")
    p.add_argument("--output-dir", default="data/validation/runs")
    p.add_argument("--persist-db", action="store_true", help="Persist run/observations/qualification to PostgreSQL")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    cards = load_basket(args.basket)
    catalog = load_provider_catalog(args.catalog)
    if args.provider not in catalog:
        raise SystemExit(f"Unknown provider: {args.provider}")
    profile = catalog[args.provider]
    benchmark = load_benchmark_csv(args.benchmark_csv)

    if args.quotes_csv:
        quotes = load_provider_quotes_csv(args.quotes_csv, args.provider)
    elif args.provider == "thecoinprinter":
        quotes = TheCoinPrinterValidationProvider(os.getenv("THECOINPRINTER_API_KEY", "")).fetch_quotes(cards)
    elif args.provider == "futnext":
        unresolved = [c.key for c in cards if c.ea_definition_id is None]
        if unresolved:
            raise SystemExit(
                "FUTNext requires verified ea_definition_id for every basket card. "
                f"Missing {len(unresolved)} IDs. Do not guess them: {', '.join(unresolved[:8])}"
            )
        quotes = FutNextValidationProvider().fetch_quotes(cards)
    else:
        raise SystemExit(
            f"{args.provider} has no authorized live adapter. Capture quotes into CSV and pass --quotes-csv."
        )

    policy = yaml.safe_load(Path(args.policy).read_text(encoding="utf-8"))
    report = evaluate_provider(
        profile=profile,
        cards=cards,
        benchmark=benchmark,
        quotes=quotes,
        max_effective_staleness_seconds=policy["hard_gates"]["max_effective_staleness_seconds"],
        min_cards=policy["hard_gates"]["min_paired_cards"],
        category_minimums=policy["category_minimums"],
        min_propagation_events=policy["freshness"]["propagation_test"]["minimum_benchmark_changes"],
        max_observation_skew_seconds=policy["benchmark"]["maximum_observation_skew_seconds"],
    )

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{args.provider}-{report.tested_at.strftime('%Y%m%dT%H%M%SZ')}"
    json_path = out / f"{stem}.json"
    csv_path = out / f"{stem}.csv"
    write_report_json(json_path, report)
    write_report_csv(csv_path, report)

    print(f"provider={args.provider}")
    print(f"status={report.status.value}")
    print(f"hot_reference_eligible={report.hot_reference_eligible}")
    print("qualified_roles=" + ",".join(r.value for r in report.qualified_roles))
    print(f"paired_cards={report.paired_cards}/{report.required_cards}")
    print(f"coverage_pct={report.coverage_pct:.1f}")
    print(f"freshness={report.freshness.reason}")
    print(f"median_abs_pct_error={report.median_abs_pct_error}")
    print(f"report={json_path}")
    if args.persist_db:
        from fc27trader.db.session import SessionLocal
        from fc27trader.validation.persist import persist_report
        with SessionLocal() as session:
            run_id = persist_report(session, report)
        print(f"db_run_id={run_id}")
    if report.rejection_reasons:
        print("reasons:")
        for reason in report.rejection_reasons:
            print(f"- {reason}")
    return 0 if report.qualified_roles else 2


if __name__ == "__main__":
    raise SystemExit(main())
