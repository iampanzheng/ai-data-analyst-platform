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

Stage 4.2 v0.1.1 fixes a local-volume compatibility regression: PostgreSQL credentials remain environment-configurable, but the local default returns to `analyst` so existing `postgres_data` volumes continue to authenticate. Changing `POSTGRES_PASSWORD` is documented as a fresh-initialization setting, not an automatic password rotation for an existing PostgreSQL volume.

Stage 4.2 v0.1.2 fixes a test-boundary regression found in the real Docker verification: repository orchestration files such as `docker-compose.yml` and `.env.example` are host-side inputs and are intentionally not copied into the FastAPI runtime image. Their compatibility assertions now live in the host `scripts/security_check.py` gate, while container pytest remains limited to portable application/runtime tests.

## Container runtime hardening (v0.2)

Application containers now use explicit non-root runtime identities. The build stages may still run privileged package-install/build steps, but the final FastAPI, ETL, Gateway, and Web processes do not run as UID 0. PostgreSQL is excluded from custom user overrides because the official image already manages its runtime user and data-directory ownership.

FastAPI receives owned application/home directories so container-side pytest remains supported. The Web image uses the official `node` user and `--chown` copies so Vite can use its application tree without root. Gateway uses a fixed numeric runtime identity and writes temporary JVM state only to standard writable temporary locations.

The local verification gate now checks this twice: `scripts/security_check.py` validates Dockerfile policy statically, and `make verify` runs `id -u` from each built application image and rejects UID 0 before running the existing regression/build/health gates.


## Final closeout

The final real-Docker verification passed all eight local production gates after runtime hardening. Runtime UID checks reported FastAPI `10001`, ETL `10001`, Gateway `10001`, and Web `1000`, confirming that the application containers do not run as root. Backend regressions, frontend deterministic tests, the production Web build, and Gateway health also passed.

Stage 4.2 is CLOSED.
