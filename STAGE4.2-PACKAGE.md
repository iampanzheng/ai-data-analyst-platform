# Stage 4.2 Package — Security / Configuration Cleanup

Version: **v0.1 candidate**  
Status: **ACTIVE**

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

## Non-goals

- No authentication/authorization feature is introduced.
- No business/API artifact contract changes.
- No GitHub Actions or public deployment configuration.
- Non-root container execution is deferred until ownership and in-container test behavior can be validated independently.

## Candidate validation

Local artifact checks completed:

- `uv run python scripts/security_check.py` — PASS
- `uv run python -m pytest -q tests/test_logging_config.py` — 3/3 PASS
- `uv run python -m compileall -q ai scripts tests` — PASS

Closeout gate: run `make verify` in the real Docker environment.
