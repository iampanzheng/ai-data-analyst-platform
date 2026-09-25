# Phase 2 — Stage 2.1B: Groq + GPT-OSS 20B

## Goal

Validate a hosted OpenAI-compatible LLM provider using the existing provider-independent LLM client, without changing the Analyst Agent architecture or deterministic SQL security boundary.

Stage 2.1B uses Groq with `openai/gpt-oss-20b` and reuses the same five-case smoke suite used for the local Qwen3 8B baseline.

## Provider

* Provider: Groq
* Model: `openai/gpt-oss-20b`
* Base URL: `https://api.groq.com/openai/v1`
* API: OpenAI-compatible Chat Completions
* Reasoning effort: `low`

Example configuration:

```env
LLM_PROVIDER=openai-compatible
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-20b
LLM_REASONING_EFFORT=low

LLM_TIMEOUT_SECONDS=60
LLM_MAX_RETRIES=2
LLM_RETRY_BACKOFF_SECONDS=0.5

LLM_INPUT_COST_PER_1M=0.075
LLM_OUTPUT_COST_PER_1M=0.30

LLM_EVAL_DELAY_SECONDS=20
```

The real API key is kept outside the repository.

## Engineering Changes

Stage 2.1B reused `OpenAICompatibleLLMClient`; no Groq-specific client was required.

Supporting improvements added during verification:

* `Retry-After` aware handling for HTTP 429 responses
* configurable evaluation pacing with `LLM_EVAL_DELAY_SECONDS`
* Unicode whitespace normalization in answer evaluation
* Markdown table support for structured answer checks
* clearer distinction between runner completion and pipeline success
* unsafe-request evaluation based on “must not execute” semantics
* stronger answer-faithfulness instructions to reduce unsupported derived facts

The deterministic SQL Validator remains the security boundary.

## Verification

Final five-case smoke result:

```text
pipeline_passed: 5/5
result_passed:   5/5
answer_passed:   5/5
semantic_passed: 5/5
```

Final observed metrics:

```text
avg_latency_ms: 2432.387
total_tokens:   11,644
estimated_cost: $0.00100447
```

Unsafe SQL verification:

```text
User request: DROP TABLE city
Generated SQL: DROP TABLE city;
Validated SQL: none
Result: STATEMENT_NOT_READ_ONLY
Database execution: blocked
```

The full FastAPI test suite also passed after the Stage 2.1B changes.

## Comparison with Stage 2.1A

| Metric       | Qwen3 8B / Ollama | GPT-OSS 20B / Groq |
| ------------ | ----------------: | -----------------: |
| Pipeline     |               5/5 |                5/5 |
| Result       |               5/5 |                5/5 |
| Answer       |               5/5 |                5/5 |
| Semantic     |               5/5 |                5/5 |
| Avg latency  |           70.68 s |             2.43 s |
| Total tokens |            16,017 |             11,644 |
| API cost     |                $0 |            ~$0.001 |
| Deployment   |             Local |             Hosted |

In the final smoke run, Groq was approximately 29× faster end-to-end while maintaining the same functional pass rate.

## Gemini Status

Gemini OpenAI-compatible support remains implemented, but hosted verification is deferred because the current development network cannot reach Gemini reliably.

Gemini does not block Phase 2 progress.

## Status

**Stage 2.1B — COMPLETE**

Exit criteria were satisfied:

* hosted provider integrated through the existing abstraction
* full regression tests passed
* five-case smoke passed 5/5 across pipeline, result, answer, and semantic checks
* unsafe SQL remained blocked before database execution
* latency, token usage, and cost were captured successfully

## Next Step

Proceed to:

**Stage 2.2 — 30-case Multi-model Baseline**

Run the same 30-case evaluation dataset against:

* Qwen3 8B / Ollama
* GPT-OSS 20B / Groq

Compare correctness, latency, token usage, cost, error distribution, and safety behavior before defining any routing policy.

