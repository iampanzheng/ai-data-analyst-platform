# Stage 3.2 Package — Richer Analytical Data

Status: **CLOSED — user-side Compose verification passed**

## Added

- ACS 2024 five-city profile fixture
- BLS OEWS May 2023 five-metro Software Developers fixture
- richer-data ETL for education/economic/employment/salary
- explicit OEWS occupation/geography/source provenance
- derived annualized median-salary documentation
- existing-volume schema and metadata migration through ETL
- richer-data fixture and integration tests
- evaluation dataset v1.1-stage3.2 with 35 cases
- dynamic report dataset-version capture
- planner/answer geography and year guardrails

## Frozen / unchanged

- SQL Validator security boundary
- read-only execution policy
- deterministic routing
- fallback/privacy policy
- Stage 2.2 frozen real-model reports

## Packaging verification

```text
compileall: PASS
tests/test_stage32_fixture.py: 2 passed
35-case dataset JSON Schema validation: PASS
```

Packaging host does not provide the project Docker runtime, so full pytest was verified in the user Compose environment instead.

## User-side runtime verification

```text
full `docker compose exec fastapi pytest -q`: PASS (100%)
`/api/schema` richer-data evidence: PASS
salary join smoke: PASS
  Los Angeles | 153566.40 | Los Angeles-Long Beach-Anaheim, CA
```

The economic-indicator curl shown during closeout contained a shell single-quote quoting error before the request reached the API; this was a command-line quoting issue, not an application failure.
