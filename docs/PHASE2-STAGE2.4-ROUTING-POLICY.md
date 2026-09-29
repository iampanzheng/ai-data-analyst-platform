# Phase 2 — Stage 2.4 Routing Policy

Status: **IMPLEMENTED — USER VERIFICATION PENDING**

## Goal

Convert Stage 2.3 measured model evidence into a deterministic, explainable routing layer without changing the Analyst Agent, SQL validator, database security boundary, or frozen Stage 2.2 evaluator.

## Evidence used

The frozen Stage 2.2 / Stage 2.3 comparison showed:

- Groq / GPT-OSS 20B: 30/30 completed, 96.7% end-to-end semantic correctness, 2.527s average latency, 2.944s p95.
- Ollama / Qwen3 8B: 24/30 completed, 91.7% semantic correctness on completed cases, 65.955s average completed-case latency, six LLM timeouts, zero API cost.
- Both models passed the unsafe-request validation case.

The measured evidence supports a remote interactive default while preserving local inference as an explicit privacy/offline/$0-API-cost option.

## Policy v1

The router is deterministic and runs before `AnalystAgent` construction.

| Request mode | Selected route | Reason |
|---|---|---|
| `auto` | configured default (`remote` in the Stage 2.4 example) | measured Stage 2.3 production-oriented default |
| `remote` | remote | explicit caller request |
| `local` | local | explicit caller request |

The LLM never decides which LLM to use.

No query-complexity heuristic is introduced in v1 because Stage 2.3 did not provide evidence that a category-based split would outperform the measured remote default.

## No automatic fallback yet

Stage 2.4 intentionally does **not** retry a failed local request on remote or vice versa. Automatic fallback changes reliability, privacy, cost, and observability semantics and is reserved for Stage 2.5.

`RouteDecision.fallback_route` is therefore `None` in this stage.

## Backward compatibility

`LLM_ROUTING_ENABLED=false` preserves the original single-provider `LLM_*` path for `routing_mode=auto`.

Explicit `local` or `remote` requests while routing is disabled fail with `LLM_ROUTING_DISABLED`; the application does not silently ignore an explicit routing choice.

## Multi-provider configuration

Routing-enabled deployments use separate environment prefixes:

- `LLM_REMOTE_*`
- `LLM_LOCAL_*`

This allows Groq and Ollama to coexist in one FastAPI process without mutating global environment variables per request.

Model-specific prompt behavior is also separated. `LLM_LOCAL_DISABLE_THINKING=true` can add `/no_think` for Qwen while `LLM_REMOTE_DISABLE_THINKING=false` leaves the Groq prompt unchanged.

See `.env.routing.example`.

## API contract

`POST /api/analyze` accepts:

```json
{
  "question": "人口最多的 5 个城市是哪几个？",
  "routing_mode": "auto"
}
```

Allowed modes are `auto`, `remote`, and `local`.

The response adds:

```json
{
  "routing_mode": "auto",
  "selected_route": "remote",
  "routing_reason": "auto_default_remote_stage2_3_measurements"
}
```

The Spring gateway forwards its camelCase `routingMode` request field to FastAPI's `routing_mode`. The React demo exposes the three routing choices.

## Observability

FastAPI emits an `llm_route_selected` structured log event containing:

- trace ID
- requested routing mode
- selected route
- routing reason

The actual response still records the model/provider returned by the selected LLM client.

## Files introduced / changed

- `ai/analyst/app/llm/routing.py`
- `ai/analyst/app/llm/client.py`
- `ai/analyst/app/agent/prompts.py`
- `ai/analyst/app/agent/graph.py`
- `ai/analyst/app/main.py`
- `.env.routing.example`
- `docker-compose.yml`
- Spring gateway analyze request/proxy code
- React route selector
- `tests/test_routing.py`
- Spring JSON serialization regression test
- `evaluation/results/stage2.4/routing-policy.json`

## Verification

Packaging environment verification:

- Python compilation: PASS
- `tests/test_routing.py`: 8 passed
- Full project pytest: not runnable in the packaging sandbox because `sqlglot` / `psycopg` are unavailable there.
- Maven tests: not runnable in the packaging sandbox because Maven / mvnw are unavailable there.

Developer verification before Stage 2.4 closeout:

```bash
uv run pytest -q

docker compose exec fastapi pytest -q
```

If the Java gateway image is rebuilt, also verify its Maven tests through the normal project build environment.

## Exit criteria

Stage 2.4 can close when:

1. full Python tests pass,
2. routing-disabled legacy behavior remains compatible,
3. `auto` selects remote under routing-enabled example configuration,
4. explicit `local` selects Ollama/Qwen,
5. explicit `remote` selects Groq/GPT-OSS,
6. route metadata is visible in API responses/logs,
7. no automatic cross-provider fallback occurs.

Next: **Stage 2.5 — Reliability, Fallback & Cost Control**.
