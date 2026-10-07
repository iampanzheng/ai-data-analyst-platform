# Phase 4 / Stage 4.1 — Local Production Baseline

## Intent

Phase 4 begins locally. The repository does not need to be pushed to GitHub yet. Stage 4.1 turns the Phase 3 application into a repeatable local production baseline that can later be wired into CI without redesigning the verification workflow.

## Verification model

The deterministic gate is `make verify`. It validates configuration, builds and starts the Compose stack, executes backend and frontend regressions, creates the production frontend bundle, and checks the public Gateway health endpoint.

Real-model acceptance remains a separate `make acceptance` operation because external provider availability, latency, quota, and credentials are not deterministic local build properties.

## Docker hygiene

`.dockerignore` excludes local secrets, Git metadata, Python/Node caches, generated reports, and archive artifacts from build context. This complements `.gitignore`; the two files solve different problems.

## Startup health

FastAPI exposes `/health`. Compose now declares a FastAPI healthcheck, and the Gateway waits for `service_healthy`. This avoids treating a merely-started Python process as an available upstream service.

## Configuration hygiene

`.env.example` contains safe defaults and the supported routing/fallback keys. Real credentials belong only in `.env` or process environment and must not be committed.

## Dependency reproducibility

The Python dependency set is version-pinned. The frontend currently lacks a committed npm lockfile, so Node dependency locking remains a known Phase 4 item. It should be produced with the actual package manager in a networked development environment and then verified, not reconstructed manually.


## Host Python runtime policy

Stage 4.1 v0.1.1 standardizes host-side Python execution on `uv run python`. This avoids relying on whether a workstation exposes the interpreter as `python` or `python3`, and keeps host commands inside the project's uv-managed runtime. Docker-container commands may continue to call `python` directly because the container image defines that interpreter.
