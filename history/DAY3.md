# Sprint 0 — Day 3

## Goal
Turn the Day 2 SQL safety layer into a regression-tested, observable foundation.

## Added
- Expanded SQL validator unit coverage.
- Real PostgreSQL integration tests.
- FastAPI schema/query integration tests.
- Client-supplied `X-Trace-ID` propagation with UUID fallback.
- JSON structured logging for SQL execution and request completion.
- Execution metrics: row count, SQL tables, execution time, total request time.

## Local unit tests
```bash
pip install -r ai/analyst/requirements.txt
pytest -m 'not integration'
```

## Integration tests
Start the stack first:
```bash
docker compose up --build -d
```
Then run tests inside the FastAPI container:
```bash
docker compose exec fastapi pytest -q
```

## Manual trace check
```bash
curl -X POST http://localhost:8000/api/query \
  -H 'Content-Type: application/json' \
  -H 'X-Trace-ID: demo-day3-001' \
  -d '{"sql":"SELECT name, population FROM city ORDER BY population DESC LIMIT 5"}'
```
The response `trace_id` must equal `demo-day3-001`, and container logs should contain the same trace id plus `execution_ms`.
