from __future__ import annotations

from dataclasses import dataclass
from time import sleep
from random import uniform

import httpx


@dataclass(slots=True)
class ConditionalState:
    etag: str | None = None
    last_modified: str | None = None


class PublicHttpClient:
    def __init__(self, timeout_seconds: float = 20.0, max_attempts: int = 3) -> None:
        self.client = httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=True,
            headers={
                "User-Agent": "fc27-top100-trading/0.1 (+personal research; contact owner if needed)",
                "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
            },
        )
        self.max_attempts = max_attempts

    def get(self, url: str, state: ConditionalState | None = None) -> httpx.Response:
        headers: dict[str, str] = {}
        if state and state.etag:
            headers["If-None-Match"] = state.etag
        if state and state.last_modified:
            headers["If-Modified-Since"] = state.last_modified

        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = self.client.get(url, headers=headers)
                if response.status_code not in (200, 304):
                    response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                if attempt == self.max_attempts:
                    break
                sleep(min(2 ** (attempt - 1), 8) + uniform(0.0, 0.35))

        assert last_error is not None
        raise last_error
