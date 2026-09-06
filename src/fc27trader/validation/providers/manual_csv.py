from __future__ import annotations

from pathlib import Path

from ..io import load_provider_quotes_csv
from ..models import MarketQuote, ValidationCard
from .base import ValidationProvider


class ManualCsvValidationProvider(ValidationProvider):
    def __init__(self, key: str, csv_path: str | Path) -> None:
        self.key = key
        self.csv_path = Path(csv_path)

    def fetch_quotes(self, cards: list[ValidationCard]) -> dict[str, MarketQuote]:
        quotes = load_provider_quotes_csv(self.csv_path, self.key)
        keys = {c.key for c in cards}
        return {k: v for k, v in quotes.items() if k in keys}
