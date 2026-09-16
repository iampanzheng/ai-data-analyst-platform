from __future__ import annotations

from typing import Any

from ..main import execute_query


def execute_sql(sql: str, trace_id: str) -> dict[str, Any]:
    columns, rows, execution_ms, tables = execute_query(sql, trace_id)
    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "execution_ms": execution_ms,
        "tables": sorted(tables),
    }
