# Stage 3.6 Package — Export / Deliverable Packaging v1.0

Status: **CLOSED**

Frozen implementation baseline: **v0.1.2**

## Goal

Turn the already verified query/analysis/chart/report artifacts into user-downloadable deliverables without introducing another factual or executable surface.

## Architecture

```text
verified query_result
+ optional controlled analysis_result
+ optional controlled chart_artifact
+ controlled report_artifact
        ↓
deterministic delivery packager
        ↓
delivery_artifact
        ↓
JSON / Markdown browser export
```

## v0.1.1 evidence-boundary hotfix

The v0.1 functional gates passed in the normal Compose environment, but closeout review found one semantic trust-boundary issue: `report_artifact.summary` directly inherited the LLM `final_answer`, which could carry unsupported source-attribution text into an artifact labeled `source = verified_artifacts`.

The hotfix changes the boundary to:

```text
LLM final_answer -> top-level conversational answer only
verified query/analysis/chart artifacts -> deterministic evidence summary -> report/delivery
```

Changes:
- report summary is now generated deterministically from verified query metadata and selected controlled operations/chart metadata
- `final_answer` is no longer copied into the verified report summary
- report artifact exposes `summary_source = deterministic_evidence`
- regression coverage rejects leakage of unsupported phrases such as `official government statistics` into verified summaries/Markdown exports


## v0.1.2 test-alignment hotfix

The first host-side `uv run pytest -q` after v0.1.1 exposed one stale Agent regression assertion that still expected the pre-hotfix behavior (`report_artifact.summary == final_answer`). Runtime behavior was correct; the test contract was obsolete.

Updated `tests/test_agent.py` now explicitly verifies the new trust boundary:
- `state.final_answer` keeps the LLM conversational answer
- `report_artifact.summary` is the deterministic evidence summary
- `report_artifact.summary_source == deterministic_evidence`
- LLM-only wording does not leak into the verified report summary

No runtime code or API contract changed in v0.1.2.

## Added

- `ai/analyst/app/tools/delivery.py`
- `delivery_artifact` in `AnalystState`
- `delivery_artifact` in `/api/analyze`
- versioned manifest: `p1.delivery.v1`
- provenance: trace ID, question, validated SQL, tables, row count
- evidence snapshot containing verified query rows and optional controlled analysis/chart artifacts
- deterministic Markdown renderer
- stable delivery JSON and Markdown filenames
- React export actions for delivery JSON and Markdown
- delivery unit tests
- Agent-level regression test for report → delivery packaging

## Security invariant

```text
verified artifacts -> deterministic packaging -> inert JSON/Markdown
```

No additional LLM call is used for delivery packaging. The packager rejects missing or non-verified reports and never executes report/export content.

## Verification completed in packaging environment

- `python -m compileall -q ai/analyst/app tests`: PASS
- `tests/test_reporting.py` + `tests/test_delivery.py`: PASS (13/13) after v0.1.1 hotfix
- Agent-level regression collection: BLOCKED by host environment missing `sqlglot`; not counted as PASS

## Final closeout verification

The v0.1 functional gates passed in the normal Compose environment:

1. `docker compose exec fastapi pytest -q` — PASS
2. `docker compose exec web npm run build` — PASS
3. report-only remote delivery smoke — PASS
4. combined correlation + scatter + report + delivery smoke — PASS

The v0.1.2 hotfix closeout rerun also passed:

1. full Compose pytest — PASS, 100%
2. frontend production build — PASS (`vite v8.3.1`, 15 modules transformed)
3. report-only smoke — PASS; deterministic summary source present and unsupported source attribution excluded from verified report/delivery
4. combined smoke — PASS; controlled correlation/chart evidence preserved in deterministic summary and delivery snapshot

Stage 3.6 is CLOSED.
