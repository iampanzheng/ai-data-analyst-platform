# Stage 3.8 Package — End-to-End Acceptance & Regression v1.0

Status: **CLOSED**

## Goal

Prove that the complete P1 product path remains stable after Phase 3 integration, without adding new product behavior.

## Acceptance surface

```text
HTTP request
→ Gateway / FastAPI
→ routing / LLM
→ SQL validation
→ read-only PostgreSQL
→ optional controlled analysis
→ optional controlled chart
→ optional evidence-bound report
→ optional deterministic delivery package
```

## Implemented

- `acceptance/cases.json`: versioned acceptance manifest
- `acceptance/run.py`: standard-library HTTP runner with deterministic artifact assertions
- JSON + Markdown acceptance reports
- coverage for health, unsafe SQL rejection, ranked query, descriptive statistics, chart artifact, report/delivery, and full combined chain
- acceptance assertions intentionally avoid exact LLM wording
- frontend presentation helpers extracted into `frontend/web/src/presentation.js`
- Node 22 built-in deterministic frontend tests (`npm test`), no new dependency
- tests cover numeric/percentage formatting, friendly labels, chart nice scale, and safe inline emphasis tokenization
- Python unit coverage for acceptance assertion/path logic

## Closeout gates

1. `docker compose exec fastapi pytest -q`
2. `docker compose exec web npm test`
3. `docker compose exec web npm run build`
4. `python -m acceptance.run` against the running gateway
5. review `acceptance/results/acceptance-report.{json,md}`
6. record final Phase 3 limitations and close Phase 3


## Stage 3.8 v0.1.1 — FastAPI container packaging hotfix

The v0.1 candidate added `tests/test_acceptance.py`, which imports `acceptance.run`, but the FastAPI Docker image copied `tests/` without copying the new `acceptance/` package. In Compose this caused pytest collection to fail with `ModuleNotFoundError: No module named 'acceptance'`.

The FastAPI Dockerfile now includes:

```dockerfile
COPY acceptance /app/acceptance
```

No acceptance logic or runtime API behavior changed. The existing `tests/test_acceptance.py` import now also acts as a container-packaging regression check.

### Stage 3.8 v0.1.2 acceptance hardening

- Corrected the gateway health acceptance path from `/health` to `/api/health`.
- Stabilized ACC-004 around its intended descriptive-statistics contract by providing the exact stored occupation category `Software Developers`; synonym/category grounding is not the target of this acceptance case.
- Failed acceptance cases now persist a bounded diagnostic snapshot (trace, validated SQL, route/fallback, errors, row count/tables/columns, analysis operation names) without copying result rows or LLM prose.


## Final closeout

Final integrated verification:

```text
docker compose exec fastapi pytest -q       PASS (100%)
docker compose exec web npm test            PASS (4/4)
docker compose exec web npm run build       PASS
uv run python -m acceptance.run              PASS (7/7)
```

Acceptance evidence is stored in:

- `acceptance/results/acceptance-report.json`
- `acceptance/results/acceptance-report.md`

Stage 3.8 is CLOSED. Phase 3 is CLOSED.
