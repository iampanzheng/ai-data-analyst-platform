# Sprint 0 — Day 2

## Goal

Move SQL safety from the FastAPI route into a reusable validator and enforce a stable API error model.

## Implemented

- AST-based PostgreSQL SQL parsing with `sqlglot`
- single-statement enforcement
- SELECT / WITH SELECT only
- public-schema restriction
- physical table allowlist
- CTE-aware table extraction
- SQL comments rejected
- SELECT INTO rejected
- row-locking reads rejected
- defensive forbidden-operation checks
- maximum SQL length
- read-only PostgreSQL transaction
- statement timeout
- result row cap
- structured rejection codes and trace IDs
- validator unit tests

## Important boundary

The validator is a policy gate. Model-generated SQL is never trusted simply because it came from the LLM.

## Verification

Run:

```bash
pip install -r ai/analyst/requirements.txt
pytest -q tests/test_security.py
```

Then:

```bash
docker compose up --build
```

Safe query:

```bash
curl -X POST http://localhost:8000/api/query \
  -H 'Content-Type: application/json' \
  -d '{"sql":"SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5"}'
```

Unsafe query example:

```bash
curl -i -X POST http://localhost:8000/api/query \
  -H 'Content-Type: application/json' \
  -d '{"sql":"DROP TABLE city"}'
```

Expected error code:

```json
{
  "code": "STATEMENT_NOT_READ_ONLY"
}
```
