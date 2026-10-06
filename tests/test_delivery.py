import pytest

from ai.analyst.app.tools.delivery import (
    DELIVERY_FORMAT_VERSION,
    DeliveryValidationError,
    build_delivery_artifact,
)


def _query_result():
    return {
        "columns": ["city", "population"],
        "rows": [["New York", 8584629], ["Los Angeles", 3869089]],
        "row_count": 2,
        "execution_ms": 3.2,
        "tables": ["city"],
    }


def _report():
    return {
        "title": "2025 City Population Report",
        "summary": "Verified city population results.",
        "key_findings": [],
        "evidence": [{"id": "query_result", "type": "query_result"}],
        "chart_refs": [],
        "source": "verified_artifacts",
    }


def test_delivery_packages_only_verified_artifacts():
    artifact = build_delivery_artifact(
        question="Generate a report",
        trace_id="trace-001",
        validated_sql="SELECT city, population FROM city",
        query_result=_query_result(),
        analysis_result=None,
        chart_artifact=None,
        report_artifact=_report(),
    )

    assert artifact["format_version"] == DELIVERY_FORMAT_VERSION
    assert artifact["source"] == "verified_artifacts"
    assert artifact["manifest"]["trace_id"] == "trace-001"
    assert artifact["manifest"]["row_count"] == 2
    assert artifact["evidence_snapshot"]["query_result"]["rows"][0] == ["New York", 8584629]
    assert artifact["exports"]["json_filename"].endswith(".json")
    assert artifact["exports"]["markdown_filename"].endswith(".md")
    assert "## Evidence Snapshot" in artifact["exports"]["markdown"]
    assert "```sql" in artifact["exports"]["markdown"]


def test_delivery_includes_analysis_and_chart_snapshots():
    analysis = {"operations": [{"operation": "correlation", "x": "x", "y": "y", "count": 2, "pearson_r": 1.0}]}
    chart = {"chart_type": "scatter", "title": "Relationship", "x": {"column": "x"}, "y": {"column": "y"}, "points": [{"x": 1, "y": 2}], "point_count": 1, "source": "verified_query_result"}
    report = _report() | {"chart_refs": ["chart_artifact"]}

    artifact = build_delivery_artifact(
        question="Generate report and chart",
        trace_id="trace-002",
        validated_sql="SELECT x, y FROM city",
        query_result=_query_result(),
        analysis_result=analysis,
        chart_artifact=chart,
        report_artifact=report,
    )

    assert artifact["manifest"]["has_analysis"] is True
    assert artifact["manifest"]["has_chart"] is True
    assert artifact["evidence_snapshot"]["analysis_result"] == analysis
    assert artifact["evidence_snapshot"]["chart_artifact"] == chart


def test_delivery_rejects_missing_report():
    with pytest.raises(DeliveryValidationError) as exc:
        build_delivery_artifact(
            question="q",
            trace_id="t",
            validated_sql="SELECT 1",
            query_result=_query_result(),
            analysis_result=None,
            chart_artifact=None,
            report_artifact=None,
        )
    assert exc.value.code == "DELIVERY_REPORT_REQUIRED"


def test_delivery_rejects_unverified_report():
    with pytest.raises(DeliveryValidationError) as exc:
        build_delivery_artifact(
            question="q",
            trace_id="t",
            validated_sql="SELECT 1",
            query_result=_query_result(),
            analysis_result=None,
            chart_artifact=None,
            report_artifact=_report() | {"source": "llm_freeform"},
        )
    assert exc.value.code == "DELIVERY_REPORT_UNVERIFIED"


def test_markdown_escapes_table_pipe():
    query = _query_result()
    query["rows"] = [["A|B", 10]]
    query["row_count"] = 1
    artifact = build_delivery_artifact(
        question="q",
        trace_id="t",
        validated_sql="SELECT city, population FROM city",
        query_result=query,
        analysis_result=None,
        chart_artifact=None,
        report_artifact=_report(),
    )
    assert "A\\|B" in artifact["exports"]["markdown"]


def test_delivery_markdown_preserves_evidence_bound_summary_only():
    report = _report() | {
        "summary": "Verified SQL returned 2 rows from city with columns city, population.",
        "summary_source": "deterministic_evidence",
    }
    artifact = build_delivery_artifact(
        question="Generate report",
        trace_id="trace-003",
        validated_sql="SELECT city, population FROM city",
        query_result=_query_result(),
        analysis_result=None,
        chart_artifact=None,
        report_artifact=report,
    )
    assert artifact["report"]["summary_source"] == "deterministic_evidence"
    assert "Verified SQL returned 2 rows" in artifact["exports"]["markdown"]
    assert "official government" not in artifact["exports"]["markdown"].lower()
