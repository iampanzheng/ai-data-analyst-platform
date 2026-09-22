# P1 Phase 2 — Stage 2.1A: Ollama + Qwen3 8B

## Objective

Use a local Qwen3 8B model through Ollama as the first real-model baseline while preserving the existing `LLMClient`, Analyst Agent orchestration, SQL Validator, PostgreSQL execution path, and evaluation harness.

## Why this model

The first local baseline is `qwen3:8b`. The official Ollama tag is approximately 5.2 GB (Q4_K_M), which is a reasonable starting point for a 16 GB Apple Silicon development machine while Docker/PostgreSQL/IDE are also running.

## macOS setup

Install and launch the current Ollama macOS application, then pull the model:

```bash
ollama pull qwen3:8b
ollama list
```

Verify Ollama on the Mac host before involving Docker:

```bash
curl http://localhost:11434/api/tags
ollama run qwen3:8b "只回答 OK"
```

For Apple Silicon development, run Ollama on the macOS host rather than inside the project Docker Compose stack so local acceleration remains available.

## Project configuration

Copy `.env.ollama.example` values into `.env`:

```env
LLM_PROVIDER=openai-compatible
LLM_BASE_URL=http://host.docker.internal:11434
LLM_API_KEY=ollama
LLM_MODEL=qwen3:8b
LLM_TIMEOUT_SECONDS=120
LLM_MAX_RETRIES=1
LLM_RETRY_BACKOFF_SECONDS=0.5
LLM_INPUT_COST_PER_1M=0
LLM_OUTPUT_COST_PER_1M=0
```

`LLM_BASE_URL` may be configured either as the provider root (`...:11434`) or with a trailing `/v1`; the client normalizes both to the same `/v1/chat/completions` endpoint.

The API key is not used by a default local Ollama server, but a non-secret placeholder is acceptable. Local API cost is recorded as zero; electricity/hardware cost is intentionally outside the current request-cost metric.

## Docker-to-host connectivity

After configuring `.env`, rebuild/recreate FastAPI so the environment is applied:

```bash
docker compose up --build -d
```

Verify from inside the FastAPI container:

```bash
docker compose exec fastapi python - <<'PY'
import httpx
r = httpx.get("http://host.docker.internal:11434/api/tags", timeout=10)
print(r.status_code)
print(r.json())
PY
```

Expected: HTTP 200 and `qwen3:8b` present in the returned model list.

## Regression before real-model smoke

```bash
docker compose exec fastapi pytest -q
```

Do not continue if the existing deterministic suite regresses.

## Five-case real-model smoke

```bash
docker compose exec fastapi python -m evaluation.smoke
# or
make smoke-docker
```

The five cases cover ranking, aggregation, filtering/sorting, grouping, and an unsafe `DROP TABLE` request.

For the unsafe case, success means the request is stopped by the deterministic SQL security boundary and no database query result is produced.

## What to record

For every case review:

- provider and model
- generated SQL
- validated SQL or validation error
- result row count
- final answer
- end-to-end latency
- normalized input/output/total token usage
- estimated API cost (zero for this local baseline)
- structured error code, if any

## Important interpretation

This stage is a connectivity and end-to-end behavior smoke test, not the 30-case model-quality baseline. A five-case pass means the local model path is operational and safe enough to proceed to Stage 2.2; it does not establish overall model accuracy.

## Exit criterion

```text
Ollama host reachable from FastAPI container
→ qwen3:8b loaded
→ existing pytest suite passes
→ 5-case smoke completes
→ generated SQL/security/result/answer/latency/tokens reviewed
```
