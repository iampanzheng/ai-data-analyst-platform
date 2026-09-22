# P1 Phase 2 — Stage 2.1: Real LLM Integration

## Objective

Connect one real OpenAI-compatible model without changing the Analyst Agent orchestration or SQL security boundary, and make the model path reliable enough for measured evaluation.

## Implemented in Stage 2.1

- provider-independent `LLMClient` remains the model boundary
- OpenAI-compatible `/v1/chat/completions` provider retained
- token usage normalized at the LLM layer to:
  - `input_tokens`
  - `output_tokens`
  - `total_tokens`
- provider/model metadata propagated through `AnalystState` and `/api/analyze`
- structured LLM error categories:
  - `LLM_CONFIGURATION_ERROR`
  - `LLM_AUTH_ERROR`
  - `LLM_RATE_LIMIT`
  - `LLM_SERVER_ERROR`
  - `LLM_TIMEOUT`
  - `LLM_CONNECTION_ERROR`
  - `LLM_REQUEST_ERROR`
  - `LLM_INVALID_RESPONSE`
- bounded retry with exponential backoff only for retryable failures
- five-case real-model smoke runner: `python -m evaluation.smoke`
- existing SQL Validator remains mandatory between generated SQL and PostgreSQL

## Configuration

```env
LLM_PROVIDER=openai-compatible
LLM_BASE_URL=https://your-provider.example[/v1]
LLM_API_KEY=...
LLM_MODEL=...
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
LLM_RETRY_BACKOFF_SECONDS=0.5
LLM_INPUT_COST_PER_1M=0
LLM_OUTPUT_COST_PER_1M=0
```

Set the two cost rates to the provider's current model pricing before recording cost measurements. Do not hard-code provider pricing into application code.

## Smoke test

With PostgreSQL/FastAPI environment available and real-model variables configured:

```bash
docker compose exec fastapi python -m evaluation.smoke
```

The smoke set covers:

1. basic ranking
2. aggregation
3. filtering/sorting
4. grouping
5. unsafe DDL request

The unsafe case is considered safe only if the Agent does not produce a database query result and records an error. The SQL Validator remains the execution boundary regardless of model behavior.

## Exit criteria

Stage 2.1 is complete only after a real provider has been run and the five-case smoke test has been reviewed with actual:

- provider/model
- generated SQL
- SQL validation outcome
- database result
- final answer
- latency
- input/output/total tokens
- estimated cost
- structured errors

Do not start the full 30-case real-model baseline until this smoke path is stable.


### Stage 2.1A — first provider: local Ollama

The first real-model path is `qwen3:8b` through Ollama on the macOS host. See `docs/PHASE2-STAGE2.1A-OLLAMA.md` and `.env.ollama.example`. This intentionally exercises the same OpenAI-compatible adapter that will later be reused for cloud providers.
