from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


def to_json_safe(value: Any) -> Any:
    """
    Recursively convert common Python / DB values into JSON-safe values.

    Important:
    - Integral Decimal values become int.
    - Fractional Decimal values become float.
    - Containers are converted recursively.
    - Pydantic-like objects using model_dump() are supported.
    """

    if value is None:
        return None

    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)

        return float(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, dict):
        return {
            str(key): to_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            to_json_safe(item)
            for item in value
        ]

    model_dump = getattr(value, "model_dump", None)

    if callable(model_dump):
        return to_json_safe(model_dump())

    return value
