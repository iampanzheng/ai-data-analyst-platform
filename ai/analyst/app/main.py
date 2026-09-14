import os
import time
import uuid
from contextlib import contextmanager

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="P1 AI Data Analyst — Day 1")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://analyst:analyst@postgres:5432/ai_analyst")
MAX_ROWS = int(os.getenv("SQL_MAX_ROWS", "1000"))
STATEMENT_TIMEOUT_MS = int(os.getenv("SQL_STATEMENT_TIMEOUT_MS", "3000"))
ALLOWED_TABLES = {"city", "employment", "salary", "education", "economic_indicator", "dataset_metadata", "column_metadata"}
DENIED = ("insert ", "update ", "delete ", "drop ", "alter ", "truncate ", "create ", "grant ", "revoke ")

class QueryRequest(BaseModel):
    sql: str = Field(min_length=1)


def validate_sql(sql: str) -> str:
    q = sql.strip().lower()
    if not (q.startswith("select ") or q.startswith("with ")):
        raise HTTPException(400, "Only SELECT/WITH statements are allowed")
    if ";" in q.rstrip(";"):
        raise HTTPException(400, "Multiple SQL statements are not allowed")
    if any(token in q for token in DENIED):
        raise HTTPException(400, "Unsafe SQL statement")
    # Day 1 allowlist: reject explicit references to non-project tables.
    import re
    refs = re.findall(r"\b(?:from|join)\s+([a-z_][a-z0-9_]*)", q)
    unknown = sorted(set(refs) - ALLOWED_TABLES)
    if unknown:
        raise HTTPException(400, f"Table not allowlisted: {unknown[0]}")
    return sql.strip().rstrip(";")


@contextmanager
def connection():
    with psycopg.connect(DATABASE_URL) as conn:
        yield conn


def execute(sql: str):
    sql = validate_sql(sql)
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL statement_timeout = {STATEMENT_TIMEOUT_MS}")
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(sql)
            columns = [d.name for d in cur.description] if cur.description else []
            rows = cur.fetchmany(MAX_ROWS)
            return columns, [dict(zip(columns, row)) for row in rows]


@app.get("/health")
def health():
    with connection() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


@app.get("/api/schema")
def schema():
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema='public' AND table_name = ANY(%s)
                ORDER BY table_name, ordinal_position
            """, (list(ALLOWED_TABLES),))
            return {"tables": [dict(zip(["table_name", "column_name", "data_type"], r)) for r in cur.fetchall()]}


@app.post("/api/query")
def query(req: QueryRequest):
    trace_id = str(uuid.uuid4())
    started = time.perf_counter()
    columns, rows = execute(req.sql)
    return {
        "trace_id": trace_id,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "execution_ms": round((time.perf_counter() - started) * 1000, 2),
    }
