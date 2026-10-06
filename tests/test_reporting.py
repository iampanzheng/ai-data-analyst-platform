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
        final_answer="These figures come from official statistics and must not enter the verified report.",
    )

    assert artifact["summary"] == (
        "Verified SQL returned 2 rows from city, education with columns population, ratio. "
        "Controlled correlation analysis computed Pearson r=1.0 for population versus ratio using 2 numeric pairs. "
        "Controlled visualization produced a scatter chart with 2 points from verified query data."
    )
    assert artifact["summary_source"] == "deterministic_evidence"
    assert "official" not in artifact["summary"].lower()
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


def test_report_summary_does_not_copy_unverified_final_answer():
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
        final_answer="According to official government statistics, this is authoritative.",
    )
    assert artifact["summary"] == (
        "Verified SQL returned 2 rows from city, education with columns population, ratio."
    )
    assert artifact["summary_source"] == "deterministic_evidence"
    assert "official" not in artifact["summary"].lower()
    assert "government" not in artifact["summary"].lower()


def test_report_summary_uses_deterministic_chinese_template_for_chinese_title():
    artifact = execute_report_plan(
        {
            "title": "城市人口分析报告",
            "include_summary": True,
            "include_query_evidence": True,
            "analysis_operation_indexes": [],
            "include_chart": False,
        },
        query_result=_query_result(),
        analysis_result=None,
        chart_artifact=None,
        final_answer="以上数据来自官方统计。",
    )
    assert artifact["summary"].startswith("已验证 SQL 返回 2 行结果")
    assert "官方" not in artifact["summary"]
    assert artifact["summary_source"] == "deterministic_evidence"
