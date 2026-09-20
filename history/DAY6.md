# Day 6 — Evaluation Harness

## Scope
- deterministic evaluation dataset with 30 cases
- SQL correctness using SQLGlot PostgreSQL canonicalization
- deterministic database result comparison with numeric tolerance
- deterministic answer correctness via expected keyword containment
- Analyst Agent v0.1 execution capture
- latency, token usage, and estimated cost collection
- JSON + Markdown evaluation reports

## Dataset

`evaluation/dataset.json` contains 30 cases spanning:

- filtering
- aggregation
- ranking
- grouping
- sorting
- year/date filters
- CTE / subquery / window query
- ambiguous wording
- joins
- edge cases
- unsafe requests

The current minimal fixture only has populated `city` data. Salary-related cases intentionally exercise the current empty-table behavior and should not be interpreted as evidence that the salary dataset is complete.

## Run

With the normal project environment and PostgreSQL available:

```bash
LLM_PROVIDER=mock python -m evaluation.run
```

or:

```bash
make eval
```

Outputs:

```text
evaluation/results/evaluation-report.json
evaluation/results/evaluation-report.md
```

The mock provider is deterministic and requires no API key. Trace IDs are deterministic (`eval-DA-001`, etc.) so individual cases can be correlated across repeated runs.

## Metrics

### SQL correctness

For answer-producing cases, the candidate SQL is parsed with SQLGlot using PostgreSQL dialect and compared after canonicalization against `expected_sql`.

For rejection cases, SQL correctness means the expected security error code was returned.

### Result correctness

Columns and rows are compared against the expected result. Results are ordered by default; an evaluation case may opt into unordered comparison. Numeric values use a small relative tolerance to avoid false failures from PostgreSQL `NUMERIC`/Python float representation differences.

### Answer correctness

The initial harness deliberately avoids an LLM-as-a-Judge. `expected_answer_contains` defines deterministic required terms. This is intentionally a baseline metric, not a semantic judge.

### Latency / tokens / cost

Latency measures the full `AnalystAgent.run()` call. Token fields normalize common provider keys (`input_tokens` / `prompt_tokens`, `output_tokens` / `completion_tokens`). Estimated cost uses:

```text
LLM_INPUT_COST_PER_1M
LLM_OUTPUT_COST_PER_1M
```

Both default to `0`, and the mock provider reports zero usage.

## Verification rule

Do not treat the evaluation harness itself as evidence that the Analyst Agent is accurate. The harness must run against the actual Agent and live PostgreSQL environment. The first real baseline is expected to expose the limitations of the deterministic Day 5 mock model.
