from __future__ import annotations

import json
from typing import Any

from ..llm.models import ChatMessage


SQL_SYSTEM_PROMPT = """You are the SQL planner for an analytics application.
Generate exactly one PostgreSQL SELECT/WITH query using only the supplied schema.
Do not use markdown fences. Do not explain the query. Never invent tables or columns.
"""

ANSWER_SYSTEM_PROMPT = """You are an analytics assistant.
Answer using only the verified SQL result supplied by the application.
Be concise, mention important numbers, and do not invent facts.
"""


def build_sql_messages(question: str, schema: dict[str, Any]) -> list[ChatMessage]:
    return [
        ChatMessage(role="system", content=SQL_SYSTEM_PROMPT),
        ChatMessage(
            role="user",
            content=f"Generate SQL for this question.\nQuestion: {question}\nSchema:\n{json.dumps(schema, ensure_ascii=False)}",
        ),
    ]


def build_answer_messages(question: str, sql: str, result: dict[str, Any]) -> list[ChatMessage]:
    return [
        ChatMessage(role="system", content=ANSWER_SYSTEM_PROMPT),
        ChatMessage(
            role="user",
            content=(
                f"Question: {question}\n"
                f"Verified SQL: {sql}\n"
                f"Verified result:\n{json.dumps(result, ensure_ascii=False)}\n"
                "Write the final answer."
            ),
        ),
    ]
