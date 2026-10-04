from __future__ import annotations

import json
import re

from .prompts import (
    build_analysis_messages,
    build_answer_messages,
    build_chart_messages,
    build_raw_analysis_sql_retry_messages,
    build_report_messages,
    build_sql_messages,
)
from .state import AnalystState
from ..llm.client import LLMClient, LLMClientError
from ..security import SQLValidationError, validate_sql
from ..tools.schema import get_database_schema
from ..tools.sql import execute_sql
from ..tools.python_analysis import AnalysisValidationError, execute_analysis_plan
from ..tools.visualization import ChartValidationError, execute_chart_plan
from ..tools.reporting import ReportValidationError, execute_report_plan


_SQL_FENCE_RE = re.compile(r"^```(?:sql)?\s*|\s*```$", re.IGNORECASE)


_REPORT_KEYWORDS = ("report", "报告", "分析报告", "简报", "brief")


def _requires_report(question: str) -> bool:
    normalized = question.casefold()
    return any(keyword in normalized for keyword in _REPORT_KEYWORDS)


_VISUALIZATION_KEYWORDS = (
    "chart", "plot", "visualize", "visualization",
    "图表", "可视化", "柱状图", "条形图", "折线图", "散点图", "趋势图", "画图",
)


def _requires_visualization(question: str) -> bool:
    normalized = question.casefold()
    return any(keyword in normalized for keyword in _VISUALIZATION_KEYWORDS)


_ANALYSIS_KEYWORDS = (
    "correlation", "相关性", "相关系数", "pearson",
    "percent change", "percentage change", "变化率", "增长率", "增幅",
    "descriptive statistics", "descriptive stats", "描述统计",
)


def _controlled_analysis_kind(question: str) -> str | None:
    normalized = question.casefold()
    if any(keyword in normalized for keyword in ("correlation", "相关性", "相关系数", "pearson")):
        return "correlation"
    if any(keyword in normalized for keyword in ("percent change", "percentage change", "变化率", "增长率", "增幅")):
        return "percent_change"
    if any(keyword in normalized for keyword in ("descriptive statistics", "descriptive stats", "描述统计")):
        return "descriptive_stats"
    return None


def _requires_controlled_analysis(question: str) -> bool:
    return _controlled_analysis_kind(question) is not None


def _sql_precomputes_controlled_analysis(sql: str, analysis_kind: str | None) -> bool:
    if analysis_kind is None:
        return False
    normalized = sql.casefold()

    if analysis_kind == "correlation":
        return re.search(r"\bcorr\s*\(", normalized) is not None

    if analysis_kind == "descriptive_stats":
        return re.search(
            r"\b(min|max|avg|count|stddev|stddev_pop|stddev_samp|variance|var_pop|var_samp)\s*\("
            r"|\bpercentile_(cont|disc)\s*\(",
            normalized,
        ) is not None

    if analysis_kind == "percent_change":
        return re.search(
            r"\b(lag|lead|first_value|last_value)\s*\("
            r"|\b(percent_change|percentage_change|growth_rate)\b",
            normalized,
        ) is not None

    return False


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
            analysis_kind = _controlled_analysis_kind(question)
            if _sql_precomputes_controlled_analysis(validated.normalized_sql, analysis_kind):
                repair_response = self.llm.chat(
                    build_raw_analysis_sql_retry_messages(
                        question,
                        state.relevant_schema,
                        analysis_kind or "",
                        validated.normalized_sql,
                        disable_thinking=getattr(self.llm, "disable_thinking", False),
                    )
                )
                state.model = repair_response.model
                state.provider = repair_response.provider
                for key, value in repair_response.usage.items():
                    state.usage[key] = state.usage.get(key, 0) + value
                sql = _normalize_sql(repair_response.content)
                state.sql_candidate = sql
                validated = validate_sql(sql)
                if _sql_precomputes_controlled_analysis(validated.normalized_sql, analysis_kind):
                    raise AnalysisValidationError(
                        "ANALYSIS_SQL_PRECOMPUTED",
                        "SQL planner must return underlying rows for controlled analysis",
                    )

            state.validated_sql = validated.normalized_sql
            state.query_result = execute_sql(validated.normalized_sql, trace_id)

            if analysis_kind is not None:
                analysis_response = self.llm.chat(
                    build_analysis_messages(
                        question,
                        state.query_result,
                        disable_thinking=getattr(self.llm, "disable_thinking", False),
                    )
                )
                state.model = analysis_response.model
                state.provider = analysis_response.provider
                for key, value in analysis_response.usage.items():
                    state.usage[key] = state.usage.get(key, 0) + value
                try:
                    analysis_plan = json.loads(analysis_response.content.strip())
                except json.JSONDecodeError as exc:
                    raise AnalysisValidationError(
                        "ANALYSIS_PLAN_INVALID_JSON",
                        "Analysis planner returned invalid JSON",
                    ) from exc
                state.analysis_result = execute_analysis_plan(analysis_plan, state.query_result)

            if _requires_visualization(question):
                chart_response = self.llm.chat(
                    build_chart_messages(
                        question,
                        state.query_result,
                        state.analysis_result,
                        disable_thinking=getattr(self.llm, "disable_thinking", False),
                    )
                )
                state.model = chart_response.model
                state.provider = chart_response.provider
                for key, value in chart_response.usage.items():
                    state.usage[key] = state.usage.get(key, 0) + value
                try:
                    chart_plan = json.loads(chart_response.content.strip())
                except json.JSONDecodeError as exc:
                    raise ChartValidationError(
                        "CHART_PLAN_INVALID_JSON",
                        "Chart planner returned invalid JSON",
                    ) from exc
                state.chart_artifact = execute_chart_plan(chart_plan, state.query_result)

            answer_response = self.llm.chat(
                build_answer_messages(
                    question,
                    validated.normalized_sql,
                    state.query_result,
                    state.analysis_result,
                    disable_thinking=getattr(self.llm, "disable_thinking", False),
                )
            )
            state.final_answer = answer_response.content.strip()
            state.model = answer_response.model
            state.provider = answer_response.provider
            for key, value in answer_response.usage.items():
                state.usage[key] = state.usage.get(key, 0) + value

            if _requires_report(question):
                report_response = self.llm.chat(
                    build_report_messages(
                        question,
                        state.query_result,
                        state.analysis_result,
                        state.chart_artifact,
                        disable_thinking=getattr(self.llm, "disable_thinking", False),
                    )
                )
                state.model = report_response.model
                state.provider = report_response.provider
                for key, value in report_response.usage.items():
                    state.usage[key] = state.usage.get(key, 0) + value
                try:
                    report_plan = json.loads(report_response.content.strip())
                except json.JSONDecodeError as exc:
                    raise ReportValidationError(
                        "REPORT_PLAN_INVALID_JSON",
                        "Report planner returned invalid JSON",
                    ) from exc
                state.report_artifact = execute_report_plan(
                    report_plan,
                    query_result=state.query_result,
                    analysis_result=state.analysis_result,
                    chart_artifact=state.chart_artifact,
                    final_answer=state.final_answer,
                )
            return state
        except (LLMClientError, SQLValidationError, AnalysisValidationError, ChartValidationError, ReportValidationError) as exc:
            code = getattr(exc, "code", "LLM_ERROR")
            message = getattr(exc, "message", str(exc))
            state.errors.append({"code": code, "message": message})
            return state


def _normalize_sql(content: str) -> str:
    value = content.strip()
    value = _SQL_FENCE_RE.sub("", value).strip()
    return value
