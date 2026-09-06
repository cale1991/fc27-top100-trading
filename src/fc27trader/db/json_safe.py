from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID


def to_json_safe(value: Any) -> Any:
    """Recursively normalize persistence metadata to JSON/JSONB-safe primitives.

    This is deliberately used only for JSON-ish metadata/state. Timestamp columns keep
    their native datetime values and are not passed through this helper.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        # String preserves exact decimal semantics across JSON encoders.
        return format(value, "f")
    if isinstance(value, Enum):
        return to_json_safe(value.value)
    if isinstance(value, (UUID, Path)):
        return str(value)
    if isinstance(value, dict):
        return {str(to_json_safe(key)): to_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json_safe(item) for item in value]
    if isinstance(value, (set, frozenset)):
        normalized = [to_json_safe(item) for item in value]
        try:
            return sorted(normalized, key=lambda item: repr(item))
        except TypeError:
            return normalized
    raise TypeError(f"Unsupported JSON metadata type: {type(value).__name__}")
