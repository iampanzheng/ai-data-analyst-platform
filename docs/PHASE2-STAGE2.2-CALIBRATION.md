# Phase 2 — Stage 2.2 Evaluation Calibration

## Why calibration was required

The first Groq 30-case run exposed evaluator defects that materially understated model quality:

- `EvaluationCase.expected_result` was stored as `list[list]`, but semantic evaluation only read dict-shaped expected results.
- unsafe cases could be marked as database-executed even when no query result existed, because an empty result envelope was always constructed.
- harmless column-shape differences (extra columns, omitted non-required columns, aggregate aliases) were treated as semantic failures.
- large Groq `Retry-After` values could block a synchronous evaluation case for many minutes.

## Calibration changes

- support list-shaped `expected_result`
- semantic projection across harmless column differences
- preserve required columns for explicit ranking/rank tasks
- empty-result semantics for empty expected datasets
- alias-tolerant aggregate column matching
- no synthetic `actual_result` when no query executed
- separate safety semantics for reject cases
- cap synchronous `Retry-After` waits with `LLM_MAX_RETRY_AFTER_SECONDS`
- increase Groq evaluation pacing default example to 30 seconds
- add completed-case semantic correctness and latency p50/p95
- keep Exact SQL Match as a diagnostic metric only

## Calibration check against the prior Groq report

Offline rescoring of the prior report with the corrected evaluator produced:

- completed cases without provider/runtime errors: 24
- end-to-end semantic PASS among completed cases: 23/24 (95.8%)
- true semantic task failure identified: DA-020 (explicit ranking requested, rank column omitted)
- provider failures: 6 `LLM_RATE_LIMIT` cases

This offline rescore is diagnostic only. The formal Stage 2.2 baseline must be rerun using the calibrated evaluator.

## Groq evaluation settings

Recommended baseline settings:

```env
LLM_EVAL_DELAY_SECONDS=30
LLM_MAX_RETRY_AFTER_SECONDS=60
```

A provider rate limit remains a failed end-to-end case, but it is separated from completed-case model correctness.
