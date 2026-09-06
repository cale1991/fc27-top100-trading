from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from statistics import median

import orjson

from fc27trader.collectors.thecoinprinter import TheCoinPrinterCollector


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * q)))
    return ordered[idx]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure The Coin Printer PC-price coverage and provider-side timestamp freshness."
    )
    parser.add_argument("--pages", type=int, default=10)
    parser.add_argument("--take", type=int, default=50)
    parser.add_argument("--output", default="data/qualification/thecoinprinter.json")
    args = parser.parse_args()

    api_key = os.getenv("THECOINPRINTER_API_KEY")
    if not api_key:
        raise SystemExit("THECOINPRINTER_API_KEY is required")
    if not 1 <= args.take <= 50:
        raise SystemExit("--take must be between 1 and 50")

    collector = TheCoinPrinterCollector(api_key)
    now = datetime.now(UTC)
    rows: list[dict] = []
    for page in range(1, args.pages + 1):
        obs = collector.search_recent(page=page, take=args.take)[0]
        payload = orjson.loads(obs.body)
        rows.extend(payload.get("data", []))

    unique = {str(row.get("id")): row for row in rows if row.get("id") is not None}
    priced = [row for row in unique.values() if row.get("pc_price") not in (None, 0)]

    lags: list[float] = []
    for row in priced:
        updated = parse_timestamp(row.get("updated_at"))
        if updated is not None:
            lags.append(max(0.0, (now - updated).total_seconds()))

    report = {
        "measured_at": now.isoformat(),
        "pages_requested": args.pages,
        "take": args.take,
        "rows_received": len(rows),
        "unique_cards": len(unique),
        "cards_with_pc_price": len(priced),
        "pc_price_coverage_ratio": (len(priced) / len(unique)) if unique else 0.0,
        "cards_with_provider_timestamp": len(lags),
        "fresh_within_120s_ratio": (sum(v <= 120 for v in lags) / len(lags)) if lags else 0.0,
        "fresh_within_300s_ratio": (sum(v <= 300 for v in lags) / len(lags)) if lags else 0.0,
        "lag_seconds_min": min(lags) if lags else None,
        "lag_seconds_median": median(lags) if lags else None,
        "lag_seconds_p95": percentile(lags, 0.95),
        "lag_seconds_max": max(lags) if lags else None,
        "qualification_note": (
            "Do not enable as primary 2-minute market feed until coverage, pagination behavior, "
            "provider-side freshness, and intended data/model-use rights are verified."
        ),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
