from __future__ import annotations

import os
import time
import uuid
from contextlib import contextmanager
from typing import Any, Iterator, Literal

import psycopg
from psycopg import sql as psycopg_sql
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
    TableEvidence,
    TableMetadata,
)
from .policy import ALLOWED_SCHEMA, ALLOWED_TABLES
from .security import SQLValidationError, validate_sql

import logging


class AnalyzeRequest(BaseModel):
    question: str = Field(min_length=1)
    routing_mode: Literal["auto", "remote", "local"] = "auto"
    fallback_mode: Literal["auto", "disabled", "cross_route"] = "auto"


class AnalyzeResponse(BaseModel):
    trace_id: str
    question: str
    routing_mode: str
    selected_route: str | None
    final_route: str | None
    routing_reason: str | None
    fallback_mode: str
    fallback_route: str | None
    fallback_used: bool
    fallback_events: list[dict[str, str]]
    route_usage: dict[str, dict[str, int]]
    estimated_cost_usd: float
    sql_candidate: str | None
    validated_sql: str | None
    query_result: dict[str, Any] | None
    analysis_result: dict[str, Any] | None
    chart_artifact: dict[str, Any] | None
    final_answer: str | None
    model: str | None
    provider: str | None
    usage: dict[str, int]
    errors: list[dict[str, str]]


configure_logging()
logger = logging.getLogger("ai.analyst.api")
app = FastAPI(title="P1 AI Data Analyst Platform")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://analyst:analyst@postgres:5432/ai_analyst")
MAX_ROWS = int(os.getenv("SQL_MAX_ROWS", "1000"))
STATEMENT_TIMEOUT_MS = int(os.getenv("SQL_STATEMENT_TIMEOUT_MS", "3000"))
VALUE_GROUNDING_MAX_VALUES = int(os.getenv("VALUE_GROUNDING_MAX_VALUES", "20"))
VALUE_GROUNDING_SEMANTIC_TYPES = {"geography_code"}
VALUE_GROUNDING_COLUMNS = {("city", "state"), ("education", "education_level")}


def _is_value_grounded(table_name: str, column_name: str, semantic_type: str) -> bool:
    return (table_name, column_name) in VALUE_GROUNDING_COLUMNS or semantic_type in VALUE_GROUNDING_SEMANTIC_TYPES


def _value_hint(table_name: str, column_name: str, semantic_type: str) -> str:
    if (table_name, column_name) == ("city", "state") or semantic_type == "geography_code":
        return (
            "Stored values are two-letter U.S. postal abbreviations. Map natural-language state "
            "names or common aliases to the stored code before filtering; for example "
            "California/加州 -> CA, Texas/德州 -> TX, New York/纽约州 -> NY."
        )
    if (table_name, column_name) == ("education", "education_level"):
        return (
            "Categorical label. When filtering, use an exact stored sample value rather than "
            "paraphrasing or shortening the category name."
        )
    return ""

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

        resolved_semantic_type = semantic_type or "unknown"
        grouped[table_name].columns.append(
            ColumnMetadata(
                name=column_name,
                business_name=business_name or column_name,
                description=column_description or "",
                data_type=data_type,
                semantic_type=resolved_semantic_type,
                nullable=is_nullable == "YES",
                queryable=True,
                value_hint=_value_hint(table_name, column_name, resolved_semantic_type),
            )
        )

    # Add deterministic table evidence plus bounded value grounding. Identifiers originate
    # from allowlisted schema introspection and are quoted defensively.
    with connection() as conn:
        with conn.cursor() as cur:
            for table in grouped.values():
                column_names = {column.name for column in table.columns}
                aggregate_parts = [psycopg_sql.SQL("COUNT(*)")]
                if "year" in column_names:
                    aggregate_parts.extend(
                        [
                            psycopg_sql.SQL("MIN({year})").format(
                                year=psycopg_sql.Identifier("year")
                            ),
                            psycopg_sql.SQL("MAX({year})").format(
                                year=psycopg_sql.Identifier("year")
                            ),
                        ]
                    )

                cur.execute(
                    psycopg_sql.SQL(
                        "SELECT {aggregates} FROM {schema}.{table}"
                    ).format(
                        aggregates=psycopg_sql.SQL(", ").join(aggregate_parts),
                        schema=psycopg_sql.Identifier(ALLOWED_SCHEMA),
                        table=psycopg_sql.Identifier(table.table_name),
                    )
                )
                evidence_row = cur.fetchone()
                row_count = int(evidence_row[0])
                min_year = (
                    int(evidence_row[1])
                    if len(evidence_row) > 1 and evidence_row[1] is not None
                    else None
                )
                max_year = (
                    int(evidence_row[2])
                    if len(evidence_row) > 2 and evidence_row[2] is not None
                    else None
                )

                if row_count == 0:
                    data_status = "empty"
                    evidence_note = "No rows are currently loaded for this dataset."
                elif min_year is not None and max_year is not None:
                    year_text = (
                        str(min_year)
                        if min_year == max_year
                        else f"{min_year}-{max_year}"
                    )
                    data_status = "available"
                    evidence_note = (
                        f"{row_count} rows are currently loaded for year range {year_text}."
                    )
                else:
                    data_status = "available"
                    evidence_note = (
                        f"{row_count} rows are currently loaded for this dataset."
                    )

                table.evidence = TableEvidence(
                    row_count=row_count,
                    data_status=data_status,
                    min_year=min_year,
                    max_year=max_year,
                    evidence_note=evidence_note,
                )

                for column in table.columns:
                    if not _is_value_grounded(
                        table.table_name, column.name, column.semantic_type
                    ):
                        continue
                    cur.execute(
                        psycopg_sql.SQL(
                            "SELECT DISTINCT {column} FROM {schema}.{table} "
                            "WHERE {column} IS NOT NULL ORDER BY {column} LIMIT %s"
                        ).format(
                            column=psycopg_sql.Identifier(column.name),
                            schema=psycopg_sql.Identifier(ALLOWED_SCHEMA),
                            table=psycopg_sql.Identifier(table.table_name),
                        ),
                        (VALUE_GROUNDING_MAX_VALUES,),
                    )
                    column.sample_values = [str(row[0]) for row in cur.fetchall()]

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
    from .llm.client import LLMClientError
    from .llm.routing import create_routed_llm_client

    try:
        decision, llm = create_routed_llm_client(req.routing_mode, fallback_mode=req.fallback_mode)
    except LLMClientError as exc:
        return AnalyzeResponse(
            trace_id=trace_id,
            question=req.question,
            routing_mode=req.routing_mode,
            selected_route=None,
            final_route=None,
            routing_reason=None,
            fallback_mode=req.fallback_mode,
            fallback_route=None,
            fallback_used=False,
            fallback_events=[],
            route_usage={},
            estimated_cost_usd=0.0,
            sql_candidate=None,
            validated_sql=None,
            query_result=None,
            analysis_result=None,
            chart_artifact=None,
            final_answer=None,
            model=None,
            provider=None,
            usage={},
            errors=[{"code": exc.code, "message": exc.message}],
        )

    logger.info(
        "llm_route_selected",
        extra={"fields": {
            "trace_id": trace_id,
            "event": "llm_route_selected",
            "routing_mode": req.routing_mode,
            "selected_route": decision.selected_route,
            "routing_reason": decision.reason,
            "fallback_mode": req.fallback_mode,
            "fallback_route": decision.fallback_route,
        }},
    )
    state = AnalystAgent(llm).run(req.question, trace_id)
    fallback_events = list(getattr(llm, "fallback_events", []))
    route_usage = dict(getattr(llm, "route_usage", {}))
    estimated_cost_usd = float(getattr(llm, "estimated_cost_usd", 0.0))
    if fallback_events:
        logger.warning(
            "llm_fallback_used",
            extra={"fields": {
                "trace_id": trace_id,
                "event": "llm_fallback_used",
                "fallback_events": fallback_events,
                "estimated_cost_usd": estimated_cost_usd,
            }},
        )
    return AnalyzeResponse(
        trace_id=trace_id,
        question=state.question,
        routing_mode=req.routing_mode,
        selected_route=decision.selected_route,
        final_route=str(getattr(llm, "current_route", decision.selected_route)),
        routing_reason=decision.reason,
        fallback_mode=req.fallback_mode,
        fallback_route=decision.fallback_route,
        fallback_used=bool(fallback_events),
        fallback_events=fallback_events,
        route_usage=route_usage,
        estimated_cost_usd=round(estimated_cost_usd, 8),
        sql_candidate=state.sql_candidate,
        validated_sql=state.validated_sql,
        query_result=state.query_result,
        analysis_result=state.analysis_result,
        chart_artifact=state.chart_artifact,
        final_answer=state.final_answer,
        model=state.model,
        provider=state.provider,
        usage=state.usage,
        errors=state.errors,
    )
