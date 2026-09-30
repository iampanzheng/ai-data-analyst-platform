# Phase 2 — Stage 2.5 Reliability, Fallback & Cost Control

## Status

Implementation v1.0 complete; user-side full pytest and route/fallback smoke remain the final closeout checks.

## Goals

Stage 2.5 adds deterministic runtime reliability behavior on top of the frozen Stage 2.4 router without changing the Analyst Agent or SQL Validator security boundary.

## Fallback contract

Request fields:

- `routing_mode`: `auto | remote | local`
- `fallback_mode`: `auto | disabled | cross_route`

Policy:

- `auto` with measured default remote: remote primary, local fallback.
- explicit `remote`: remote primary, local fallback when fallback mode is `auto`.
- explicit `local`: local-only when fallback mode is `auto`; this preserves privacy intent.
- local -> remote is only allowed when caller explicitly selects `cross_route`.
- `disabled` prevents all cross-route fallback.

Fallback is allowed only for configured retryable provider failures. Default codes:

- `LLM_TIMEOUT`
- `LLM_CONNECTION_ERROR`
- `LLM_RATE_LIMIT`
- `LLM_SERVER_ERROR`

Authentication, request-shape, validation, SQL/security and other non-retryable failures do not trigger fallback.

## No duplicate SQL execution

Fallback is implemented at the `LLMClient.chat()` boundary rather than by rerunning `AnalystAgent.run()`.

Therefore:

1. SQL-generation provider failure can fallback before SQL exists.
2. Answer-generation provider failure can fallback after the query result already exists.
3. The SQL query is not rerun merely because the answer-generation provider failed.
4. Once fallback succeeds, the request sticks to the fallback route for subsequent LLM calls.

## Cost control

Provider pricing is configured per route:

- `LLM_REMOTE_INPUT_COST_PER_1M`
- `LLM_REMOTE_OUTPUT_COST_PER_1M`
- `LLM_LOCAL_INPUT_COST_PER_1M`
- `LLM_LOCAL_OUTPUT_COST_PER_1M`

Response telemetry includes route-level token usage and estimated request cost. `LLM_ROUTING_MAX_ESTIMATED_COST_USD` can stop a subsequent LLM call after accumulated known response usage reaches the configured budget. `0` disables this guard.

This is an estimate based on returned token usage; it is not a billing ledger and cannot account for provider work that failed before returning usage.

## Observability

`/api/analyze` now returns:

- `selected_route` — initial deterministic route
- `final_route` — route actually active when the request finished
- `fallback_mode`
- `fallback_route`
- `fallback_used`
- `fallback_events`
- `route_usage`
- `estimated_cost_usd`

Fallback events are also logged as `llm_fallback_used` with the request trace ID.

## Stage boundary

Stage 2.5 does not alter SQL validation, read-only execution, routing measurements, or the Stage 2.2 evaluator. Circuit breakers, persistent provider health scoring, and asynchronous retry queues are intentionally out of scope for this stage.
