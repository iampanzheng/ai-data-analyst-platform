# Stage 3.5 Package — Controlled Reporting v1.0

Status: **CLOSED / verified baseline**

## Added

- optional explicit report-intent trigger
- JSON-only report selection planner
- deterministic report-plan validator and assembler
- `report_artifact` in Analyst state and `/api/analyze`
- deterministic binding to `query_result`, selected controlled-analysis operations, and `chart_artifact`
- deterministic key findings copied from application-computed analysis values
- React Report Panel
- client-side JSON export
- reporting validation/unit tests
- Agent trigger/non-trigger regression tests

## Security invariant

```text
LLM -> artifact-selection plan -> deterministic validation/binding -> report_artifact
```

The model does not generate report facts or executable report code.

## Final verification

- Compose full pytest: PASS, 100%
- reporting unit tests: PASS (5/5)
- frontend production build: PASS (`vite v8.3.1`, 15 modules transformed)
- report-only remote smoke: PASS
  - `query_result.row_count = 5`
  - `report_artifact.source = verified_artifacts`
  - query evidence present
  - `fallback_used = false`
  - `errors = []`
- combined analysis + chart + report remote smoke: PASS
  - correlation operation present
  - `pearson_r = 0.36675379037073685`
  - scatter chart artifact present
  - report evidence references query result, analysis operation, and chart artifact
  - report finding value exactly matches controlled analysis output
  - `fallback_used = false`
  - `errors = []`

Stage 3.5 is frozen. Stage 3.6 starts from this verified baseline.
