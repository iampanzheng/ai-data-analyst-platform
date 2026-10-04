import pytest

from ai.analyst.app.tools.visualization import ChartValidationError, execute_chart_plan


def _result(columns, rows):
    return {"columns": columns, "rows": rows, "row_count": len(rows)}


def test_builds_bar_chart_from_verified_result():
    artifact = execute_chart_plan(
        {"chart_type": "bar", "x": "city", "y": "population", "title": "Population"},
        _result(["city", "population"], [["A", 10], ["B", 20]]),
    )
    assert artifact["chart_type"] == "bar"
    assert artifact["points"] == [{"x": "A", "y": 10.0}, {"x": "B", "y": 20.0}]
    assert artifact["source"] == "verified_query_result"


def test_builds_scatter_chart_with_numeric_strings():
    artifact = execute_chart_plan(
        {"chart_type": "scatter", "x": "population", "y": "ratio"},
        _result(["population", "ratio"], [[100, "42.5"], [200, "46.4"]]),
    )
    assert artifact["points"][0] == {"x": 100.0, "y": 42.5}


def test_rejects_unknown_chart_column():
    with pytest.raises(ChartValidationError) as exc:
        execute_chart_plan(
            {"chart_type": "bar", "x": "city", "y": "missing"},
            _result(["city", "population"], [["A", 10]]),
        )
    assert exc.value.code == "CHART_COLUMN_NOT_FOUND"


def test_rejects_non_numeric_y():
    with pytest.raises(ChartValidationError) as exc:
        execute_chart_plan(
            {"chart_type": "line", "x": "year", "y": "label"},
            _result(["year", "label"], [[2024, "high"]]),
        )
    assert exc.value.code == "CHART_NON_NUMERIC_Y"


def test_rejects_arbitrary_chart_code_or_extra_keys():
    with pytest.raises(ChartValidationError) as exc:
        execute_chart_plan(
            {"chart_type": "bar", "x": "city", "y": "population", "code": "alert(1)"},
            _result(["city", "population"], [["A", 10]]),
        )
    assert exc.value.code == "CHART_PLAN_INVALID"
