# Day 3 Fix 3 — Make integration tests executable inside FastAPI container

## Problem
The FastAPI image was built with `./ai/analyst` as build context and only copied `app/` into the image. The repository `tests/` directory was therefore absent, so:

    docker compose exec fastapi pytest -q

returned `no tests ran`.

## Fix
- Docker build context changed to repository root.
- Image now copies `/ai` and `/tests`.
- `PYTHONPATH=/app` makes `ai.analyst...` imports work.
- Uvicorn imports `ai.analyst.app.main:app`.

## Validation intent
After rebuild:

    docker compose up --build -d
    docker compose exec fastapi pytest -q

should collect both unit and integration tests. Because `DATABASE_URL` is present in the container, integration tests should execute against the Compose PostgreSQL service.
