# Stage 2.3 Package

This package extends the Stage 2.2 final v1.0.1 baseline with reproducible model comparison and failure analysis only.

No Stage 2.2 evaluator, prompt, provider behavior, SQL security rule, or routing behavior is changed.

Added:

- `docs/PHASE2-STAGE2.3-MODEL-COMPARISON.md`
- `evaluation/compare_models.py`
- `evaluation/results/stage2.2/` frozen Groq/Qwen calibrated reports
- `evaluation/results/stage2.3/model-comparison.json`
- `evaluation/results/stage2.3/model-comparison.md`
- `evaluation/results/stage2.3/failure-matrix.csv`
- `tests/test_model_comparison.py`
- Stage 2.2 / 2.3 status update in `PROJECT-CONTEXT.md`

Stage 2.3 status: **COMPLETE**

Next: Stage 2.4 — Routing Policy.
