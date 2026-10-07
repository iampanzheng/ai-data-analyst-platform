# Stage 4.2 Package — Security / Configuration Cleanup

Version: **v1.0**  
Status: **CLOSED**

## Goal

Improve the local/default security posture and remove configuration inconsistencies without changing the analyst product contract or requiring GitHub/deployment infrastructure.

## Changes

- Bind published PostgreSQL, FastAPI, Gateway, and Web ports to `127.0.0.1` by default.
- Make PostgreSQL database/user/password and host ports environment-configurable with local-development defaults.
- Make Gateway CORS origin and Web API base URL environment-configurable.
- Honor `LOG_LEVEL` in FastAPI logging with INFO fallback for invalid values.
- Redact sensitive structured-log fields recursively.
- Add `scripts/security_check.py` and run it as the first `make verify` gate.
- Add deterministic logging-redaction regression tests.
- Keep repository-orchestration checks in the host security gate rather than requiring Compose/.env files inside the FastAPI runtime image.

## Non-goals

- No authentication/authorization feature is introduced.
- No business/API artifact contract changes.
- No GitHub Actions or public deployment configuration.
- No authentication/authorization feature is introduced in this stage beyond configuration/runtime hardening.

## Candidate validation

Local artifact checks completed:

- `uv run python scripts/security_check.py` — PASS
- `uv run python -m pytest -q tests/test_logging_config.py` — 3/3 PASS
- `uv run python -m compileall -q ai scripts tests` — PASS

Closeout gate: run `make verify` in the real Docker environment.

Stage 4.2 v0.1.1 fixes a local-volume compatibility regression: PostgreSQL credentials remain environment-configurable, but the local default returns to `analyst` so existing `postgres_data` volumes continue to authenticate. Changing `POSTGRES_PASSWORD` is documented as a fresh-initialization setting, not an automatic password rotation for an existing PostgreSQL volume.

Stage 4.2 v0.1.2 fixes a test-boundary regression found in the real Docker verification: repository orchestration files such as `docker-compose.yml` and `.env.example` are host-side inputs and are intentionally not copied into the FastAPI runtime image. Their compatibility assertions now live in the host `scripts/security_check.py` gate, while container pytest remains limited to portable application/runtime tests.

## Stage 4.2 v0.2 — Container Runtime Hardening

This iteration hardens the application containers to run as non-root without changing product/API behavior:

- FastAPI runs as UID/GID `10001:10001`, with `/app` and its home directory owned for in-container pytest/cache use.
- ETL runs as UID/GID `10001:10001`; fixture CSVs remain readable and database writes continue through PostgreSQL credentials.
- Gateway runtime runs as UID/GID `10001:10001`; the Maven build stage remains a build-only stage.
- Web uses the official Node image's `node` user and installs/copies application files with matching ownership.
- PostgreSQL keeps the official image user model and is intentionally not overridden.
- `scripts/security_check.py` now requires an explicit non-root runtime `USER` in every application Dockerfile.
- `make verify` now includes an image/runtime UID gate for FastAPI, ETL, Gateway, and Web before regression tests.

Local artifact validation completed:

- `uv run python scripts/security_check.py` — PASS
- logging-redaction tests — 3/3 PASS
- Python compileall — PASS
- `scripts/verify_local.sh` shell syntax — PASS

Final user-side closeout verification: PASS.

```text
FastAPI runtime uid: 10001
ETL runtime uid: 10001
Gateway runtime uid: 10001
Web runtime uid: 1000
FastAPI/Python regression suite: PASS (100%)
Frontend deterministic tests: PASS (4/4)
Frontend production build: PASS
Gateway health: PASS
Local production baseline: PASS
```

Stage 4.2 is CLOSED.
