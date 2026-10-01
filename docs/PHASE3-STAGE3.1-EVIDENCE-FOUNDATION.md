# Phase 3 — Stage 3.1: Evidence Foundation

Status: **Implemented; pending final local container verification**

## Goal

Before adding richer datasets, Python analysis, charts, or reports, make the actual availability of each analytical dataset explicit to the application and the LLM.

Previously, the schema exposed that tables existed, but did not tell the Analyst whether those tables contained usable rows. Stage 3.1 adds deterministic dataset evidence to the existing schema contract.

## API contract

Every allowlisted table returned by `GET /api/schema` now includes:

```text
evidence.row_count
evidence.data_status
evidence.min_year
evidence.max_year
evidence.evidence_note
```

`data_status` is `available` or `empty`. If a table has a `year` column, the service also reports the loaded minimum and maximum year.

## Current fixture expectations

### city

```json
{
  "row_count": 15,
  "data_status": "available",
  "min_year": 2025,
  "max_year": 2025,
  "evidence_note": "15 rows are currently loaded for year range 2025."
}
```

### salary

```json
{
  "row_count": 0,
  "data_status": "empty",
  "min_year": null,
  "max_year": null,
  "evidence_note": "No rows are currently loaded for this dataset."
}
```

Other currently empty analytical tables should follow the same empty-data semantics.

## Planner behavior

The SQL system prompt now treats table evidence as authoritative:

- do not assume an `empty` table contains rows;
- do not invent business facts from an empty dataset;
- avoid relying on empty tables unless the user explicitly asks about that dataset or its lack of data.

This does not replace SQL validation. Generated SQL remains untrusted and must still pass the existing SQL Validator before database execution.

## Safety boundary

Stage 3.1 does not change:

- allowlisted schemas/tables;
- SQL Validator rules;
- read-only transaction policy;
- row cap / statement timeout;
- deterministic routing;
- fallback/privacy behavior.

Evidence queries use table/schema identifiers originating from the existing allowlist/introspection path and quote them with psycopg identifiers.

## Verification

Packaging environment:

```text
compileall: PASS
```

The packaging sandbox does not expose Docker and its host Python environment does not include the project's `psycopg` dependency. Therefore full verification is intentionally deferred to the project's normal Compose environment rather than installing ad-hoc sandbox dependencies.

Run:

```bash
docker compose up -d --build postgres etl fastapi
docker compose exec fastapi pytest -q
```

Then verify the real API:

```bash
curl -sS http://localhost:8000/api/schema
```

Acceptance:

- full pytest suite is green;
- `city.evidence.row_count == 15`;
- `city.evidence.data_status == "available"`;
- `city.evidence.min_year == 2025`;
- `city.evidence.max_year == 2025`;
- `salary.evidence.row_count == 0`;
- `salary.evidence.data_status == "empty"`;
- SQL security/routing/fallback regressions remain green.

## Next stage

After Stage 3.1 is verified and closed:

> **Stage 3.2 — Richer Analytical Data**

That stage should populate the currently empty analytical domains with reproducible fixture/source data so later Python analysis and visualization operate on meaningful multi-table evidence.
