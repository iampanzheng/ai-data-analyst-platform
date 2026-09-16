from __future__ import annotations

import os
import time
import uuid
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from .logging_config import configure_logging
from .telemetry import get_or_create_trace_id, request_timing

from .models import (
    ColumnMetadata,
    ErrorResponse,
    QueryRequest,
    QueryResponse,
    SchemaResponse,
    TableMetadata,
)
from .policy import ALLOWED_SCHEMA, ALLOWED_TABLES
from .security import SQLValidationError, validate_sql

import logging


class AnalyzeRequest(BaseModel):
    question: str = Field(min_length=1)


class AnalyzeResponse(BaseModel):
    trace_id: str
    question: str
    sql_candidate: str | None
    validated_sql: str | None
    query_result: dict[str, Any] | None
    final_answer: str | None
    model: str | None
    usage: dict[str, int]
    errors: list[dict[str, str]]


configure_logging()
logger = logging.getLogger("ai.analyst.api")
app = FastAPI(title="P1 AI Data Analyst — Day 5")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://analyst:analyst@postgres:5432/ai_analyst")
MAX_ROWS = int(os.getenv("SQL_MAX_ROWS", "1000"))
STATEMENT_TIMEOUT_MS = int(os.getenv("SQL_STATEMENT_TIMEOUT_MS", "3000"))

@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    with psycopg.connect(DATABASE_URL) as conn:
        yield conn


def execute_query(sql: str, trace_id: str) -> tuple[list[str], list[list[Any]], float, frozenset[str]]:
    validated = validate_sql(sql)
    started = time.perf_counter()
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL statement_timeout = {STATEMENT_TIMEOUT_MS}")
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(validated.normalized_sql)
            columns = [desc.name for desc in (cur.description or [])]
            rows = [list(row) for row in cur.fetchmany(MAX_ROWS)]
    elapsed_ms = request_timing(started)
    logger.info(
        "sql_execution",
        extra={"fields": {
            "trace_id": trace_id,
            "event": "sql_execution",
            "tables": sorted(validated.tables),
            "row_count": len(rows),
            "execution_ms": elapsed_ms,
        }},
    )
    return columns, rows, elapsed_ms, validated.tables


def error_response(code: str, message: str, trace_id: str, status_code: int) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "trace_id": trace_id},
    )


@app.get("/health")
def health() -> dict[str, str]:
    try:
        with connection() as conn:
            conn.execute("SELECT 1")
    except psycopg.Error as exc:
        raise error_response(
            "DATABASE_UNAVAILABLE", "Database is unavailable", str(uuid.uuid4()), 503
        ) from exc
    return {"status": "ok"}


@app.get("/api/schema", response_model=SchemaResponse)
def schema() -> SchemaResponse:
    """Expose only allowlisted physical tables plus business metadata."""
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    c.table_name,
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    d.dataset_name,
                    d.description,
                    d.source,
                    d.update_frequency,
                    cm.business_name,
                    cm.description AS column_description,
                    cm.semantic_type
                FROM information_schema.columns AS c
                LEFT JOIN dataset_metadata AS d
                    ON d.dataset_name = c.table_name
                LEFT JOIN column_metadata AS cm
                    ON cm.dataset_id = d.id
                   AND cm.column_name = c.column_name
                WHERE c.table_schema = %s
                  AND c.table_name = ANY(%s)
                ORDER BY c.table_name, c.ordinal_position
                """,
                (ALLOWED_SCHEMA, list(ALLOWED_TABLES)),
            )
            rows = cur.fetchall()

    grouped: dict[str, TableMetadata] = {}
    for row in rows:
        (
            table_name,
            column_name,
            data_type,
            is_nullable,
            dataset_name,
            description,
            source,
            update_frequency,
            business_name,
            column_description,
            semantic_type,
        ) = row

        if table_name not in grouped:
            grouped[table_name] = TableMetadata(
                table_name=table_name,
                business_name=dataset_name or table_name,
                description=description or "",
                source=source or "",
                update_frequency=update_frequency,
                columns=[],
            )

        grouped[table_name].columns.append(
            ColumnMetadata(
                name=column_name,
                business_name=business_name or column_name,
                description=column_description or "",
                data_type=data_type,
                semantic_type=semantic_type or "unknown",
                nullable=is_nullable == "YES",
                queryable=True,
            )
        )

    return SchemaResponse(schema_name=ALLOWED_SCHEMA, tables=list(grouped.values()))


@app.post(
    "/api/query",
    response_model=QueryResponse,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def query(req: QueryRequest, request: Request) -> QueryResponse:
    trace_id = get_or_create_trace_id(request)
    started = time.perf_counter()
    try:
        columns, rows, execution_ms, _tables = execute_query(req.sql, trace_id)
    except SQLValidationError as exc:
        raise error_response(exc.code, exc.message, trace_id, 400) from exc
    except psycopg.errors.QueryCanceled as exc:
        raise error_response(
            "STATEMENT_TIMEOUT",
            "SQL execution exceeded the configured timeout",
            trace_id,
            409,
        ) from exc
    except psycopg.Error as exc:
        raise error_response("DATABASE_QUERY_ERROR", "Database query failed", trace_id, 500) from exc

    logger.info(
        "request_complete",
        extra={"fields": {
            "trace_id": trace_id,
            "event": "request_complete",
            "path": "/api/query",
            "total_execution_ms": request_timing(started),
            "row_count": len(rows),
        }},
    )

    return QueryResponse(
        trace_id=trace_id,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        execution_ms=execution_ms,
    )


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest, request: Request) -> AnalyzeResponse:
    trace_id = get_or_create_trace_id(request)
    from .agent.graph import AnalystAgent
    from .llm.client import create_llm_client

    state = AnalystAgent(create_llm_client()).run(req.question, trace_id)
    return AnalyzeResponse(
        trace_id=trace_id,
        question=state.question,
        sql_candidate=state.sql_candidate,
        validated_sql=state.validated_sql,
        query_result=state.query_result,
        final_answer=state.final_answer,
        model=state.model,
        usage=state.usage,
        errors=state.errors,
    )
