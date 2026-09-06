from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter

import httpx

from ..models import MarketQuote, ValidationCard
from .base import ValidationProvider


class FutNextValidationProvider(ValidationProvider):
    """Technical validator for FUTNext's FC Enhancer price surface.

    This adapter is intentionally validation-only. The endpoint is not a documented public API;
    production use must remain disabled until FUTNext grants permission/API terms.
    """

    key = "futnext"

    def __init__(self, timeout_seconds: float = 20.0, batch_size: int = 50) -> None:
        self.client = httpx.Client(base_url="https://enhancer-api.futnext.com", timeout=timeout_seconds)
        self.batch_size = batch_size

    def fetch_quotes(self, cards: list[ValidationCard]) -> dict[str, MarketQuote]:
        out: dict[str, MarketQuote] = {}
        resolved = [c for c in cards if c.ea_definition_id is not None]
        for i in range(0, len(resolved), self.batch_size):
            batch = resolved[i : i + self.batch_size]
            ids = "_".join(str(c.ea_definition_id) for c in batch)
            started = datetime.now(UTC)
            t0 = perf_counter()
            response = self.client.get("/players/prices", params={"ids": ids, "platform": "pc"})
            latency = (perf_counter() - t0) * 1000
            observed = datetime.now(UTC)
            response.raise_for_status()
            payload = response.json()
            by_id = {int(row["definitionId"]): row for row in payload if row.get("definitionId") is not None}
            for card in batch:
                row = by_id.get(card.ea_definition_id)
                price = None
                if row and row.get("prices"):
                    price = row["prices"][0]
                out[card.key] = MarketQuote(
                    provider=self.key,
                    card_key=card.key,
                    price_pc=int(price) if price is not None else None,
                    # Upstream response observed publicly does not expose an authoritative data timestamp.
                    provider_timestamp=None,
                    observed_at=observed,
                    request_started_at=started,
                    http_latency_ms=latency,
                    source_card_id=str(card.ea_definition_id),
                    fields_available=list(row.keys()) if row else [],
                    raw_reference=str(response.url),
                )
        return out
