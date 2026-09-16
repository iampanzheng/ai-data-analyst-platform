# Sprint 0 Day 4

## Goal
Establish the end-to-end application skeleton:

```text
React → Spring Boot Gateway → FastAPI → PostgreSQL
```

No LLM/Agent is added in Day 4.

## Services

- `postgres`: data store
- `etl`: data loading job
- `fastapi`: deterministic AI/data execution API
- `gateway`: Spring Boot API edge
- `web`: React/Vite UI

## Gateway API

- `GET /api/health` → FastAPI health
- `GET /api/schema` → schema metadata
- `POST /api/query` → safe SQL query

The gateway forwards `X-Trace-ID` to FastAPI and propagates FastAPI error bodies/statuses.

## Local verification

```bash
docker compose up --build -d
curl http://localhost:8080/api/health
curl http://localhost:8080/api/schema
curl -X POST http://localhost:8080/api/query \\
  -H 'Content-Type: application/json' \\
  -H 'X-Trace-ID: day4-001' \\
  -d '{"sql":"SELECT name, population FROM city ORDER BY population DESC LIMIT 5"}'
```

Open `http://localhost:5173` for the minimal React client.

## Expected architecture

```text
Browser
   ↓
React :5173
   ↓
Spring Boot :8080
   ↓
FastAPI :8000
   ↓
PostgreSQL :5432
```
