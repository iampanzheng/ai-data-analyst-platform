# Stage 3.3 Package — Controlled Python Analysis v1.0

Status: ✅ CLOSED

## v0.1.3 regression fix

- fixes double-escaped raw regexes in `_sql_precomputes_controlled_analysis` that raised `re.error: missing ), unterminated subpattern`
- adds regression assertions for correlation, descriptive-statistics aggregates / percentile, and percent-change window functions
- does not change the Stage 3.3 architecture or execution policy

## v0.1.2 changes

This candidate adds deterministic enforcement for controlled-analysis questions.

For correlation, descriptive statistics, and percent-change intents:

1. The first LLM SQL candidate is normalized and passed through the existing SQL Validator.
2. If the validated SQL precomputes the controlled statistic, the Agent requests exactly one repaired raw-row SQL plan.
3. The repaired SQL is passed through the same SQL Validator again.
4. If it still precomputes the statistic, the request fails with `ANALYSIS_SQL_PRECOMPUTED`.
5. Only the final validated raw-row SQL is executed.
6. The controlled Python executor performs the requested statistic from the verified SQL result.

This preserves the existing SQL Validator security boundary and avoids whole-Agent replay or duplicate SQL execution.

## Controlled operations

- `descriptive_stats`
- `correlation`
- `percent_change`

No arbitrary Python code execution, `eval`, `exec`, filesystem, network, shell, or OS access is exposed.

## Verification and closeout

Packaging checks:

- `python -m compileall -q ai/analyst/app tests`: PASS
- isolated `_sql_precomputes_controlled_analysis` checks: PASS for correlation / descriptive stats / percentile / percent-change / raw-row negative cases

Final user-side verification on the v0.1.3 hotfix baseline:

- full Compose pytest: PASS, 100%
- remote correlation smoke: PASS
  - raw SQL rows returned for five cities
  - controlled operation: `correlation`
  - `pearson_r = 0.36675379037073685`
  - `fallback_used = false`
  - `errors = []`
- remote descriptive-statistics smoke: PASS
  - raw SQL rows returned for five 2023 software-developer metro salary observations
  - controlled operation: `descriptive_stats`
  - `count = 5`
  - `min = 125715.2`
  - `max = 153566.4`
  - `mean = 136693.44`
  - `median = 129188.8`
  - `fallback_used = false`
  - `errors = []`

The v0.1.2 malformed-regex regression is therefore closed. Stage 3.3 acceptance criteria are satisfied and the stage is formally CLOSED.

## Stage 3.4 handoff

Next starting point: **Stage 3.4 — Visualization**.

Preserve the Stage 3.3 execution boundary:

`validated SQL -> verified rows -> controlled analysis operations -> evidence-backed answer`

Visualization should consume verified query/analysis evidence; it must not introduce arbitrary Python execution or bypass the SQL Validator.
