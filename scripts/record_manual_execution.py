#!/usr/bin/env python3
"""CLI fallback for recording a manual PC listing sample without the API/UI."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
import uuid

from fc27trader.db.models import Card
from fc27trader.db.repositories import insert_execution_observation
from fc27trader.db.session import SessionLocal
from fc27trader.services.verification_confidence import calculate_manual_observation_confidence


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card-id", required=True)
    ap.add_argument("--listings", required=True, help="comma-separated PC BIN prices")
    ap.add_argument("--observed-at", help="ISO-8601 observation time; defaults to now")
    ap.add_argument("--approximate", action="store_true", help="mark values as approximate rather than exact listings")
    args = ap.parse_args()
    prices = sorted(int(x.strip()) for x in args.listings.split(",") if x.strip())
    if not prices:
        raise SystemExit("at least one positive listing price is required")
    now = datetime.now(UTC)
    observed_at = datetime.fromisoformat(args.observed_at.replace("Z", "+00:00")) if args.observed_at else now
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=UTC)
    confidence = calculate_manual_observation_confidence(
        observed_at=observed_at,
        received_at=now,
        listing_prices=prices,
        lowest_bin=prices[0],
        screenshot_present=False,
        approximate=args.approximate,
    )
    with SessionLocal() as session:
        card = session.get(Card, uuid.UUID(args.card_id))
        if not card:
            raise SystemExit("card not found")
        row = insert_execution_observation(
            session, card=card, source_key="manual_user", observed_at=observed_at,
            observation_type="manual_approximate" if args.approximate else "manual_values", lowest_bin=prices[0],
            listing_prices=prices, confidence=confidence.value, expires_at=now+timedelta(minutes=5),
        )
        session.commit()
        print(f"execution_observation_id={row.id} confidence={confidence.value:.3f} age_seconds={confidence.age_seconds:.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
