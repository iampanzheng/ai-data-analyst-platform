# 09 Evaluation Dataset Schema

Day 6 uses `evaluation/dataset.json` as the versioned evaluation dataset and `evaluation/dataset.schema.json` as its machine-readable schema.

Each case contains:

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
expected_error_code
```

Runtime output is captured separately as:

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
model/provider
error_type
error_message
```

The initial dataset contains 30 cases and covers filtering, aggregation, ranking, grouping, sorting, year/date filters, CTE/subquery/window queries, ambiguous wording, joins, edge cases, and unsafe requests.

The evaluator is deterministic by default:

- SQL: SQLGlot PostgreSQL canonicalization
- result: column/row comparison with numeric tolerance
- answer: expected keyword containment
- rejection: expected security error code

LLM-as-a-Judge is intentionally deferred until the deterministic baseline is established.
