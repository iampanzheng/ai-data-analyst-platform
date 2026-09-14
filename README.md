# P1 — AI Data Analyst Platform

V1.1 Sprint 0 — Day 2: Schema/Metadata + SQL Validator.

## Current runtime path

```text
Public data
    ↓
data/raw
    ↓
ETL
    ↓
PostgreSQL
    ↓
GET /api/schema  ← physical schema + business metadata
    ↓
SQL Validator    ← independent policy gate
    ↓
POST /api/query
```

The deterministic query path is the foundation. The LLM will be added later and must use `/api/schema` to build schema-aware prompts, while the validator remains the independent execution gate.

## Run

```bash
cp .env.example .env
docker compose up --build
```

## Schema metadata

```bash
curl http://localhost:8000/api/schema
```

The endpoint exposes only allowlisted `public` tables and joins PostgreSQL `information_schema` with `dataset_metadata` and `column_metadata`.

## First safe query

```bash
curl -X POST http://localhost:8000/api/query \
  -H 'Content-Type: application/json' \
  -d '{"sql":"SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5"}'
```

## Validator examples

Allowed:

```sql
SELECT c.name, s.median_salary
FROM city c
JOIN salary s ON s.city_id = c.id
LIMIT 5;
```

Rejected:

```sql
DROP TABLE city;
```

```sql
SELECT * FROM users;
```

```sql
SELECT * FROM pg_catalog.pg_tables;
```

```sql
SELECT * FROM city; SELECT * FROM salary;
```

## Validation rules

- PostgreSQL SQL parsed with `sqlglot`
- one statement only
- SELECT / WITH SELECT only
- public schema only
- allowlisted physical tables only
- CTE-aware table extraction
- comments rejected
- SELECT INTO rejected
- row-locking reads rejected
- defensive forbidden-operation checks
- maximum SQL length
- read-only database transaction
- statement timeout
- result row cap
- structured validation error code + trace ID

## Day 2 exit criterion

A reviewer can inspect a stable schema metadata contract, see the same table policy used by the API and validator, submit a safe query, and observe unsafe SQL rejected.
