from __future__ import annotations

import json
import os
from typing import Any

from ai.analyst.app.serialization import to_json_safe

from ..llm.models import ChatMessage


SQL_SYSTEM_PROMPT = """You are the SQL planner for an analytics application.
Generate exactly one PostgreSQL SELECT/WITH query using only the supplied schema.
Treat column descriptions, semantic types, value hints, and sample values as authoritative value semantics.
When a geography column stores codes or abbreviations, filter using the stored code value rather than a spelled-out label.
When sample_values are supplied, prefer one of those stored values instead of inventing a label.
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
"""


def _thinking_directive() -> str:
    value = os.getenv("LLM_DISABLE_THINKING", "false").strip().lower()
    return "/no_think\n" if value in {"1", "true", "yes", "on"} else ""


def build_sql_messages(question: str, schema: dict[str, Any]) -> list[ChatMessage]:
    return [
        ChatMessage(role="system", content=SQL_SYSTEM_PROMPT),
        ChatMessage(
            role="user",
            content=(
                f"{_thinking_directive()}Generate SQL for this question.\n"
                f"Question: {question}\nSchema:\n{json.dumps(schema, ensure_ascii=False)}"
            ),
        ),
    ]


def build_answer_messages(question: str, sql: str, result: dict[str, Any]) -> list[ChatMessage]:
    return [
        ChatMessage(role="system", content=ANSWER_SYSTEM_PROMPT),
        ChatMessage(
            role="user",
            content=(
                f"{_thinking_directive()}Question: {question}\n"
                f"Verified SQL: {sql}\n"
                f"Verified result:\n{json.dumps(to_json_safe(result), ensure_ascii=False)}\n"
                "Write the final answer."
            ),
        ),
    ]
