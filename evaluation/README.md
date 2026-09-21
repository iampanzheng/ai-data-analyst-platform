# Evaluation Harness v0.1

This directory contains the deterministic evaluation harness for Analyst Agent v0.1.

## Baseline artifacts

The reviewed Mock Provider baseline is preserved as:

```text
results/baseline-mock-v0.1.json
results/baseline-mock-v0.1.md
```

Do not overwrite these files with later model runs. New provider/model baselines should use distinct names.

## Dataset validation

`dataset.json` is validated against `dataset.schema.json` (JSON Schema Draft 2020-12) before evaluation cases are constructed. Dataset-shape errors fail fast.

## Evaluator v0.1 semantics

- `sql_correct`: SQLGlot-normalized reference-SQL equality. This is deterministic structural/reference matching, not full semantic SQL equivalence.
- `result_correct`: column/row comparison with ordered/unordered modes and numeric tolerance. For answer-producing cases this is the stronger objective correctness signal.
- `answer_correct`: deterministic required-keyword containment. This does not measure full semantic answer quality.
- Reject cases: correctness is based on the expected validator/error code; result and answer metrics are N/A.

LLM-as-a-Judge is intentionally deferred. The v0.1 baseline should remain stable so later real-model runs can be compared against it.

## Run

```bash
python -m evaluation.run
```

or:

```bash
make eval
```

The normal runner writes the latest run to `evaluation/results/evaluation-report.json` and `evaluation/results/evaluation-report.md`. Promote a reviewed run to a versioned baseline filename when it should be preserved for comparison.
