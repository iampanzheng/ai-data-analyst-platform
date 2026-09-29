# Stage 2.2 Final Package

This package is based on `ai-data-analyst-phase2-stage2.2-calibrated-v0.2` and adds the final Stage 2.2 calibration/closeout.

## Added / changed

- `evaluation/dataset.json`
  - DA-027 now explicitly declares `semantic_columns: ["name", "state"]`.
- `evaluation/dataset.schema.json`
  - supports optional `semantic_columns`.
- `evaluation/evaluator.py`
  - loads `semantic_columns` into `EvaluationCase`.
- `evaluation/semantic_eval.py`
  - uses explicit semantic output columns while preserving reference SQL/result diagnostics.
- `evaluation/rescore.py`
  - offline re-score of existing model reports; no LLM calls required.
- `tests/test_semantic_eval.py`
  - regression tests for semantic-column projection and required rank behavior.
- `evaluation/results/stage2.2/raw/`
  - original calibrated Groq and Qwen reports.
- `evaluation/results/stage2.2/final/`
  - offline rescored final reports.
- `docs/PHASE2-STAGE2.2-FINAL.md`
  - final Stage 2.2 comparison and closeout.

## Validation performed in packaging environment

- `python -m compileall -q ai evaluation tests` — PASS
- `python -m pytest -q tests/test_semantic_eval.py` — 18 passed
- dataset JSON Schema validation — PASS
- offline re-score for both Groq and Qwen reports — PASS

Full project pytest could not be executed in the packaging environment because `psycopg` and `sqlglot` are not installed there. Run the normal project/Docker test suite locally before committing.
