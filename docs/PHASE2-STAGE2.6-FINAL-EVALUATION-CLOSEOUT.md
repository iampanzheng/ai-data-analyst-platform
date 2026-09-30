# Phase 2 — Final Evaluation & Closeout

Status: **CLOSED**

Phase 2 extended the Phase 1 Analyst Agent without redesigning the established SQL-security architecture. The final system now supports real LLM providers, calibrated evaluation, measured model comparison, deterministic routing, privacy-aware fallback, route-level usage/cost telemetry, and runtime fallback observability.

## Stage closeout

- Stage 2.1 — Real LLM Integration: complete
- Stage 2.2 — Calibrated Multi-model Baseline: complete
- Stage 2.3 — Model Comparison & Failure Analysis: complete
- Stage 2.4 — Deterministic Routing: complete
- Stage 2.5 — Reliability, Fallback & Cost Control: complete
- Stage 2.6 — Evaluation & Closeout: complete

## Frozen model baselines

### Groq / GPT-OSS 20B

| Metric | Result |
|---|---:|
| Cases | 30 |
| Completed | 30 / 30 |
| Semantic result correctness | 28 / 29 (96.55%) |
| Answer correctness | 29 / 29 (100%) |
| Safety correctness | 1 / 1 (100%) |
| End-to-end semantic correctness | 29 / 30 (96.67%) |
| Average latency | 2.527 s |
| P95 latency | 2.944 s |
| Total tokens | 74,202 |
| Estimated API cost | $0.0064746 |
| Provider/runtime failures | 0 |

Known semantic failure: DA-020 returned the correct top-three cities but omitted the explicit rank output required by the task.

### Ollama / Qwen3 8B

| Metric | Result |
|---|---:|
| Cases | 30 |
| Completed | 24 / 30 |
| Semantic result correctness | 22 / 29 (75.86%) |
| Answer correctness | 22 / 29 (75.86%) |
| Safety correctness | 1 / 1 (100%) |
| End-to-end semantic correctness | 22 / 30 (73.33%) |
| Completed-case semantic correctness | 22 / 24 (91.67%) |
| Average completed-case latency | 65.955 s |
| P95 completed-case latency | 116.302 s |
| Total tokens | 74,788 |
| Estimated API cost | $0 |
| Provider/runtime failures | 6 LLM timeouts |

Failure interpretation:

- six failures were local inference timeouts rather than demonstrated SQL-reasoning failures;
- DA-020 matched the shared rank-output adherence weakness;
- DA-027 had a final-answer entity-generation defect (`新 York`) even though the result set was correct.

## Final routing contract

```text
routing_mode=auto   → remote
routing_mode=remote → remote
routing_mode=local  → local
```

Routing remains deterministic and outside the LLM.

## Final fallback contract

Retryable provider failures:

```text
LLM_TIMEOUT
LLM_CONNECTION_ERROR
LLM_RATE_LIMIT
LLM_SERVER_ERROR
```

Non-fallback examples:

```text
LLM_AUTH_ERROR
LLM_REQUEST_ERROR
SQL validation/security rejection
```

Privacy behavior:

```text
local + fallback_mode=auto
→ no automatic remote fallback

local + fallback_mode=cross_route
→ explicit permission for local → remote fallback
```

Fallback occurs at the LLM-call boundary rather than by replaying the whole Agent, preventing duplicate SQL execution when answer generation fails.

## Runtime acceptance evidence

### Stage 2.4

User-side verification:

- full project pytest: PASS
- curl route smoke: PASS
- browser route smoke: PASS
- `auto → remote`: PASS
- `remote → remote`: PASS
- `local → local`: PASS

### Stage 2.5

User-side verification:

- full project pytest: PASS

Real fallback smoke:

| Scenario | Result |
|---|---|
| remote + auth error + auto | PASS — no fallback |
| remote + connection error + auto | PASS — fallback to local |
| local + connection error + auto | PASS — remained local / privacy-safe |
| local + connection error + cross_route | PASS — fallback to remote |
| fallback metadata | PASS |
| route usage accounting | PASS |
| remote estimated-cost telemetry | PASS |

Observed telemetry matched the contract for `selected_route`, `final_route`, `fallback_used`, `fallback_events`, `route_usage`, and `estimated_cost_usd`.

## Final architecture

```text
React
  ↓
Spring Boot Gateway
  ↓
FastAPI /api/analyze
  ↓
Deterministic Route Selection
  ├── remote / Groq GPT-OSS 20B
  └── local  / Ollama Qwen3 8B
  ↓
Resilient LLM Client
  ├── bounded provider retry
  ├── privacy-aware fallback
  ├── sticky fallback
  └── usage / estimated-cost telemetry
  ↓
Analyst Agent v0.1
  ↓
Schema Tool
  ↓
LLM SQL generation
  ↓
SQL Validator  ← deterministic security boundary
  ↓
Read-only PostgreSQL
  ↓
Query evidence
  ↓
LLM answer generation
```

The SQL Validator remains unchanged as the database execution security boundary. Routing and fallback do not authorize unsafe SQL.

## Acceptance decision

Phase 2 acceptance criteria are satisfied:

- real providers operate behind the provider-independent abstraction;
- real-model performance is measured on a common calibrated evaluator;
- model quality and system reliability are separated;
- deterministic routing is implemented and runtime-verified;
- privacy-safe fallback is implemented and runtime-verified;
- route usage and estimated cost are observable;
- unsafe SQL remains blocked by deterministic validation;
- the final user-side regression suite is green.

> **Phase 2 — Real LLM Evaluation, Routing & Cost Control: CLOSED**

## Frozen decisions

Do not redesign these without new measured evidence:

1. SQL Validator remains the security boundary.
2. Routing remains deterministic and outside the LLM.
3. `auto` defaults to the measured remote interactive path.
4. Explicit local mode is privacy-safe by default.
5. Local→remote fallback requires explicit `cross_route` permission.
6. Provider fallback occurs at the LLM-call boundary, not by rerunning the complete Agent.
7. Exact SQL Match remains diagnostic rather than the primary correctness metric.
8. Model quality and runtime reliability remain separate evaluation dimensions.
9. Provider failure is not treated as successful security rejection.

## Phase 3 starting point

Phase 3 should extend analysis capability rather than revisit the closed routing/security fundamentals.

Recommended direction:

```text
richer datasets / metadata
→ stronger evidence interpretation
→ controlled Python analysis capability
→ visualization / chart generation
→ report-quality evidence packaging
```

Before implementation, define the Phase 3 product objective and measurable acceptance criteria. Do not introduce unrestricted arbitrary Python execution; any analysis tool must have an explicit execution policy and deterministic safety boundary.
