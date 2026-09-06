from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

from fc27trader.domain.enums import Platform
from fc27trader.domain.market import MarketSnapshot


REQUIRED_COLUMNS = {"card_external_id", "source_key", "lowest_bin"}


def load_market_csv(path: str | Path) -> list[MarketSnapshot]:
    rows: list[MarketSnapshot] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}")
        for row in reader:
            observed = row.get("observed_at")
            observed_at = datetime.fromisoformat(observed) if observed else datetime.now(UTC)
            rows.append(
                MarketSnapshot(
                    card_external_id=row["card_external_id"],
                    source_key=row["source_key"],
                    platform=Platform(row.get("platform") or "pc"),
                    observed_at=observed_at,
                    lowest_bin=int(row["lowest_bin"]) if row.get("lowest_bin") else None,
                    best_bid=int(row["best_bid"]) if row.get("best_bid") else None,
                    active_listings=int(row["active_listings"]) if row.get("active_listings") else None,
                    sales_5m=int(row["sales_5m"]) if row.get("sales_5m") else None,
                    sales_15m=int(row["sales_15m"]) if row.get("sales_15m") else None,
                )
            )
    return rows
