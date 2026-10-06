# Phase 3 / Stage 3.8 — End-to-End Acceptance & Regression

Stage 3.8 is a verification stage, not a feature stage.

## Why

Phase 3 now spans controlled numerical analysis, visualization, evidence-bound reporting, deterministic delivery packaging, and a portfolio-ready web workspace. The final Phase 3 gate should verify the integrated behavior rather than add another capability.

## Two-layer verification

### Real-stack HTTP acceptance

`acceptance/run.py` calls the running application through the gateway and checks stable machine contracts. It does not require exact natural-language answer wording.

The suite covers:
- availability
- SQL security boundary
- verified query result
- controlled analysis
- controlled visualization
- evidence-bound report
- deterministic delivery package
- full combined artifact chain

### Deterministic frontend regression

Presentation-only logic lives in `frontend/web/src/presentation.js` and is tested using Node 22's built-in `node:test` runner. This avoids new test-runtime dependencies while locking down the presentation behaviors discovered during Stage 3.7 browser review.

Raw artifacts remain unchanged; tests only verify display-layer behavior.

## Phase 3 closeout rule

Do not close Phase 3 until backend pytest, frontend deterministic tests, frontend production build, and real-stack acceptance all pass and the generated acceptance report has been reviewed.


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


## Final result

Stage 3.8 completed successfully on the integrated stack:

```text
backend pytest                 PASS (100%)
frontend deterministic tests  PASS (4/4)
frontend production build     PASS
real-stack acceptance          PASS (7/7)
```

The generated acceptance reports are checked into `acceptance/results/` as closeout evidence. Stage 3.8 and Phase 3 are CLOSED.
