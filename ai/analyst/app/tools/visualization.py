from __future__ import annotations

import math
from decimal import Decimal
from typing import Any


ALLOWED_CHART_TYPES = frozenset({"bar", "line", "scatter"})
MAX_CHART_POINTS = 100
MAX_TITLE_LENGTH = 120


class ChartValidationError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _numeric(value: Any) -> float:
    if isinstance(value, bool) or value is None:
        raise ValueError
    if isinstance(value, (int, float, Decimal)):
        number = float(value)
    elif isinstance(value, str):
        try:
            number = float(value.strip())
        except ValueError as exc:
            raise ValueError from exc
    else:
        raise ValueError
    if not math.isfinite(number):
        raise ValueError
    return number


def _validate_plan_shape(plan: Any) -> dict[str, Any]:
    if not isinstance(plan, dict):
        raise ChartValidationError("CHART_PLAN_INVALID", "Chart plan must be a JSON object")

    allowed_keys = {"chart_type", "x", "y", "title"}
    extra = set(plan) - allowed_keys
    required = {"chart_type", "x", "y"}
    missing = required - set(plan)
    if extra or missing:
        raise ChartValidationError(
            "CHART_PLAN_INVALID",
            "Chart plan must contain only chart_type, x, y, and optional title",
        )

    chart_type = plan.get("chart_type")
    x = plan.get("x")
    y = plan.get("y")
    title = plan.get("title", "")

    if chart_type not in ALLOWED_CHART_TYPES:
        raise ChartValidationError(
            "CHART_TYPE_NOT_ALLOWED",
            f"Chart type must be one of: {', '.join(sorted(ALLOWED_CHART_TYPES))}",
        )
    if not isinstance(x, str) or not x.strip() or not isinstance(y, str) or not y.strip():
        raise ChartValidationError("CHART_PLAN_INVALID", "Chart x and y must be non-empty column names")
    if not isinstance(title, str):
        raise ChartValidationError("CHART_PLAN_INVALID", "Chart title must be a string")
    if len(title) > MAX_TITLE_LENGTH:
        raise ChartValidationError("CHART_TITLE_TOO_LONG", "Chart title is too long")

    return {"chart_type": chart_type, "x": x, "y": y, "title": title.strip()}


def execute_chart_plan(plan: Any, query_result: dict[str, Any]) -> dict[str, Any]:
    validated = _validate_plan_shape(plan)
    columns = query_result.get("columns")
    rows = query_result.get("rows")
    if not isinstance(columns, list) or not all(isinstance(column, str) for column in columns):
        raise ChartValidationError("CHART_RESULT_INVALID", "Verified SQL result has invalid columns")
    if not isinstance(rows, list):
        raise ChartValidationError("CHART_RESULT_INVALID", "Verified SQL result has invalid rows")
    if len(rows) == 0:
        raise ChartValidationError("CHART_RESULT_EMPTY", "Cannot build a chart from an empty SQL result")
    if len(rows) > MAX_CHART_POINTS:
        raise ChartValidationError(
            "CHART_TOO_MANY_POINTS",
            f"Chart input exceeds the {MAX_CHART_POINTS}-point limit; narrow the SQL result first",
        )

    try:
        x_index = columns.index(validated["x"])
        y_index = columns.index(validated["y"])
    except ValueError as exc:
        raise ChartValidationError(
            "CHART_COLUMN_NOT_FOUND",
            "Chart columns must exist in the verified SQL result",
        ) from exc

    points: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) != len(columns):
            raise ChartValidationError("CHART_RESULT_INVALID", "Verified SQL result contains an invalid row")
        raw_x = row[x_index]
        raw_y = row[y_index]
        try:
            y_value = _numeric(raw_y)
        except ValueError as exc:
            raise ChartValidationError(
                "CHART_NON_NUMERIC_Y",
                f"Chart y column '{validated['y']}' must contain finite numeric values",
            ) from exc

        if validated["chart_type"] == "scatter":
            try:
                x_value: Any = _numeric(raw_x)
            except ValueError as exc:
                raise ChartValidationError(
                    "CHART_NON_NUMERIC_X",
                    f"Scatter x column '{validated['x']}' must contain finite numeric values",
                ) from exc
        else:
            if raw_x is None:
                raise ChartValidationError("CHART_NULL_X", "Chart x values cannot be null")
            if isinstance(raw_x, Decimal):
                x_value = float(raw_x)
            elif isinstance(raw_x, (str, int, float)) and not isinstance(raw_x, bool):
                x_value = raw_x
            else:
                x_value = str(raw_x)

        points.append({"x": x_value, "y": y_value})

    return {
        "chart_type": validated["chart_type"],
        "title": validated["title"] or f"{validated['y']} by {validated['x']}",
        "x": {"column": validated["x"]},
        "y": {"column": validated["y"]},
        "points": points,
        "point_count": len(points),
        "source": "verified_query_result",
    }
