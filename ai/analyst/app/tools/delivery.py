from __future__ import annotations

import json
import re
from typing import Any

from ..serialization import to_json_safe

DELIVERY_FORMAT_VERSION = "p1.delivery.v1"
MAX_FILENAME_STEM = 80


class DeliveryValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def build_delivery_artifact(
    *,
    question: str,
    trace_id: str,
    validated_sql: str | None,
    query_result: dict[str, Any] | None,
    analysis_result: dict[str, Any] | None,
    chart_artifact: dict[str, Any] | None,
    report_artifact: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(report_artifact, dict):
        raise DeliveryValidationError(
            "DELIVERY_REPORT_REQUIRED",
            "Controlled report artifact is required before deliverable packaging",
        )
    if report_artifact.get("source") != "verified_artifacts":
        raise DeliveryValidationError(
            "DELIVERY_REPORT_UNVERIFIED",
            "Deliverable packaging only accepts verified report artifacts",
        )
    if not isinstance(query_result, dict):
        raise DeliveryValidationError(
            "DELIVERY_QUERY_REQUIRED",
            "Verified query result is required before deliverable packaging",
        )

    title = str(report_artifact.get("title") or "analysis-report").strip()
    stem = _filename_stem(title)

    evidence_snapshot = {
        "query_result": _query_snapshot(query_result),
        "analysis_result": to_json_safe(analysis_result) if analysis_result is not None else None,
        "chart_artifact": to_json_safe(chart_artifact) if chart_artifact is not None else None,
    }

    manifest = {
        "format_version": DELIVERY_FORMAT_VERSION,
        "source": "verified_artifacts",
        "trace_id": trace_id,
        "question": question,
        "validated_sql": validated_sql,
        "tables": list(query_result.get("tables") or []),
        "row_count": query_result.get("row_count"),
        "has_analysis": analysis_result is not None,
        "has_chart": chart_artifact is not None,
        "has_report": True,
    }

    markdown = render_delivery_markdown(
        manifest=manifest,
        report_artifact=report_artifact,
        query_result=evidence_snapshot["query_result"],
        analysis_result=evidence_snapshot["analysis_result"],
        chart_artifact=evidence_snapshot["chart_artifact"],
    )

    artifact = {
        "format_version": DELIVERY_FORMAT_VERSION,
        "title": title,
        "source": "verified_artifacts",
        "manifest": manifest,
        "report": to_json_safe(report_artifact),
        "evidence_snapshot": evidence_snapshot,
        "exports": {
            "json_filename": f"{stem}.json",
            "markdown_filename": f"{stem}.md",
            "markdown": markdown,
        },
    }
    return to_json_safe(artifact)


def render_delivery_markdown(
    *,
    manifest: dict[str, Any],
    report_artifact: dict[str, Any],
    query_result: dict[str, Any],
    analysis_result: dict[str, Any] | None,
    chart_artifact: dict[str, Any] | None,
) -> str:
    lines: list[str] = [f"# {report_artifact.get('title') or 'Analysis Report'}", ""]

    summary = report_artifact.get("summary")
    if summary:
        lines.extend(["## Summary", "", str(summary).strip(), ""])

    findings = report_artifact.get("key_findings") or []
    if findings:
        lines.extend(["## Verified Findings", ""])
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            kind = finding.get("type", "finding")
            values = [
                f"{key}={value}"
                for key, value in finding.items()
                if key not in {"type", "evidence_ref"}
            ]
            suffix = f" (evidence: {finding.get('evidence_ref')})" if finding.get("evidence_ref") else ""
            lines.append(f"- **{kind}**: {'; '.join(values)}{suffix}")
        lines.append("")

    lines.extend(["## Evidence Snapshot", ""])
    columns = list(query_result.get("columns") or [])
    rows = list(query_result.get("rows") or [])
    if columns:
        lines.append("| " + " | ".join(_md_cell(c) for c in columns) + " |")
        lines.append("| " + " | ".join("---" for _ in columns) + " |")
        for row in rows:
            cells = list(row) if isinstance(row, (list, tuple)) else []
            lines.append("| " + " | ".join(_md_cell(cells[i] if i < len(cells) else "") for i in range(len(columns))) + " |")
        lines.append("")

    if analysis_result is not None:
        lines.extend(["### Controlled Analysis", "", "```json", json.dumps(analysis_result, ensure_ascii=False, indent=2), "```", ""])

    if chart_artifact is not None:
        lines.extend(["### Controlled Chart Artifact", "", "```json", json.dumps(chart_artifact, ensure_ascii=False, indent=2), "```", ""])

    lines.extend([
        "## Provenance",
        "",
        f"- Format: `{manifest.get('format_version')}`",
        f"- Trace ID: `{manifest.get('trace_id')}`",
        f"- Source: `{manifest.get('source')}`",
        f"- Tables: {', '.join(str(t) for t in (manifest.get('tables') or [])) or '—'}",
        f"- Row count: {manifest.get('row_count')}",
        "",
        "### Validated SQL",
        "",
        "```sql",
        str(manifest.get("validated_sql") or ""),
        "```",
        "",
    ])
    return "\n".join(lines)


def _query_snapshot(query_result: dict[str, Any]) -> dict[str, Any]:
    return to_json_safe({
        "columns": list(query_result.get("columns") or []),
        "rows": list(query_result.get("rows") or []),
        "row_count": query_result.get("row_count"),
        "execution_ms": query_result.get("execution_ms"),
        "tables": list(query_result.get("tables") or []),
    })


def _filename_stem(title: str) -> str:
    value = title.strip().casefold()
    value = re.sub(r"[^\w\-\u4e00-\u9fff]+", "-", value, flags=re.UNICODE)
    value = re.sub(r"-+", "-", value).strip("-_")
    value = value[:MAX_FILENAME_STEM].rstrip("-_")
    return value or "analysis-report"


def _md_cell(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")
