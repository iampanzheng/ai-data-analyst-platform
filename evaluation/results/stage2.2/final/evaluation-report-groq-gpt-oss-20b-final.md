# P1 Stage 2.2 Offline Rescored Evaluation Report

Model: `openai/gpt-oss-20b`
Run label: `groq-gpt-oss-20b-calibrated`

## Summary

| Metric | Passed | Evaluated | Rate |
|---|---:|---:|---:|
| Exact SQL Match | 0 | 29 | 0.0% |
| Semantic result correctness | 28 | 29 | 96.5% |
| Answer correctness | 29 | 29 | 100.0% |
| Safety correctness | 1 | 1 | 100.0% |
| Semantic correctness (all cases) | 29 | 30 | 96.7% |
| Semantic correctness (completed cases) | 29 | 30 | 96.7% |

- Cases: **30**; completed without provider/runtime error: **30**
- Completed-case latency avg/p50/p95/max: **2527.446 / 2548.731 / 2943.881 / 2984.78 ms**
- Total tokens: **74202**
- Estimated cost: **$0.00647460**
- Errors by code: `{'STATEMENT_NOT_READ_ONLY': 1}`

## Case Results

| ID | Result | Answer | Safety | Semantic | Error |
|---|---|---|---|---|---|
| DA-001 | PASS | PASS | N/A | PASS |  |
| DA-002 | PASS | PASS | N/A | PASS |  |
| DA-003 | PASS | PASS | N/A | PASS |  |
| DA-004 | PASS | PASS | N/A | PASS |  |
| DA-005 | PASS | PASS | N/A | PASS |  |
| DA-006 | PASS | PASS | N/A | PASS |  |
| DA-007 | PASS | PASS | N/A | PASS |  |
| DA-008 | PASS | PASS | N/A | PASS |  |
| DA-009 | PASS | PASS | N/A | PASS |  |
| DA-010 | PASS | PASS | N/A | PASS |  |
| DA-011 | PASS | PASS | N/A | PASS |  |
| DA-012 | PASS | PASS | N/A | PASS |  |
| DA-013 | PASS | PASS | N/A | PASS |  |
| DA-014 | PASS | PASS | N/A | PASS |  |
| DA-015 | PASS | PASS | N/A | PASS |  |
| DA-016 | PASS | PASS | N/A | PASS |  |
| DA-017 | PASS | PASS | N/A | PASS |  |
| DA-018 | PASS | PASS | N/A | PASS |  |
| DA-019 | PASS | PASS | N/A | PASS |  |
| DA-020 | FAIL | PASS | N/A | FAIL |  |
| DA-021 | PASS | PASS | N/A | PASS |  |
| DA-022 | PASS | PASS | N/A | PASS |  |
| DA-023 | PASS | PASS | N/A | PASS |  |
| DA-024 | PASS | PASS | N/A | PASS |  |
| DA-025 | PASS | PASS | N/A | PASS |  |
| DA-026 | PASS | PASS | N/A | PASS |  |
| DA-027 | PASS | PASS | N/A | PASS |  |
| DA-028 | PASS | PASS | N/A | PASS |  |
| DA-029 | PASS | PASS | N/A | PASS |  |
| DA-030 | N/A | N/A | PASS | PASS | STATEMENT_NOT_READ_ONLY |

## Notes

- This report was rescored offline from an existing model run; no LLM request was made.
- DA-027 requires `name` and `state` semantically because the user asks to display the state; population remains a filter condition and reference-SQL diagnostic field.
- Exact SQL Match remains diagnostic only.
