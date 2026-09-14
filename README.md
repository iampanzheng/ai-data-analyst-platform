# P1 — AI Data Analyst Platform

V1.1 Sprint 0 / Day 1: public data → ETL → PostgreSQL → SQL.

## Run
```bash
cp .env.example .env
make etl
make up
```

For fresh public raw files:
```bash
make data-download
```
This downloads Census Vintage 2025 city population data and BLS May 2024 OEWS metropolitan data. The Census fixture is checked in so the clean-clone demo does not depend on network access.

## First query
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/query -H 'Content-Type: application/json' -d '{"sql":"SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5"}'
```

## Day 1 data flow
```text
Public data
    ↓
data/raw
    ↓
ETL
    ↓
data/processed
    ↓
PostgreSQL
    ↓
FastAPI /api/query
    ↓
SQL result
```

The LLM agent is intentionally not part of Day 1.
