from __future__ import annotations

import re

from .prompts import build_answer_messages, build_sql_messages
from .state import AnalystState
from ..llm.client import LLMClient, LLMClientError
from ..security import SQLValidationError, validate_sql
from ..tools.schema import get_database_schema
from ..tools.sql import execute_sql


_SQL_FENCE_RE = re.compile(r"^```(?:sql)?\s*|\s*```$", re.IGNORECASE)


class AnalystAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def run(self, question: str, trace_id: str) -> AnalystState:
        state = AnalystState(question=question, trace_id=trace_id)
        try:
            state.relevant_schema = get_database_schema()
            sql_response = self.llm.chat(
                build_sql_messages(
                    question,
                    state.relevant_schema,
                    disable_thinking=getattr(self.llm, "disable_thinking", False),
                )
            )
            state.model = sql_response.model
            state.provider = sql_response.provider
            state.usage = dict(sql_response.usage)
            sql = _normalize_sql(sql_response.content)
            state.sql_candidate = sql

            validated = validate_sql(sql)
            state.validated_sql = validated.normalized_sql
            state.query_result = execute_sql(validated.normalized_sql, trace_id)

            answer_response = self.llm.chat(
                build_answer_messages(
                    question,
                    validated.normalized_sql,
                    state.query_result,
                    disable_thinking=getattr(self.llm, "disable_thinking", False),
                )
            )
            state.final_answer = answer_response.content.strip()
            state.model = answer_response.model
            state.provider = answer_response.provider
            for key, value in answer_response.usage.items():
                state.usage[key] = state.usage.get(key, 0) + value
            return state
        except (LLMClientError, SQLValidationError) as exc:
            code = getattr(exc, "code", "LLM_ERROR")
            message = getattr(exc, "message", str(exc))
            state.errors.append({"code": code, "message": message})
            return state


def _normalize_sql(content: str) -> str:
    value = content.strip()
    value = _SQL_FENCE_RE.sub("", value).strip()
    return value
