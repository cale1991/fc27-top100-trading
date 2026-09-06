from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import MarketQuote, ValidationCard


class ValidationProvider(ABC):
    key: str

    @abstractmethod
    def fetch_quotes(self, cards: list[ValidationCard]) -> dict[str, MarketQuote]:
        """Fetch PC quotes. Must not fabricate a provider timestamp when the upstream omits one."""
        raise NotImplementedError
