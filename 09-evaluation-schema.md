# 09 Evaluation Dataset Schema

The canonical machine-readable schema is:

```text
evaluation/dataset.schema.json
```

`evaluation.run.load_cases()` validates `evaluation/dataset.json` against JSON Schema Draft 2020-12 before evaluation begins.

## Case fields

```text
question_id
question
category
difficulty
expected_behavior
expected_sql
expected_tables
expected_columns
expected_result
result_order
expected_answer_contains
expected_error_code (reject cases)
```

## Captured run fields

```text
actual_sql
validated_sql
actual_result
actual_answer
sql_correct
result_correct
answer_correct
latency_ms
input_tokens
output_tokens
total_tokens
estimated_cost
trace_id
model
provider
error_type
error_message
```

## Baseline

The first dataset contains 30 cases. Versioned Mock baseline artifacts live under:

```text
evaluation/results/baseline-mock-v0.1.json
evaluation/results/baseline-mock-v0.1.md
```

Evaluator semantics and limitations are documented in `evaluation/README.md`.
