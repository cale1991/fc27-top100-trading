from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter

import httpx

from ..models import MarketQuote, ValidationCard
from .base import ValidationProvider


class TheCoinPrinterValidationProvider(ValidationProvider):
    key = "thecoinprinter"

    def __init__(self, api_key: str, timeout_seconds: float = 20.0) -> None:
        if not api_key:
            raise ValueError("THECOINPRINTER_API_KEY is required")
        self.client = httpx.Client(
            base_url="https://api.thecoinprinter.com",
            timeout=timeout_seconds,
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        )

    def fetch_quotes(self, cards: list[ValidationCard]) -> dict[str, MarketQuote]:
        out: dict[str, MarketQuote] = {}
        for card in cards:
            start_dt = datetime.now(UTC)
            t0 = perf_counter()
            response = self.client.get("/api/v1/public/players/search", params={"q": card.name, "page": 1, "take": 50})
            latency = (perf_counter() - t0) * 1000
            observed = datetime.now(UTC)
            response.raise_for_status()
            payload = response.json()
            candidates = payload.get("data", [])
            match = _choose_match(card, candidates)
            if match is None:
                out[card.key] = MarketQuote(
                    provider=self.key, card_key=card.key, price_pc=None, observed_at=observed,
                    request_started_at=start_dt, http_latency_ms=latency,
                    fields_available=list(candidates[0].keys()) if candidates else [],
                    raw_reference=str(response.url),
                )
                continue
            updated = match.get("updated_at")
            out[card.key] = MarketQuote(
                provider=self.key,
                card_key=card.key,
                price_pc=match.get("pc_price"),
                provider_timestamp=datetime.fromisoformat(updated.replace("Z", "+00:00")) if updated else None,
                observed_at=observed,
                request_started_at=start_dt,
                http_latency_ms=latency,
                source_card_id=str(match.get("id")) if match.get("id") else None,
                fields_available=list(match.keys()),
                raw_reference=str(response.url),
                metadata={"rating": match.get("rating"), "group_type": match.get("group_type")},
            )
        return out


def _choose_match(card: ValidationCard, candidates: list[dict]) -> dict | None:
    exact = [c for c in candidates if str(c.get("name", "")).casefold() == card.name.casefold()]
    if card.rating is not None:
        rated = [c for c in exact if c.get("rating") == card.rating]
        if rated:
            exact = rated
    wanted_group = card.version.casefold()
    group_matches = [
        c for c in exact if wanted_group in str(c.get("group_type", "")).casefold()
        or str(c.get("group_type", "")).casefold() in wanted_group
    ]
    return (group_matches or exact or candidates[:1] or [None])[0]
