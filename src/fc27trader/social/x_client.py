from __future__ import annotations

import httpx


class XPostingClient:
    """Official X API v2 posting adapter. Requires a user-authorized access token."""

    def __init__(self, user_access_token: str, base_url: str = "https://api.x.com/2", timeout_seconds: float = 20.0):
        if not user_access_token:
            raise ValueError("X user access token is required")
        self.client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {user_access_token}", "Content-Type": "application/json"},
            timeout=timeout_seconds,
        )

    def post(self, text: str) -> dict:
        response = self.client.post("/tweets", json={"text": text})
        response.raise_for_status()
        return response.json()
