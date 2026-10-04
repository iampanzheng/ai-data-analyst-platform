import pytest

from ai.analyst.app.tools.reporting import ReportValidationError, execute_report_plan


def _query_result():
    return {
        "columns": ["population", "ratio"],
        "rows": [[100, 10], [200, 20]],
        "row_count": 2,
        "tables": ["city", "education"],
    }


def test_report_binds_only_verified_artifacts():
    artifact = execute_report_plan(
        {
            "title": "Population and education report",
            "include_summary": True,
            "include_query_evidence": True,
            "analysis_operation_indexes": [0],
            "include_chart": True,
        },
        query_result=_query_result(),
        analysis_result={"operations": [{"operation": "correlation", "x": "population", "y": "ratio", "count": 2, "pearson_r": 1.0}]},
        chart_artifact={"chart_type": "scatter", "title": "Relationship", "point_count": 2, "source": "verified_query_result"},
        final_answer="The verified correlation is 1.0.",
    )

    assert artifact["summary"] == "The verified correlation is 1.0."
    assert artifact["key_findings"] == [{
        "type": "correlation",
        "x": "population",
        "y": "ratio",
        "count": 2,
        "pearson_r": 1.0,
        "evidence_ref": "analysis_result.operations[0]",
    }]
    assert [item["id"] for item in artifact["evidence"]] == [
        "query_result", "analysis_result.operations[0]", "chart_artifact"
    ]
    assert artifact["source"] == "verified_artifacts"


def test_report_rejects_unknown_analysis_reference():
    with pytest.raises(ReportValidationError) as exc:
        execute_report_plan(
            {
                "title": "Report",
                "include_summary": True,
                "include_query_evidence": True,
                "analysis_operation_indexes": [1],
                "include_chart": False,
            },
            query_result=_query_result(),
            analysis_result={"operations": [{"operation": "correlation"}]},
            chart_artifact=None,
            final_answer="Answer",
        )
    assert exc.value.code == "REPORT_ANALYSIS_REF_INVALID"


def test_report_rejects_missing_chart_reference():
    with pytest.raises(ReportValidationError) as exc:
        execute_report_plan(
            {
                "title": "Report",
                "include_summary": True,
                "include_query_evidence": True,
                "analysis_operation_indexes": [],
                "include_chart": True,
            },
            query_result=_query_result(),
            analysis_result=None,
            chart_artifact=None,
            final_answer="Answer",
        )
    assert exc.value.code == "REPORT_CHART_REF_INVALID"


def test_report_rejects_extra_keys_and_freeform_payload():
    with pytest.raises(ReportValidationError) as exc:
        execute_report_plan(
            {
                "title": "Report",
                "include_summary": True,
                "include_query_evidence": True,
                "analysis_operation_indexes": [],
                "include_chart": False,
                "html": "<script>alert(1)</script>",
            },
            query_result=_query_result(),
            analysis_result=None,
            chart_artifact=None,
            final_answer="Answer",
        )
    assert exc.value.code == "REPORT_PLAN_INVALID"


def test_report_can_exist_without_analysis_or_chart():
    artifact = execute_report_plan(
        {
            "title": "Population report",
            "include_summary": True,
            "include_query_evidence": True,
            "analysis_operation_indexes": [],
            "include_chart": False,
        },
        query_result=_query_result(),
        analysis_result=None,
        chart_artifact=None,
        final_answer="Population summary.",
    )
    assert artifact["key_findings"] == []
    assert artifact["chart_refs"] == []
    assert artifact["evidence"][0]["type"] == "query_result"
