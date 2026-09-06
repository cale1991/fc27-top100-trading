from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class RawObservation:
    source_key: str
    source_kind: str
    url: str
    observed_at: datetime
    body: bytes
    status_code: int = 200
    content_type: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    source_timestamp: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Collector(ABC):
    key: str

    @abstractmethod
    def collect(self) -> list[RawObservation]:
        raise NotImplementedError
