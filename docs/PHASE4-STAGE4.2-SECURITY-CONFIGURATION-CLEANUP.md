# Phase 4 — Stage 4.2 Security / Configuration Cleanup

## Purpose

Stage 4.2 improves the default local security posture and makes security-sensitive runtime configuration explicit. It intentionally avoids adding authentication or changing the evidence-backed analysis pipeline.

## Default network exposure

Compose-published ports are bound to `127.0.0.1` by default. This keeps PostgreSQL, FastAPI, the Gateway, and the development Web server reachable from the local machine while preventing accidental LAN exposure from the default Compose configuration.

The internal Docker network remains unchanged; services still communicate by service name.

## Database configuration

`POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` are now environment-configurable. The checked-in examples contain local-development defaults only. Real credentials belong in `.env` or the process environment and `.env` remains excluded from Git and Docker build context.

## CORS and frontend endpoint configuration

`CORS_ALLOWED_ORIGIN` and `VITE_API_BASE_URL` are controlled through environment variables instead of being hard-coded in Compose. The default remains the local development origin/API URL.

## Logging hygiene

FastAPI structured JSON logging now:

- honors `LOG_LEVEL`;
- falls back to INFO for invalid level names;
- recursively redacts sensitive structured fields including API keys, passwords, authorization values, secrets, tokens, and database URLs;
- preserves non-secret token usage counters such as `input_tokens`.

The existing application log events use constant messages and bounded metadata. The redaction layer is defense-in-depth for future structured fields.

## Deterministic security gate

`scripts/security_check.py` checks key repository configuration assumptions, including secret-file ignore rules, removal of the legacy hard-coded database password, environment-configurable CORS, and loopback-only published ports. `make verify` executes this check before the existing Compose/build/test/health gates.

## Deferred item: non-root containers

The current application containers still use their base-image default user. Converting them to non-root is desirable, but it affects file ownership, in-container pytest/cache behavior, and build/runtime permissions. It is deliberately deferred to a separately validated change rather than being mixed into this configuration-hardening candidate.
