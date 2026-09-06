from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter
from typing import Any

import httpx
import orjson

from fc27trader.collectors.base import Collector, RawObservation

PARSE_FUTBIN_SCRAPER_ID = "21963078-8a17-40ff-a896-9b0b0ec3e828"
DEFAULT_BASE_URL = f"https://api.parse.bot/scraper/{PARSE_FUTBIN_SCRAPER_ID}"
PARSER_VERSION = "parse-futbin-v1"
SCHEMA_VERSION = "1"


def _header_int(headers: httpx.Headers, *names: str) -> int | None:
    for name in names:
        value = headers.get(name)
        if value is None:
            continue
        try:
            return int(float(value))
        except (TypeError, ValueError):
            continue
    return None


class ParseBotFutbinError(RuntimeError):
    pass


class ParseBotFutbinRateLimit(ParseBotFutbinError):
    def __init__(self, message: str, *, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ParseBotFutbinCollector(Collector):
    """Optional authenticated collector for Parse.bot's documented FUTBIN wrapper.

    It consumes Parse's commercial REST API; it does not scrape FUTBIN directly.
    All returned prices are reference data, never execution truth.
    """

    key = "parse_futbin"

    def __init__(self, api_key: str, *, base_url: str = DEFAULT_BASE_URL, client: httpx.Client | None = None) -> None:
        if not api_key:
            raise ValueError("PARSE_API_KEY is required when Parse/FUTBIN is enabled")
        self._api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(
            timeout=20.0,
            follow_redirects=True,
            headers={
                "X-API-Key": api_key,
                "User-Agent": "fc27-top100-trading/0.2 private-research",
                "Accept": "application/json",
            },
        )

    def collect(self) -> list[RawObservation]:
        return self.collect_catalogue_page(1)

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> RawObservation:
        url = f"{self.base_url}/{endpoint}"
        started = perf_counter()
        try:
            response = self.client.get(url, params=params or {}, headers={"X-API-Key": self._api_key})
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise ParseBotFutbinError(f"Parse/FUTBIN request failed: {type(exc).__name__}") from exc
        latency_ms = (perf_counter() - started) * 1000.0
        if response.status_code == 429:
            retry_after = _header_int(response.headers, "retry-after")
            raise ParseBotFutbinRateLimit("Parse/FUTBIN rate limit reached", retry_after=retry_after)
        if response.status_code >= 400:
            # Do not include response/request headers in errors; they may contain the key.
            raise ParseBotFutbinError(f"Parse/FUTBIN HTTP {response.status_code} on {endpoint}")

        now = datetime.now(UTC)
        metadata = {
            "endpoint": endpoint,
            "parser_version": PARSER_VERSION,
            "schema_version": SCHEMA_VERSION,
            "latency_ms": latency_ms,
            "credits_used_header": _header_int(response.headers, "x-credits-used", "x-credit-used", "x-parse-credits-used"),
            "credits_remaining_header": _header_int(response.headers, "x-credits-remaining", "x-credit-remaining", "x-parse-credits-remaining"),
            "rate_limit_remaining": _header_int(response.headers, "x-ratelimit-remaining", "x-rate-limit-remaining"),
            "rate_limit_limit": _header_int(response.headers, "x-ratelimit-limit", "x-rate-limit-limit"),
            "reference_only": True,
            "upstream": "futbin",
            "provider_relationship": "independent_unofficial_wrapper",
        }
        return RawObservation(
            source_key=self.key,
            source_kind=f"parse_futbin_{endpoint}",
            url=str(response.request.url),
            observed_at=now,
            body=response.content,
            status_code=response.status_code,
            content_type=response.headers.get("content-type"),
            metadata=metadata,
        )

    def collect_catalogue_page(self, page: int = 1) -> list[RawObservation]:
        return [self._get("get_players", {"page": int(page), "fc26_only": "true"})]

    def collect_player_details(self, player_id: str | int) -> list[RawObservation]:
        return [self._get("get_player_details", {"player_id": str(player_id)})]

    def collect_market_trends(self) -> list[RawObservation]:
        return [self._get("get_market_trends")]

    def collect_sbcs(self, page: int = 1) -> list[RawObservation]:
        return [self._get("get_sbcs", {"page": int(page), "active_only": "true"})]

    def collect_evos(self) -> list[RawObservation]:
        return [self._get("get_evos")]

    def collect_objectives(self, page: int = 1) -> list[RawObservation]:
        return [self._get("get_objectives", {"page": int(page)})]


def parse_parse_payload(body: bytes) -> dict[str, Any]:
    payload = orjson.loads(body)
    if not isinstance(payload, dict):
        raise ValueError("Parse/FUTBIN response must be a JSON object")
    return payload
