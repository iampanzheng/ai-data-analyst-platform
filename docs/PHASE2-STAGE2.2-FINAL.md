# Phase 2 — Stage 2.2: 30-case Multi-model Baseline

## Status

**COMPLETE**

Stage 2.2 freezes the calibrated evaluation dataset/evaluator and compares the same 30-case workload across:

- Local: Ollama + `qwen3:8b`
- Hosted: Groq + `openai/gpt-oss-20b`

No routing policy is selected in this stage. The results are inputs to Stage 2.3 and Stage 2.4.

## Final Calibration

DA-027 asks:

> 找出所有人口超过 150 万的城市，并显示州。

The reference SQL may still select population for diagnostic comparison, but the user-required semantic output is only:

- `name`
- `state`

The dataset therefore records:

```json
"semantic_columns": ["name", "state"]
```

This does not hide the Qwen answer-quality issue: its DA-027 answer contains `新 York`, so answer/end-to-end correctness remain FAIL. No model-specific alias or exception was added.

## Final Baseline

| Metric | Qwen3 8B / Ollama | GPT-OSS 20B / Groq |
|---|---:|---:|
| Cases | 30 | 30 |
| Completed | 24/30 | 30/30 |
| Semantic result correctness | 22/29 (75.9%) | 28/29 (96.6%) |
| Answer correctness | 22/29 (75.9%) | 29/29 (100%) |
| Safety correctness | 1/1 (100%) | 1/1 (100%) |
| End-to-end semantic, all cases | 22/30 (73.3%) | 29/30 (96.7%) |
| End-to-end semantic, completed cases | 22/24 (91.7%) | 29/30 (96.7%) |
| Average latency | 65.955 s | 2.527 s |
| P50 latency | 63.807 s | 2.549 s |
| P95 latency | 116.302 s | 2.944 s |
| Max latency | 126.038 s | 2.985 s |
| Total tokens | 74,788 | 74,202 |
| Estimated API cost | $0 | $0.0064746 |
| Provider/runtime failures | 6 timeouts | 0 |

Groq was approximately **26.1× faster** on average in this baseline.

## Shared Failure

Both models fail DA-020 semantically.

The question explicitly asks for population ranking and top 3 output. Both models return the correct top three cities but omit an explicit rank column from the query result. This remains a real instruction-adherence failure and is intentionally retained.

## Qwen-specific Findings

Qwen completed-case semantic correctness is strong (91.7%), but system reliability is reduced by six `LLM_TIMEOUT` cases. Local inference also has much higher latency and substantially larger output-token usage than Groq.

DA-027 remains an answer-level failure because `New York` is rendered as `新 York`. The evaluator is not relaxed for this one output.

## Groq-specific Findings

Groq completed all 30 cases without provider/runtime failure. Its only semantic failure is DA-020. The unsafe request DA-030 is correctly blocked by the deterministic SQL Validator with `STATEMENT_NOT_READ_ONLY` before database execution.

## Metric Interpretation

`Exact SQL Match` remains a diagnostic metric only. Equivalent SQL forms, harmless aliases, extra columns, latest-year filters, and other semantically valid differences can fail exact matching while producing correct business results.

Primary quality signals are:

- semantic result correctness
- answer correctness
- end-to-end semantic correctness
- safety correctness
- provider/runtime completion rate
- latency and cost

## Offline Re-score

`evaluation/rescore.py` can re-apply the frozen semantic evaluator to an existing JSON report without calling the model again.

Example:

```bash
python -m evaluation.rescore \
  evaluation/results/stage2.2/raw/evaluation-report-qwen3-8b-ollama-calibrated.json \
  --output evaluation/results/stage2.2/final/evaluation-report-qwen3-8b-ollama-final.json
```

## Next Step

Proceed to **Stage 2.3 — Model Comparison & Failure Analysis**.

Use the measured Stage 2.2 results to characterize model strengths, reliability, latency, token behavior, and deployment tradeoffs before defining the deterministic routing policy in Stage 2.4.
