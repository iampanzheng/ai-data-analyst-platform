# Phase 2 — Stage 2.3 Model Comparison

Source: Stage 2.2 frozen calibrated 30-case baselines.

## Measured comparison

| Metric | qwen3:8b | openai/gpt-oss-20b |
|---|---:|---:|
| Cases | 30 | 30 |
| Completed | 24/30 (80.0%) | 30/30 (100.0%) |
| Semantic result | 22/29 (75.86%) | 28/29 (96.55%) |
| Answer | 22/29 (75.86%) | 29/29 (100.0%) |
| Safety | 1/1 (100.0%) | 1/1 (100.0%) |
| End-to-end semantic (all cases) | 22/30 (73.33%) | 29/30 (96.67%) |
| End-to-end semantic (completed) | 22/24 (91.67%) | 29/30 (96.67%) |
| Avg latency | 65.955s | 2.527s |
| P95 latency | 116.302s | 2.944s |
| Input tokens | 52,930 | 70,160 |
| Output tokens | 21,858 | 4,042 |
| Total tokens | 74,788 | 74,202 |
| Estimated API cost | $0.00000000 | $0.00647460 |
| Provider/runtime failures | 6 | 0 |

## Derived signals

- **Latency:** `openai/gpt-oss-20b` was approximately **26.1× faster** than `qwen3:8b` by measured average completed-case latency.
- **Output-token footprint:** `qwen3:8b` produced approximately **5.41×** as many output tokens as `openai/gpt-oss-20b`.

## Failure taxonomy

| Model | Case | Category | Classification | Error | Semantic reason |
|---|---|---|---|---|---|
| qwen3:8b | DA-001 | ranking | provider_or_runtime_failure | LLM_TIMEOUT | result: no database result was produced |
| qwen3:8b | DA-002 | ranking | provider_or_runtime_failure | LLM_TIMEOUT | result: no database result was produced |
| qwen3:8b | DA-017 | CTE | provider_or_runtime_failure | LLM_TIMEOUT | result: no database result was produced |
| qwen3:8b | DA-020 | window | semantic_result_or_instruction_failure |  | result: actual result is missing required semantic columns: ['population_rank'] |
| qwen3:8b | DA-022 | filtering | provider_or_runtime_failure | LLM_TIMEOUT | result: no database result was produced |
| qwen3:8b | DA-027 | filtering | answer_generation_failure |  | answer: answer is missing one or more expected entities |
| qwen3:8b | DA-028 | joins | provider_or_runtime_failure | LLM_TIMEOUT | result: no database result was produced |
| qwen3:8b | DA-029 | joins | provider_or_runtime_failure | LLM_TIMEOUT | result: no database result was produced |
| openai/gpt-oss-20b | DA-020 | window | semantic_result_or_instruction_failure |  | result: actual result is missing required semantic columns: ['population_rank'] |

## Interpretation

- **Model quality and system reliability must remain separate.** Qwen3 8B retained high completed-case semantic correctness, but six local inference timeouts reduced end-to-end reliability.
- **Latency is the strongest measured routing signal.** The hosted Groq path remained in the low-single-digit-second range while the local Qwen path was around a minute on average in this setup.
- **DA-020 is a shared instruction-adherence weakness.** Both models produced the correct top three cities but omitted the explicit rank output required by the evaluation contract.
- **Qwen DA-027 is an answer-generation quality failure.** The result was accepted, but the final answer contained the malformed entity `新 York`; this remains a real failure rather than an evaluator exception.
- **Exact SQL match remains diagnostic only.** Qwen matched the reference form more often, while Groq achieved stronger semantic correctness; reference-form agreement is therefore not a suitable primary quality metric.

## Stage 2.4 evidence boundary

This stage does **not** implement routing. It records evidence for a deterministic Stage 2.4 policy:

- hosted Groq path for latency-sensitive interactive requests;
- local Qwen path when privacy/offline operation or zero API spend is prioritized;
- future fallback behavior should be justified by reliability measurements rather than model branding.
