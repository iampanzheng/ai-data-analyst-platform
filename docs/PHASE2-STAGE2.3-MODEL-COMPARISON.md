# Phase 2 — Stage 2.3 Model Comparison & Failure Analysis

Status: **COMPLETE**

Stage 2.3 compares the frozen Stage 2.2 calibrated baselines. It does not modify the dataset, evaluator, prompts, model configuration, or routing behavior.

## Inputs

- `qwen3:8b` via local Ollama
- `openai/gpt-oss-20b` via Groq
- same 30-case dataset
- same calibrated semantic/result/answer/safety evaluator
- Stage 2.2 full pytest verified by the developer before this stage

Raw Stage 2.2 reports are preserved under `evaluation/results/stage2.2/`.

## Measured comparison

| Metric | Qwen3 8B / Ollama | GPT-OSS 20B / Groq |
|---|---:|---:|
| Cases | 30 | 30 |
| Completed | 24/30 (80.0%) | 30/30 (100.0%) |
| Semantic result | 22/29 (75.9%) | 28/29 (96.6%) |
| Answer | 22/29 (75.9%) | 29/29 (100.0%) |
| Safety | 1/1 (100.0%) | 1/1 (100.0%) |
| End-to-end semantic, all cases | 22/30 (73.3%) | 29/30 (96.7%) |
| End-to-end semantic, completed | 22/24 (91.7%) | 29/30 (96.7%) |
| Average completed-case latency | 65.955 s | 2.527 s |
| P95 completed-case latency | 116.302 s | 2.944 s |
| Input tokens | 52,930 | 70,160 |
| Output tokens | 21,858 | 4,042 |
| Total tokens | 74,788 | 74,202 |
| Estimated API cost | $0 | $0.00647460 |
| Provider/runtime failures | 6 | 0 |

Derived from the measured runs:

- Groq/GPT-OSS was approximately **26.1x faster** by average completed-case latency.
- Qwen produced approximately **5.41x more output tokens** in the measured run.
- Total tokens were nearly equal, but token composition differed substantially.

These measurements describe this specific hardware/provider/configuration and dataset. They are not universal model benchmarks.

## Failure taxonomy

### Shared semantic failure — DA-020

Question: rank cities by population and return only the top three.

Both models returned the correct top three cities but omitted the explicit `population_rank` output required by the task contract. This is classified as an instruction-adherence / semantic-result failure rather than an SQL execution failure.

This shared failure should remain visible in the baseline. Stage 2.3 does not tune the prompt to remove it.

### Qwen local inference reliability failures

Six Qwen cases ended with `LLM_TIMEOUT`:

- DA-001 — ranking
- DA-002 — ranking
- DA-017 — CTE
- DA-022 — filtering
- DA-028 — join
- DA-029 — join

The timeouts span multiple task categories, so the measured evidence supports treating them primarily as local inference reliability/latency failures rather than a single SQL-reasoning weakness.

### Qwen answer-generation failure — DA-027

The SQL/result path produced the expected cities and states, but the final answer contained the malformed entity `新 York`. The result therefore passed while answer/end-to-end semantic correctness failed.

This remains a real model output failure. The evaluator is not weakened with a one-off alias for this malformed entity.

### Safety behavior

Both models passed the unsafe-request case. The dangerous statement was stopped by the deterministic SQL validator before database execution.

Safety success remains independent of provider/model quality and is enforced by the deterministic boundary.

## Interpretation

### Model quality vs system reliability

Qwen's **91.7% completed-case semantic correctness** shows that successful local completions are generally strong. Its **73.3% all-case end-to-end semantic correctness** is much lower because six requests timed out.

This distinction must remain explicit:

```text
model/task quality != system reliability
```

### Latency

Latency is the strongest measured routing signal in the current setup:

```text
Groq / GPT-OSS: ~2.5 s average
Qwen / Ollama:  ~66 s average
```

The local path is therefore not currently equivalent to the hosted path for interactive UX.

### Cost and deployment properties

Qwen has zero measured API cost and supports local/private/offline operation. Groq incurred only a small measured API cost for the 30-case run while providing substantially better latency and completion reliability.

Cost alone is therefore not a sufficient routing signal. Routing must consider latency, availability, privacy/locality requirements, and reliability together.

### Exact SQL match

Exact SQL match remains diagnostic only. Qwen matched the reference SQL form more often than Groq, while Groq achieved stronger semantic/end-to-end outcomes. This reinforces the Stage 2.2 decision not to treat reference-form SQL equality as the primary quality metric.

## Reproducible comparison artifacts

Stage 2.3 adds:

```text
evaluation/compare_models.py
evaluation/results/stage2.3/model-comparison.json
evaluation/results/stage2.3/model-comparison.md
evaluation/results/stage2.3/failure-matrix.csv
```

Example:

```bash
python -m evaluation.compare_models \
  evaluation/results/stage2.2/evaluation-report-qwen3-8b-ollama-calibrated.json \
  evaluation/results/stage2.2/evaluation-report-groq-gpt-oss-20b-calibrated.json \
  --json-out evaluation/results/stage2.3/model-comparison.json \
  --md-out evaluation/results/stage2.3/model-comparison.md \
  --failures-out evaluation/results/stage2.3/failure-matrix.csv
```

## Evidence carried into Stage 2.4

Stage 2.3 does not implement a router. It establishes evidence for the next stage:

- **Hosted Groq path:** strongest evidence for latency-sensitive interactive requests.
- **Local Qwen path:** valuable when local/private/offline execution or zero API spend is prioritized.
- **Fallback/retry decisions:** should be based on measured failure modes and latency budgets, not model names alone.
- **Safety:** must remain deterministic and independent of routing.

## Exit status

Stage 2.3 is complete when:

- frozen Stage 2.2 reports are preserved;
- model metrics are compared reproducibly;
- failures are classified by model quality vs provider/runtime reliability;
- routing implications are documented without yet implementing routing.

All four conditions are satisfied by this package.

Next: **Stage 2.4 — Routing Policy**.
