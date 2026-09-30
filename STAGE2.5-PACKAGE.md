# Stage 2.5 Package — Reliability, Fallback & Cost Control

This package continues directly from the verified Stage 2.4 routing implementation.

## Main additions

- `ai/analyst/app/llm/reliability.py`
- deterministic retryable-error fallback
- privacy-safe local behavior
- sticky fallback at the LLM-call boundary
- route-level usage and estimated cost telemetry
- optional request cost guard
- API/Gateway/React propagation of `fallback_mode`
- fallback metadata in `/api/analyze`
- `tests/test_reliability.py`
- Stage 2.5 documentation and environment settings

## Validation performed in packaging environment

- Python compileall / py_compile: PASS
- `tests/test_reliability.py` + `tests/test_routing.py`: 17 passed
- Full suite not claimed in packaging environment because its system Python lacks project dependencies such as sqlglot/psycopg.

User-side closeout should run the normal project pytest suite and runtime smoke tests.
