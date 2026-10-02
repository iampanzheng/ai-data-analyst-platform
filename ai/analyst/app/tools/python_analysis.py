from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Any


MAX_ANALYSIS_ROWS = 1000
MAX_ANALYSIS_OPERATIONS = 3
_ALLOWED_OPERATIONS = {"descriptive_stats", "correlation", "percent_change"}


class AnalysisValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class AnalysisOperation:
    operation: str
    column: str | None = None
    x: str | None = None
    y: str | None = None


def validate_analysis_plan(plan: Any, available_columns: list[str]) -> list[AnalysisOperation]:
    if not isinstance(plan, dict) or set(plan) != {"operations"}:
        raise AnalysisValidationError(
            "ANALYSIS_PLAN_INVALID",
            "Analysis plan must contain only an operations array",
        )
    raw_operations = plan.get("operations")
    if not isinstance(raw_operations, list):
        raise AnalysisValidationError(
            "ANALYSIS_PLAN_INVALID",
            "Analysis plan operations must be an array",
        )
    if len(raw_operations) > MAX_ANALYSIS_OPERATIONS:
        raise AnalysisValidationError(
            "ANALYSIS_PLAN_TOO_LARGE",
            f"Analysis plan may contain at most {MAX_ANALYSIS_OPERATIONS} operations",
        )

    columns = set(available_columns)
    operations: list[AnalysisOperation] = []
    for raw in raw_operations:
        if not isinstance(raw, dict):
            raise AnalysisValidationError("ANALYSIS_PLAN_INVALID", "Each operation must be an object")
        operation = raw.get("operation")
        if operation not in _ALLOWED_OPERATIONS:
            raise AnalysisValidationError(
                "ANALYSIS_OPERATION_NOT_ALLOWED",
                f"Analysis operation is not allowed: {operation}",
            )

        if operation in {"descriptive_stats", "percent_change"}:
            if set(raw) != {"operation", "column"}:
                raise AnalysisValidationError(
                    "ANALYSIS_PLAN_INVALID",
                    f"{operation} accepts only operation and column",
                )
            column = raw.get("column")
            if not isinstance(column, str) or column not in columns:
                raise AnalysisValidationError(
                    "ANALYSIS_COLUMN_NOT_FOUND",
                    f"Analysis column is not present in SQL result: {column}",
                )
            operations.append(AnalysisOperation(operation=operation, column=column))
            continue

        if set(raw) != {"operation", "x", "y"}:
            raise AnalysisValidationError(
                "ANALYSIS_PLAN_INVALID",
                "correlation accepts only operation, x, and y",
            )
        x = raw.get("x")
        y = raw.get("y")
        if not isinstance(x, str) or x not in columns or not isinstance(y, str) or y not in columns:
            raise AnalysisValidationError(
                "ANALYSIS_COLUMN_NOT_FOUND",
                "Correlation columns must both be present in the SQL result",
            )
        operations.append(AnalysisOperation(operation=operation, x=x, y=y))

    return operations


def execute_analysis_plan(plan: Any, query_result: dict[str, Any]) -> dict[str, Any]:
    columns = query_result.get("columns")
    rows = query_result.get("rows")
    if not isinstance(columns, list) or not all(isinstance(c, str) for c in columns):
        raise AnalysisValidationError("ANALYSIS_INPUT_INVALID", "SQL result columns are invalid")
    if not isinstance(rows, list):
        raise AnalysisValidationError("ANALYSIS_INPUT_INVALID", "SQL result rows are invalid")
    if len(rows) > MAX_ANALYSIS_ROWS:
        raise AnalysisValidationError(
            "ANALYSIS_INPUT_TOO_LARGE",
            f"Controlled analysis accepts at most {MAX_ANALYSIS_ROWS} rows",
        )

    operations = validate_analysis_plan(plan, columns)
    index = {name: i for i, name in enumerate(columns)}
    results: list[dict[str, Any]] = []

    for operation in operations:
        if operation.operation == "descriptive_stats":
            values = _numeric_column(rows, index[operation.column], operation.column)
            if not values:
                raise AnalysisValidationError("ANALYSIS_NO_NUMERIC_DATA", f"No numeric data for {operation.column}")
            results.append(
                {
                    "operation": "descriptive_stats",
                    "column": operation.column,
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": statistics.fmean(values),
                    "median": statistics.median(values),
                }
            )
        elif operation.operation == "correlation":
            pairs = _numeric_pairs(rows, index[operation.x], index[operation.y], operation.x, operation.y)
            if len(pairs) < 2:
                raise AnalysisValidationError("ANALYSIS_INSUFFICIENT_DATA", "Correlation needs at least two numeric pairs")
            xs = [p[0] for p in pairs]
            ys = [p[1] for p in pairs]
            if len(set(xs)) < 2 or len(set(ys)) < 2:
                raise AnalysisValidationError("ANALYSIS_CONSTANT_COLUMN", "Correlation requires non-constant columns")
            results.append(
                {
                    "operation": "correlation",
                    "x": operation.x,
                    "y": operation.y,
                    "count": len(pairs),
                    "pearson_r": statistics.correlation(xs, ys),
                }
            )
        else:
            values = _numeric_column(rows, index[operation.column], operation.column)
            if len(values) < 2:
                raise AnalysisValidationError("ANALYSIS_INSUFFICIENT_DATA", "Percent change needs at least two numeric values")
            first, last = values[0], values[-1]
            if first == 0:
                raise AnalysisValidationError("ANALYSIS_DIVIDE_BY_ZERO", "Percent change cannot use zero as the first value")
            results.append(
                {
                    "operation": "percent_change",
                    "column": operation.column,
                    "first": first,
                    "last": last,
                    "percent_change": ((last - first) / first) * 100.0,
                }
            )

    return {"operations": results}


def _to_number(value: Any, column: str) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        numeric = float(value)
    else:
        try:
            numeric = float(str(value))
        except (TypeError, ValueError) as exc:
            raise AnalysisValidationError(
                "ANALYSIS_NON_NUMERIC_VALUE",
                f"Column contains a non-numeric value: {column}",
            ) from exc
    if not math.isfinite(numeric):
        raise AnalysisValidationError("ANALYSIS_NON_FINITE_VALUE", f"Column contains NaN or Infinity: {column}")
    return numeric


def _numeric_column(rows: list[Any], idx: int, column: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        if not isinstance(row, (list, tuple)) or idx >= len(row):
            raise AnalysisValidationError("ANALYSIS_INPUT_INVALID", "SQL result row does not match columns")
        value = _to_number(row[idx], column)
        if value is not None:
            values.append(value)
    return values


def _numeric_pairs(
    rows: list[Any], x_idx: int, y_idx: int, x_name: str, y_name: str
) -> list[tuple[float, float]]:
    pairs: list[tuple[float, float]] = []
    for row in rows:
        if not isinstance(row, (list, tuple)) or max(x_idx, y_idx) >= len(row):
            raise AnalysisValidationError("ANALYSIS_INPUT_INVALID", "SQL result row does not match columns")
        x = _to_number(row[x_idx], x_name)
        y = _to_number(row[y_idx], y_name)
        if x is not None and y is not None:
            pairs.append((x, y))
    return pairs
