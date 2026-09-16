# Day 4 Fix 1 — Gateway JSON request body

## Symptom
`POST /api/query` through Spring Boot returned FastAPI validation error:
`Field required` at `body`, while direct FastAPI calls succeeded.

## Root cause
The gateway constructed the FastAPI request body with a generic `Map`. The downstream FastAPI service received the request without the expected JSON body in the observed runtime.

## Fix
Use an explicit `FastApiQueryRequest` Java record and pass it to `RestClient.body(...)` with `Content-Type: application/json`.

## Regression test
`FastApiClientTest` verifies:
- POST `/api/query`
- `Content-Type: application/json`
- `X-Trace-ID` propagation
- exact JSON body `{ "sql": "SELECT 1" }`

## Validation
After rebuilding:
```bash
docker compose down
docker compose up --build -d
curl -X POST http://localhost:8080/api/query \
  -H 'Content-Type: application/json' \
  -H 'X-Trace-ID: day4-002' \
  -d '{"sql":"SELECT name, population FROM city ORDER BY population DESC LIMIT 5"}'
```
Expected: HTTP 200 with the PostgreSQL query result and `trace_id=day4-002`.
