from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter

import httpx

from .base import Collector, RawObservation


class FutDbNoQuotaError(RuntimeError):
    def __init__(self, *, retry_after: int | None = None):
        super().__init__("FUT-DB quota is zero")
        self.retry_after = retry_after


class FutDbCollector(Collector):
    """Documented FUT-DB JSON API adapter for FC26.

    Player universe/metadata works with an API key. Price endpoints are premium.
    All price output is REFERENCE/HISTORICAL only, never executable market data.
    """

    key = "futdb"
    base_url = "https://api.fut-db.com/api"

    def __init__(self, api_key: str, timeout_seconds: float = 30.0) -> None:
        if not api_key:
            raise ValueError("FUTDB_API_KEY is required")
        self.client = httpx.Client(
            timeout=timeout_seconds,
            headers={"X-AUTH-TOKEN": api_key, "Accept": "application/json"},
        )

    def collect(self) -> list[RawObservation]:
        return self.collect_players(page=1)

    def _get(self, url: str, *, kind: str) -> RawObservation:
        started = perf_counter()
        response = self.client.get(url)
        latency_ms = (perf_counter() - started) * 1000.0
        if response.status_code == 429:
            limit = response.headers.get("x-ratelimit-limit")
            remaining = response.headers.get("x-ratelimit-remaining")
            if str(limit) == "0" or str(remaining) == "0":
                retry = response.headers.get("retry-after")
                raise FutDbNoQuotaError(retry_after=int(retry) if retry and retry.isdigit() else None)
        response.raise_for_status()
        return self._obs(url, response, kind, latency_ms)

    def collect_players(self, page: int = 1) -> list[RawObservation]:
        url = f"{self.base_url}/players?page={page}"
        return [self._get(url, kind="futdb_players")]

    def collect_entity_page(self, entity_type: str, page: int = 1) -> list[RawObservation]:
        endpoint = {"club": "clubs", "league": "leagues", "nation": "nations", "rarity": "rarities"}.get(entity_type)
        if endpoint is None:
            raise ValueError(f"unsupported FUT-DB entity type: {entity_type}")
        url = f"{self.base_url}/{endpoint}?page={page}"
        return [self._get(url, kind=f"futdb_{entity_type}s")]

    def collect_player_price(self, player_id: int | str) -> list[RawObservation]:
        url = f"{self.base_url}/players/{player_id}/price"
        return [self._get(url, kind="futdb_player_price")]

    def _obs(self, url: str, response: httpx.Response, kind: str, latency_ms: float) -> RawObservation:
        return RawObservation(
            source_key=self.key,
            source_kind=kind,
            url=url,
            observed_at=datetime.now(UTC),
            body=response.content,
            status_code=response.status_code,
            content_type=response.headers.get("content-type"),
            etag=response.headers.get("etag"),
            last_modified=response.headers.get("last-modified"),
            metadata={
                "latency_ms": latency_ms,
                "rate_limit_limit": response.headers.get("x-ratelimit-limit"),
                "rate_limit_remaining": response.headers.get("x-ratelimit-remaining"),
                "retry_after": response.headers.get("retry-after"),
                "rate_limit_reset": response.headers.get("x-ratelimit-reset"),
            },
        )
