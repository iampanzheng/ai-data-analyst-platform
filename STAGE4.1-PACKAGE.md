# Stage 4.1 — Local Production Baseline

Status: **v0.1 candidate**

## Goal

Create a repeatable, local-only production baseline before publishing the repository to GitHub. This stage does not add Analyst features and does not require GitHub Actions.

## Changes

- Add `.dockerignore` so secrets, Git metadata, caches, generated outputs, and local artifacts do not enter Docker build context.
- Add a FastAPI healthcheck and make the Spring Boot Gateway wait for FastAPI health rather than mere container start.
- Add `scripts/verify_local.sh` and `make verify` as the deterministic local production gate.
- Split backend tests, frontend tests, frontend build, Compose validation, and real-stack acceptance into explicit Make targets.
- Expand `.env.example` to document routing/fallback configuration without embedding secrets.
- Refresh README/PROJECT-CONTEXT for Phase 4.

## Deterministic local gate

```bash
make verify
```

This runs:

1. `docker compose config --quiet`
2. `docker compose up -d --build postgres etl fastapi gateway web`
3. `docker compose exec -T fastapi pytest -q`
4. `docker compose exec -T web npm test`
5. `docker compose exec -T web npm run build`
6. `GET http://localhost:8080/api/health`

The Stage 3.8 real-stack acceptance suite remains separate:

```bash
make acceptance
```

It may exercise configured real-model routing and therefore is not part of the deterministic local gate.

## Known remaining item

`frontend/web` does not currently contain a committed npm lockfile. Dependency locking should be generated and verified in a networked development environment in a later Phase 4 step; no synthetic lockfile is created offline.

## Closeout gates

- `make verify` passes end to end on the user's local Docker environment.
- `.env` / `.git` / caches are excluded from Docker build context.
- FastAPI reaches healthy state before Gateway startup dependency is satisfied.
- Existing Phase 3 acceptance behavior remains unchanged.
