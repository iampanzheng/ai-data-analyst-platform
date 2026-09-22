# 06 FastAPI API Contract

## GET /health

Returns FastAPI/database readiness.

## GET /api/schema

Returns only application-allowlisted PostgreSQL tables together with physical column information and business metadata from `dataset_metadata` / `column_metadata`.

## POST /api/query

Request:

```json
{"sql":"SELECT name, population FROM city LIMIT 5"}
```

Successful response:

```json
{
  "columns": ["name", "population"],
  "rows": [["New York", 8584629]],
  "row_count": 1,
  "trace_id": "...",
  "execution_ms": 11.64
}
```

Validation failures return a structured error such as:

```json
{
  "detail": {
    "code": "TABLE_NOT_ALLOWED",
    "message": "Table not allowlisted: users",
    "trace_id": "..."
  }
}
```

## POST /api/analyze

Request:

```json
{"question":"人口最多的 5 个城市是哪几个？"}
```

Response shape:

```json
{
  "trace_id": "...",
  "question": "人口最多的 5 个城市是哪几个？",
  "sql_candidate": "SELECT ...",
  "validated_sql": "SELECT ...",
  "query_result": {
    "columns": ["name", "state", "population", "year"],
    "rows": [],
    "row_count": 0,
    "execution_ms": 0.0,
    "trace_id": "..."
  },
  "final_answer": "...",
  "model": "mock-analyst-v0.1",
  "provider": "mock",
  "usage": {},
  "errors": []
}
```

Generated SQL is validated through the same SQL security policy as `/api/query`; the Agent cannot bypass the validator.

## Gateway routes

The Spring Boot gateway exposes corresponding routes under `http://localhost:8080/api`:

```text
GET  /api/health
GET  /api/schema
POST /api/query
POST /api/analyze
```

## Future API work

Conversation/history, persisted evaluation runs, authentication, and richer report APIs are not part of the Phase 1 portfolio baseline.
