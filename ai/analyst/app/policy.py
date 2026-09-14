from __future__ import annotations

ALLOWED_SCHEMA = "public"
ALLOWED_TABLES = frozenset(
    {
        "city",
        "employment",
        "salary",
        "education",
        "economic_indicator",
    }
)
