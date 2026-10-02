import math

import pytest

from ai.analyst.app.tools.python_analysis import (
    AnalysisValidationError,
    execute_analysis_plan,
    validate_analysis_plan,
)


def _result(columns, rows):
    return {"columns": columns, "rows": rows, "row_count": len(rows)}


def test_descriptive_stats():
    result = execute_analysis_plan(
        {"operations": [{"operation": "descriptive_stats", "column": "value"}]},
        _result(["value"], [[10], [20], [30]]),
    )
    op = result["operations"][0]
    assert op["count"] == 3
    assert op["min"] == 10.0
    assert op["max"] == 30.0
    assert op["mean"] == 20.0
    assert op["median"] == 20.0


def test_correlation():
    result = execute_analysis_plan(
        {"operations": [{"operation": "correlation", "x": "x", "y": "y"}]},
        _result(["x", "y"], [[1, 2], [2, 4], [3, 6]]),
    )
    assert math.isclose(result["operations"][0]["pearson_r"], 1.0)


def test_percent_change_preserves_row_order():
    result = execute_analysis_plan(
        {"operations": [{"operation": "percent_change", "column": "value"}]},
        _result(["value"], [[100], [120], [150]]),
    )
    op = result["operations"][0]
    assert op["first"] == 100.0
    assert op["last"] == 150.0
    assert op["percent_change"] == 50.0


def test_rejects_arbitrary_operation():
    with pytest.raises(AnalysisValidationError) as exc:
        validate_analysis_plan(
            {"operations": [{"operation": "python", "code": "import os"}]},
            ["value"],
        )
    assert exc.value.code == "ANALYSIS_OPERATION_NOT_ALLOWED"


def test_rejects_unknown_column():
    with pytest.raises(AnalysisValidationError) as exc:
        execute_analysis_plan(
            {"operations": [{"operation": "descriptive_stats", "column": "missing"}]},
            _result(["value"], [[1], [2]]),
        )
    assert exc.value.code == "ANALYSIS_COLUMN_NOT_FOUND"


def test_rejects_non_numeric_value():
    with pytest.raises(AnalysisValidationError) as exc:
        execute_analysis_plan(
            {"operations": [{"operation": "descriptive_stats", "column": "value"}]},
            _result(["value"], [[1], ["not-a-number"]]),
        )
    assert exc.value.code == "ANALYSIS_NON_NUMERIC_VALUE"


def test_rejects_extra_plan_keys():
    with pytest.raises(AnalysisValidationError) as exc:
        validate_analysis_plan(
            {"operations": [{"operation": "descriptive_stats", "column": "value"}], "code": "x"},
            ["value"],
        )
    assert exc.value.code == "ANALYSIS_PLAN_INVALID"


def test_allows_empty_plan_when_sql_already_has_final_statistics():
    assert validate_analysis_plan({"operations": []}, ["mean_salary"]) == []
    assert execute_analysis_plan(
        {"operations": []},
        _result(["mean_salary"], [[136693.44]]),
    ) == {"operations": []}
