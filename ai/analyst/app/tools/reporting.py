from __future__ import annotations

from dataclasses import dataclass
from typing import Any


MAX_REPORT_TITLE_LENGTH = 120
MAX_REPORT_ANALYSIS_REFS = 3


class ReportValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ReportPlan:
    title: str
    include_summary: bool
    include_query_evidence: bool
    analysis_operation_indexes: tuple[int, ...]
    include_chart: bool


def validate_report_plan(
    plan: Any,
    analysis_result: dict[str, Any] | None,
    chart_artifact: dict[str, Any] | None,
) -> ReportPlan:
    expected_keys = {
        "title",
        "include_summary",
        "include_query_evidence",
        "analysis_operation_indexes",
        "include_chart",
    }
    if not isinstance(plan, dict) or set(plan) != expected_keys:
        raise ReportValidationError(
            "REPORT_PLAN_INVALID",
            "Report plan must contain only the allowed report-planning fields",
        )

    title = plan.get("title")
    if not isinstance(title, str) or not title.strip() or len(title.strip()) > MAX_REPORT_TITLE_LENGTH:
        raise ReportValidationError(
            "REPORT_TITLE_INVALID",
            f"Report title must be 1-{MAX_REPORT_TITLE_LENGTH} characters",
        )

    include_summary = plan.get("include_summary")
    include_query_evidence = plan.get("include_query_evidence")
    include_chart = plan.get("include_chart")
    if not all(isinstance(value, bool) for value in (include_summary, include_query_evidence, include_chart)):
        raise ReportValidationError(
            "REPORT_PLAN_INVALID",
            "Report include flags must be booleans",
        )

    raw_indexes = plan.get("analysis_operation_indexes")
    if not isinstance(raw_indexes, list) or len(raw_indexes) > MAX_REPORT_ANALYSIS_REFS:
        raise ReportValidationError(
            "REPORT_PLAN_INVALID",
            f"analysis_operation_indexes must be an array of at most {MAX_REPORT_ANALYSIS_REFS} indexes",
        )
    if not all(isinstance(index, int) and not isinstance(index, bool) and index >= 0 for index in raw_indexes):
        raise ReportValidationError(
            "REPORT_ANALYSIS_REF_INVALID",
            "Analysis operation references must be non-negative integer indexes",
        )
    if len(set(raw_indexes)) != len(raw_indexes):
        raise ReportValidationError(
            "REPORT_ANALYSIS_REF_INVALID",
            "Analysis operation references must be unique",
        )

    operations = []
    if analysis_result is not None:
        operations = analysis_result.get("operations") or []
    if not isinstance(operations, list):
        raise ReportValidationError(
            "REPORT_INPUT_INVALID",
            "Controlled analysis result is invalid",
        )
    for index in raw_indexes:
        if index >= len(operations):
            raise ReportValidationError(
                "REPORT_ANALYSIS_REF_INVALID",
                f"Analysis operation reference does not exist: {index}",
            )

    if include_chart and chart_artifact is None:
        raise ReportValidationError(
            "REPORT_CHART_REF_INVALID",
            "Report plan requested a chart that is not available",
        )

    return ReportPlan(
        title=title.strip(),
        include_summary=include_summary,
        include_query_evidence=include_query_evidence,
        analysis_operation_indexes=tuple(raw_indexes),
        include_chart=include_chart,
    )


def execute_report_plan(
    plan: Any,
    *,
    query_result: dict[str, Any],
    analysis_result: dict[str, Any] | None,
    chart_artifact: dict[str, Any] | None,
    final_answer: str | None,
) -> dict[str, Any]:
    if not isinstance(query_result, dict):
        raise ReportValidationError("REPORT_INPUT_INVALID", "Verified SQL result is required")

    validated = validate_report_plan(plan, analysis_result, chart_artifact)
    operations = (analysis_result or {}).get("operations") or []

    evidence: list[dict[str, Any]] = []
    if validated.include_query_evidence:
        evidence.append(
            {
                "id": "query_result",
                "type": "query_result",
                "row_count": query_result.get("row_count"),
                "columns": list(query_result.get("columns") or []),
                "tables": list(query_result.get("tables") or []),
            }
        )

    key_findings: list[dict[str, Any]] = []
    for index in validated.analysis_operation_indexes:
        operation = operations[index]
        if not isinstance(operation, dict):
            raise ReportValidationError("REPORT_INPUT_INVALID", "Analysis operation is invalid")
        ref = f"analysis_result.operations[{index}]"
        evidence.append(
            {
                "id": ref,
                "type": "analysis_result",
                "operation_index": index,
                "operation": dict(operation),
            }
        )
        key_findings.append(_finding_from_operation(operation, ref))

    chart_refs: list[str] = []
    if validated.include_chart and chart_artifact is not None:
        chart_refs.append("chart_artifact")
        evidence.append(
            {
                "id": "chart_artifact",
                "type": "chart_artifact",
                "chart_type": chart_artifact.get("chart_type"),
                "title": chart_artifact.get("title"),
                "point_count": chart_artifact.get("point_count"),
                "source": chart_artifact.get("source"),
            }
        )

    return {
        "title": validated.title,
        "summary": _build_evidence_summary(
            query_result=query_result,
            selected_operations=[operations[index] for index in validated.analysis_operation_indexes],
            chart_artifact=chart_artifact if validated.include_chart else None,
            language_hint=validated.title,
        ) if validated.include_summary else None,
        "summary_source": "deterministic_evidence" if validated.include_summary else None,
        "key_findings": key_findings,
        "evidence": evidence,
        "chart_refs": chart_refs,
        "source": "verified_artifacts",
    }


def _build_evidence_summary(
    *,
    query_result: dict[str, Any],
    selected_operations: list[dict[str, Any]],
    chart_artifact: dict[str, Any] | None,
    language_hint: str,
) -> str:
    row_count = query_result.get("row_count")
    tables = [str(value) for value in (query_result.get("tables") or [])]
    columns = [str(value) for value in (query_result.get("columns") or [])]
    use_zh = any("\u4e00" <= char <= "\u9fff" for char in language_hint)

    parts: list[str] = []
    if use_zh:
        if isinstance(row_count, int) and row_count >= 0:
            base = f"已验证 SQL 返回 {row_count} 行结果"
        else:
            base = "已验证 SQL 返回结果集"
        if tables:
            base += f"，来源表为 {', '.join(tables)}"
        if columns:
            base += f"，包含列 {', '.join(columns)}"
        parts.append(base + "。")
    else:
        if isinstance(row_count, int) and row_count >= 0:
            base = f"Verified SQL returned {row_count} row{'s' if row_count != 1 else ''}"
        else:
            base = "Verified SQL returned a result set"
        if tables:
            base += f" from {', '.join(tables)}"
        if columns:
            base += f" with columns {', '.join(columns)}"
        parts.append(base + ".")

    for operation in selected_operations:
        kind = operation.get("operation")
        if kind == "correlation":
            if use_zh:
                parts.append(
                    "受控相关性分析计算得到 "
                    f"{operation.get('x')} 与 {operation.get('y')} 的 Pearson r={operation.get('pearson_r')}，"
                    f"使用 {operation.get('count')} 对数值样本。"
                )
            else:
                parts.append(
                    "Controlled correlation analysis computed "
                    f"Pearson r={operation.get('pearson_r')} for "
                    f"{operation.get('x')} versus {operation.get('y')} "
                    f"using {operation.get('count')} numeric pairs."
                )
        elif kind == "descriptive_stats":
            if use_zh:
                parts.append(
                    "受控描述统计计算得到 "
                    f"{operation.get('column')} 的 count={operation.get('count')}、min={operation.get('min')}、"
                    f"max={operation.get('max')}、mean={operation.get('mean')}、median={operation.get('median')}。"
                )
            else:
                parts.append(
                    "Controlled descriptive analysis computed "
                    f"count={operation.get('count')}, min={operation.get('min')}, "
                    f"max={operation.get('max')}, mean={operation.get('mean')}, "
                    f"median={operation.get('median')} for {operation.get('column')}."
                )
        elif kind == "percent_change":
            if use_zh:
                parts.append(
                    "受控百分比变化分析计算得到 "
                    f"{operation.get('column')} 从 {operation.get('first')} 到 {operation.get('last')} 的变化为 "
                    f"{operation.get('percent_change')}%。"
                )
            else:
                parts.append(
                    "Controlled percent-change analysis computed "
                    f"{operation.get('percent_change')}% for {operation.get('column')} "
                    f"from {operation.get('first')} to {operation.get('last')}."
                )

    if chart_artifact is not None:
        if use_zh:
            parts.append(
                "受控可视化根据已验证查询数据生成 "
                f"{chart_artifact.get('chart_type')} 图，共 {chart_artifact.get('point_count')} 个数据点。"
            )
        else:
            parts.append(
                "Controlled visualization produced a "
                f"{chart_artifact.get('chart_type')} chart with "
                f"{chart_artifact.get('point_count')} points from verified query data."
            )

    return " ".join(parts)


def _finding_from_operation(operation: dict[str, Any], evidence_ref: str) -> dict[str, Any]:
    kind = operation.get("operation")
    if kind == "correlation":
        return {
            "type": "correlation",
            "x": operation.get("x"),
            "y": operation.get("y"),
            "count": operation.get("count"),
            "pearson_r": operation.get("pearson_r"),
            "evidence_ref": evidence_ref,
        }
    if kind == "descriptive_stats":
        return {
            "type": "descriptive_stats",
            "column": operation.get("column"),
            "count": operation.get("count"),
            "min": operation.get("min"),
            "max": operation.get("max"),
            "mean": operation.get("mean"),
            "median": operation.get("median"),
            "evidence_ref": evidence_ref,
        }
    if kind == "percent_change":
        return {
            "type": "percent_change",
            "column": operation.get("column"),
            "first": operation.get("first"),
            "last": operation.get("last"),
            "percent_change": operation.get("percent_change"),
            "evidence_ref": evidence_ref,
        }
    raise ReportValidationError(
        "REPORT_ANALYSIS_OPERATION_UNSUPPORTED",
        f"Unsupported controlled analysis operation in report: {kind}",
    )
