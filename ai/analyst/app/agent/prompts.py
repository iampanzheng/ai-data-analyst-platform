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
For questions asking for descriptive statistics, correlation, or percent change, return the underlying rows and numeric columns needed for that calculation; do not calculate those statistics in SQL unless the requested result cannot be represented as row data. Preserve useful year/geography context columns when available so the final answer can describe the evidence correctly.
Do not use markdown fences. Do not explain the query. Never invent tables or columns.
"""


RAW_ANALYSIS_SQL_RETRY_SYSTEM_PROMPT = """You are repairing a SQL plan for a controlled analytics application.
The previous SQL was safe SQL, but it incorrectly computed a statistic that must be delegated to the controlled Python analysis runtime.
Generate exactly one PostgreSQL SELECT/WITH query that returns the underlying row-level numeric columns required for the requested controlled analysis.
Do not compute correlation, descriptive statistics, percent change, percentiles, averages, minima, maxima, counts, or other final statistical aggregates for that controlled analysis in SQL.
Preserve useful year and geography context columns when available.
Use only the supplied schema. Do not use markdown fences. Do not explain the query.
"""

ANALYSIS_SYSTEM_PROMPT = """You are the analysis planner for a controlled analytics runtime.
Return JSON only. Never return Python code.
Allowed operations are descriptive_stats, correlation, and percent_change.
Use only columns present in the verified SQL result.
A single descriptive_stats operation already returns count, min, max, mean, and median for its column; never create separate operations for those statistics.
Use one correlation operation for one pair of columns. Use one percent_change operation for one ordered numeric series.
If the verified SQL result already contains the final statistic(s) requested by the user and no additional controlled calculation is needed, return {"operations":[]}.
The exact schema is: {"operations":[{"operation":"descriptive_stats","column":"col"}]} or {"operations":[{"operation":"correlation","x":"col1","y":"col2"}]} or {"operations":[{"operation":"percent_change","column":"col"}]} or {"operations":[]}.
Do not include markdown or extra keys.
"""



CHART_SYSTEM_PROMPT = """You are the chart planner for a controlled analytics application.
Return JSON only. Never return JavaScript, Python, SQL, HTML, SVG, or plotting-library code.
Allowed chart types are bar, line, and scatter.
Use only columns present in the verified SQL result.
Choose bar for categorical comparisons/rankings, line for ordered time/progression, and scatter for relationships between two numeric variables.
The exact schema is {"chart_type":"bar|line|scatter","x":"column","y":"column","title":"short title"}.
Do not include markdown or extra keys.
"""

ANSWER_SYSTEM_PROMPT = """You are an analytics assistant.
Answer using only the verified SQL query result and controlled analysis result supplied by the application.
Be concise, mention important numbers, and do not invent facts.
Base the answer strictly on the supplied evidence. Controlled analysis values are application-computed evidence, not model-generated facts.
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



def build_analysis_messages(
    question: str,
    result: dict[str, Any],
    *,
    disable_thinking: bool | None = None,
) -> list[ChatMessage]:
    return [
        ChatMessage(role="system", content=ANALYSIS_SYSTEM_PROMPT),
        ChatMessage(
            role="user",
            content=(
                f"{_thinking_directive(disable_thinking)}Generate analysis plan for this question.\n"
                f"Question: {question}\n"
                f"Verified SQL result:\n{json.dumps(to_json_safe(result), ensure_ascii=False)}"
            ),
        ),
    ]


def build_raw_analysis_sql_retry_messages(
    question: str,
    schema: dict[str, Any],
    analysis_kind: str,
    previous_sql: str,
    *,
    disable_thinking: bool | None = None,
) -> list[ChatMessage]:
    return [
        ChatMessage(role="system", content=RAW_ANALYSIS_SQL_RETRY_SYSTEM_PROMPT),
        ChatMessage(
            role="user",
            content=(
                f"{_thinking_directive(disable_thinking)}Regenerate raw-row SQL for controlled analysis.\n"
                f"Controlled analysis kind: {analysis_kind}\n"
                f"Question: {question}\n"
                f"Previous SQL that precomputed the statistic: {previous_sql}\n"
                f"Schema:\n{json.dumps(schema, ensure_ascii=False)}"
            ),
        ),
    ]


def build_answer_messages(
    question: str,
    sql: str,
    result: dict[str, Any],
    analysis_result: dict[str, Any] | None = None,
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
                f"Controlled analysis result:\n{json.dumps(to_json_safe(analysis_result), ensure_ascii=False)}\n"
                "Write the final answer."
            ),
        ),
    ]


def build_chart_messages(
    question: str,
    result: dict[str, Any],
    analysis_result: dict[str, Any] | None = None,
    *,
    disable_thinking: bool | None = None,
) -> list[ChatMessage]:
    return [
        ChatMessage(role="system", content=CHART_SYSTEM_PROMPT),
        ChatMessage(
            role="user",
            content=(
                f"{_thinking_directive(disable_thinking)}Generate chart plan for this question.\n"
                f"Question: {question}\n"
                f"Verified SQL result:\n{json.dumps(to_json_safe(result), ensure_ascii=False)}\n"
                f"Controlled analysis result:\n{json.dumps(to_json_safe(analysis_result), ensure_ascii=False)}"
            ),
        ),
    ]
