from __future__ import annotations

from typing import Any

from ..main import schema


def get_database_schema() -> dict[str, Any]:
    return schema().model_dump()
