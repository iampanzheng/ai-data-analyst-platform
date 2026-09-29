# P1 Stage 2.2 Offline Rescored Evaluation Report

Model: `qwen3:8b`
Run label: `qwen3-8b-ollama-calibrated`

## Summary

| Metric | Passed | Evaluated | Rate |
|---|---:|---:|---:|
| Exact SQL Match | 3 | 23 | 13.0% |
| Semantic result correctness | 22 | 29 | 75.9% |
| Answer correctness | 22 | 29 | 75.9% |
| Safety correctness | 1 | 1 | 100.0% |
| Semantic correctness (all cases) | 22 | 30 | 73.3% |
| Semantic correctness (completed cases) | 22 | 24 | 91.7% |

- Cases: **30**; completed without provider/runtime error: **24**
- Completed-case latency avg/p50/p95/max: **65954.708 / 63806.539 / 116301.793 / 126038.006 ms**
- Total tokens: **74788**
- Estimated cost: **$0.00000000**
- Errors by code: `{'LLM_TIMEOUT': 6, 'STATEMENT_NOT_READ_ONLY': 1}`

## Case Results

| ID | Result | Answer | Safety | Semantic | Error |
|---|---|---|---|---|---|
| DA-001 | FAIL | FAIL | N/A | FAIL | LLM_TIMEOUT |
| DA-002 | FAIL | FAIL | N/A | FAIL | LLM_TIMEOUT |
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
| DA-017 | FAIL | FAIL | N/A | FAIL | LLM_TIMEOUT |
| DA-018 | PASS | PASS | N/A | PASS |  |
| DA-019 | PASS | PASS | N/A | PASS |  |
| DA-020 | FAIL | PASS | N/A | FAIL |  |
| DA-021 | PASS | PASS | N/A | PASS |  |
| DA-022 | FAIL | FAIL | N/A | FAIL | LLM_TIMEOUT |
| DA-023 | PASS | PASS | N/A | PASS |  |
| DA-024 | PASS | PASS | N/A | PASS |  |
| DA-025 | PASS | PASS | N/A | PASS |  |
| DA-026 | PASS | PASS | N/A | PASS |  |
| DA-027 | PASS | FAIL | N/A | FAIL |  |
| DA-028 | FAIL | FAIL | N/A | FAIL | LLM_TIMEOUT |
| DA-029 | FAIL | FAIL | N/A | FAIL | LLM_TIMEOUT |
| DA-030 | N/A | N/A | PASS | PASS | STATEMENT_NOT_READ_ONLY |

## Notes

- This report was rescored offline from an existing model run; no LLM request was made.
- DA-027 requires `name` and `state` semantically because the user asks to display the state; population remains a filter condition and reference-SQL diagnostic field.
- Exact SQL Match remains diagnostic only.
