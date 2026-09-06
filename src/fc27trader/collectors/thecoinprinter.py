from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter

import httpx

from .base import Collector, RawObservation


class TheCoinPrinterCollector(Collector):
    """Read-only approved-partner API adapter. Prices are reference-only."""

    key = "thecoinprinter"
    base_url = "https://api.thecoinprinter.com"

    def __init__(self, api_key: str, timeout_seconds: float = 20.0) -> None:
        if not api_key:
            raise ValueError("THECOINPRINTER_API_KEY is required")
        self.client = httpx.Client(
            timeout=timeout_seconds,
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        )

    def collect(self) -> list[RawObservation]:
        return self.search_recent(page=1, take=50)

    def search_recent(self, page: int = 1, take: int = 50) -> list[RawObservation]:
        return self.search(q=None, page=page, take=take)

    def search(self, q: str | None, page: int = 1, take: int = 50) -> list[RawObservation]:
        if take > 50:
            raise ValueError("The Coin Printer API maximum take is 50")
        url = f"{self.base_url}/api/v1/public/players/search"
        params = {"page": page, "take": take}
        if q is not None:
            if len(q) < 2:
                raise ValueError("q must be at least 2 characters")
            params["q"] = q
        started = perf_counter()
        response = self.client.get(url, params=params)
        latency_ms = (perf_counter() - started) * 1000.0
        response.raise_for_status()
        return [RawObservation(
            source_key=self.key,
            source_kind="thecoinprinter_player_search",
            url=str(response.url),
            observed_at=datetime.now(UTC),
            body=response.content,
            status_code=response.status_code,
            content_type=response.headers.get("content-type"),
            etag=response.headers.get("etag"),
            last_modified=response.headers.get("last-modified"),
            metadata={
                "latency_ms": latency_ms,
                "rate_limit_remaining": response.headers.get("x-ratelimit-remaining"),
                "rate_limit_reset": response.headers.get("x-ratelimit-reset"),
            },
        )]
