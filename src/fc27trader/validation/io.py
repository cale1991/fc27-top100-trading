from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

import yaml

from .models import BenchmarkQuote, MarketQuote, ProviderProfile, ValidationCard


def load_basket(path: str | Path) -> list[ValidationCard]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return [ValidationCard.model_validate(item) for item in data["cards"]]


def load_provider_catalog(path: str | Path) -> dict[str, ProviderProfile]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return {
        key: ProviderProfile.model_validate({"key": key, **value})
        for key, value in data["providers"].items()
    }


def load_benchmark_csv(path: str | Path) -> dict[str, BenchmarkQuote]:
    out: dict[str, BenchmarkQuote] = {}
    with Path(path).open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if not row.get("price_pc"):
                continue
            out[row["card_key"]] = BenchmarkQuote(
                card_key=row["card_key"],
                price_pc=int(row["price_pc"]),
                observed_at=datetime.fromisoformat(row["observed_at"].replace("Z", "+00:00")),
                provider_timestamp=(
                    datetime.fromisoformat(row["provider_timestamp"].replace("Z", "+00:00"))
                    if row.get("provider_timestamp")
                    else None
                ),
                source=row.get("source") or "futbin_manual",
                raw_reference=row.get("raw_reference") or None,
            )
    return out


def load_provider_quotes_csv(path: str | Path, provider: str) -> dict[str, MarketQuote]:
    out: dict[str, MarketQuote] = {}
    with Path(path).open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            out[row["card_key"]] = MarketQuote(
                provider=provider,
                card_key=row["card_key"],
                price_pc=int(row["price_pc"]) if row.get("price_pc") else None,
                provider_timestamp=(
                    datetime.fromisoformat(row["provider_timestamp"].replace("Z", "+00:00"))
                    if row.get("provider_timestamp")
                    else None
                ),
                observed_at=datetime.fromisoformat(row["observed_at"].replace("Z", "+00:00")),
                http_latency_ms=float(row["http_latency_ms"]) if row.get("http_latency_ms") else None,
                source_card_id=row.get("source_card_id") or None,
                fields_available=(row.get("fields_available") or "").split("|") if row.get("fields_available") else [],
                raw_reference=row.get("raw_reference") or None,
            )
    return out


def write_report_json(path: str | Path, report) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report.model_dump_json(indent=2), encoding="utf-8")


def write_report_csv(path: str | Path, report) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "provider", "card_key", "category", "benchmark_price_pc", "provider_price_pc",
        "benchmark_observed_at", "provider_observed_at", "provider_timestamp",
        "http_latency_ms", "provider_age_seconds", "observed_skew_seconds",
        "absolute_error_coins", "absolute_pct_error", "raw_reference",
    ]
    with target.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for o in report.observations:
            writer.writerow({
                "provider": o.provider,
                "card_key": o.card_key,
                "category": o.category.value,
                "benchmark_price_pc": o.benchmark_price_pc,
                "provider_price_pc": o.provider_price_pc,
                "benchmark_observed_at": o.benchmark_observed_at.isoformat(),
                "provider_observed_at": o.provider_observed_at.isoformat(),
                "provider_timestamp": o.provider_timestamp.isoformat() if o.provider_timestamp else "",
                "http_latency_ms": o.http_latency_ms,
                "provider_age_seconds": o.provider_age_seconds,
                "observed_skew_seconds": o.observed_skew_seconds,
                "absolute_error_coins": o.absolute_error_coins,
                "absolute_pct_error": o.absolute_pct_error,
                "raw_reference": o.raw_reference,
            })
