from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnalystState:
    question: str
    intent: str | None = None
    relevant_schema: dict[str, Any] | None = None
    sql_candidate: str | None = None
    validated_sql: str | None = None
    query_result: dict[str, Any] | None = None
    analysis_result: dict[str, Any] | None = None
    chart_artifact: dict[str, Any] | None = None
    report_artifact: dict[str, Any] | None = None
    delivery_artifact: dict[str, Any] | None = None
    final_answer: str | None = None
    errors: list[dict[str, str]] = field(default_factory=list)
    trace_id: str = ""
    model: str | None = None
    provider: str | None = None
    usage: dict[str, int] = field(default_factory=dict)
