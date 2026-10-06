from acceptance.run import build_diagnostics, check_assertion, resolve_path


def test_resolve_path_nested_value():
    payload = {"query_result": {"row_count": 5}}
    assert resolve_path(payload, "query_result.row_count") == 5


def test_check_assertion_collection_field_contains():
    payload = {
        "analysis_result": {
            "operations": [
                {"operation": "descriptive_stats"},
                {"operation": "correlation"},
            ]
        }
    }
    assertion = {
        "path": "analysis_result.operations",
        "op": "collection_field_contains",
        "field": "operation",
        "value": "correlation",
    }
    assert check_assertion(payload, assertion) is None


def test_check_assertion_reports_missing_path():
    failure = check_assertion({}, {"path": "query_result.row_count", "op": "eq", "value": 5})
    assert failure == "query_result.row_count: path not found"


def test_check_assertion_length_eq():
    assert check_assertion({"errors": []}, {"path": "errors", "op": "length_eq", "value": 0}) is None


def test_build_diagnostics_limits_payload_to_execution_evidence():
    payload = {
        "trace_id": "abc",
        "validated_sql": "SELECT 1",
        "selected_route": "remote",
        "fallback_used": False,
        "errors": [{"code": "X"}],
        "query_result": {"row_count": 0, "tables": ["salary"], "columns": ["median_salary"], "rows": [[123]]},
        "final_answer": "untrusted prose",
    }
    diagnostics = build_diagnostics(payload)
    assert diagnostics["query_result"]["row_count"] == 0
    assert "rows" not in diagnostics["query_result"]
    assert "final_answer" not in diagnostics


def test_acceptance_manifest_targets_gateway_health_and_exact_salary_category():
    import json
    from pathlib import Path
    cases = json.loads(Path("acceptance/cases.json").read_text(encoding="utf-8"))["cases"]
    by_id = {case["id"]: case for case in cases}
    assert by_id["ACC-001"]["path"] == "/api/health"
    assert "Software Developers" in by_id["ACC-004"]["body"]["question"]
