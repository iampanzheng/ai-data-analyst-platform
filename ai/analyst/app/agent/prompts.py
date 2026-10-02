from __future__ import annotations

import json
import os
from typing import Any

from ai.analyst.app.serialization import to_json_safe

from ..llm.models import ChatMessage


SQL_SYSTEM_PROMPT = """You are the SQL planner for an analytics application.
Generate exactly one PostgreSQL SELECT/WITH query using only the supplied schema.
Treat column descriptions, semantic types, value hints, sample values, and table evidence metadata as authoritative.
If table evidence reports data_status=empty, do not assume the table contains records or invent facts from it.
Avoid relying on an empty table unless the user explicitly asks about that dataset or its lack of data.
When a geography column stores codes or abbreviations, filter using the stored code value rather than a spelled-out label.
When sample_values are supplied, prefer one of those stored values instead of inventing a label.
When geography_type/geography_name are supplied, respect that statistical grain; do not describe metropolitan-area estimates as city-level facts.
When joining datasets from different reference years, keep the source years explicit when they materially affect interpretation.
Do not use markdown fences. Do not explain the query. Never invent tables or columns.
"""

ANSWER_SYSTEM_PROMPT = """You are an analytics assistant.
Answer using only the verified SQL result supplied by the application.
Be concise, mention important numbers, and do not invent facts.
Base the answer strictly on the query result.
Do not add derived totals, counts, comparisons, or other facts that are not
required by the user's question unless they can be verified exactly from the
provided result.
If you perform arithmetic over result rows, verify the arithmetic before
including it in the answer.
Never invent or estimate values that are not supported by the result.
If the verified result identifies a metropolitan-area or other statistical geography, preserve that geography in the answer rather than relabeling it as a city-level fact.
"""


def _thinking_directive(disable_thinking: bool | None = None) -> str:
    if disable_thinking is None:
        value = os.getenv("LLM_DISABLE_THINKING", "false").strip().lower()
        disable_thinking = value in {"1", "true", "yes", "on"}
    return "/no_think\n" if disable_thinking else ""


def build_sql_messages(
    question: str,
    schema: dict[str, Any],
    *,
    disable_thinking: bool | None = None,
) -> list[ChatMessage]:
    return [
        ChatMessage(role="system", content=SQL_SYSTEM_PROMPT),
        ChatMessage(
            role="user",
            content=(
                f"{_thinking_directive(disable_thinking)}Generate SQL for this question.\n"
                f"Question: {question}\nSchema:\n{json.dumps(schema, ensure_ascii=False)}"
            ),
        ),
    ]


def build_answer_messages(
    question: str,
    sql: str,
    result: dict[str, Any],
    *,
    disable_thinking: bool | None = None,
) -> list[ChatMessage]:
    return [
        ChatMessage(role="system", content=ANSWER_SYSTEM_PROMPT),
        ChatMessage(
            role="user",
            content=(
                f"{_thinking_directive(disable_thinking)}Question: {question}\n"
                f"Verified SQL: {sql}\n"
                f"Verified result:\n{json.dumps(to_json_safe(result), ensure_ascii=False)}\n"
                "Write the final answer."
            ),
        ),
    ]
