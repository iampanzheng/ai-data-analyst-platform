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
        "summary": final_answer if validated.include_summary else None,
        "key_findings": key_findings,
        "evidence": evidence,
        "chart_refs": chart_refs,
        "source": "verified_artifacts",
    }


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
