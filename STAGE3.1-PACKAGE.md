# Stage 3.1 Package — Evidence Foundation

This package starts Phase 3 from the closed Phase 2 baseline.

## Implemented

- table-level evidence metadata in `/api/schema`
- row count and data availability status
- min/max year profiling for datasets with a `year` column
- SQL planner awareness of empty datasets
- integration assertions for current `city` and `salary` fixture states
- Phase 3 documentation and project-context updates

## Deliberately unchanged

- SQL Validator
- read-only database policy
- routing/fallback architecture
- provider configuration
- Phase 2 evaluation baseline

## Packaging-environment verification

```text
compileall: PASS
```

Full pytest is not claimed from the packaging sandbox because Docker is unavailable there and host Python lacks the project's `psycopg` dependency.

Use the normal project container:

```bash
docker compose up -d --build postgres etl fastapi
docker compose exec fastapi pytest -q
curl -sS http://localhost:8000/api/schema
```

Close Stage 3.1 after those checks pass.
