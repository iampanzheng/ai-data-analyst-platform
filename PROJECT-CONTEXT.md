# PROJECT-CONTEXT.md — P1 AI Data Analyst Platform

> Project-local source of truth for implementation status, architecture, measured results, verification state, frozen decisions, and next starting point.

# 1. Current Status

```text
Phase 1 — MVP Foundation                         ✅ CLOSED
Phase 2 — Real LLM Evaluation / Routing / Cost  ✅ CLOSED
```

Phase 2 stages:

```text
Stage 2.1 — Real LLM Integration                 ✅
Stage 2.2 — Calibrated Multi-model Baseline      ✅
Stage 2.3 — Model Comparison / Failure Analysis  ✅
Stage 2.4 — Deterministic Routing                ✅
Stage 2.5 — Reliability / Fallback / Cost        ✅
Stage 2.6 — Evaluation & Closeout                ✅
```

Do not redesign completed Phase 1–2 architecture without new measured evidence.

# 2. Core Architecture

```text
React
  ↓
Spring Boot Gateway
  ↓
FastAPI
  ↓
Deterministic Router
  ├── remote: Groq / GPT-OSS 20B
  └── local:  Ollama / Qwen3 8B
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
LLM SQL candidate
  ↓
SQL Validator
  ↓
read-only PostgreSQL
  ↓
Query Result
  ↓
LLM final answer
```

Core principle:

```text
request → validate → execute → evidence
```

LLM-generated SQL is untrusted. The SQL Validator remains the execution security boundary.

# 3. Routing / Fallback Contract

```text
routing_mode=auto   → remote
routing_mode=remote → remote
routing_mode=local  → local
```

```text
remote + fallback_mode=auto
→ retryable provider failure may fallback to local

local + fallback_mode=auto
→ remains local; never silently sends data remote

local + fallback_mode=cross_route
→ explicit permission for local → remote fallback

fallback_mode=disabled
→ no cross-route fallback
```

Retryable fallback classes:

```text
LLM_TIMEOUT
LLM_CONNECTION_ERROR
LLM_RATE_LIMIT
LLM_SERVER_ERROR
```

Authentication/configuration and SQL-security errors do not trigger provider fallback.

# 4. Frozen Stage 2.2 Baselines

## Groq / GPT-OSS 20B

```text
cases                         30
completed                     30/30
semantic result               28/29  (96.55%)
answer correctness            29/29  (100%)
safety                        1/1    (100%)
end-to-end semantic           29/30  (96.67%)
avg latency                   2.527 s
p95 latency                   2.944 s
tokens                        74,202
estimated cost                $0.0064746
provider/runtime failures     0
```

Known semantic failure: DA-020 omitted explicit rank output.

## Ollama / Qwen3 8B

```text
cases                         30
completed                     24/30
semantic result               22/29  (75.86%)
answer correctness            22/29  (75.86%)
safety                        1/1    (100%)
end-to-end semantic           22/30  (73.33%)
completed-case semantic       22/24  (91.67%)
avg completed latency         65.955 s
p95 completed latency         116.302 s
tokens                        74,788
estimated API cost            $0
provider/runtime failures     6 LLM_TIMEOUT
```

Interpretation:

- Qwen completed-case quality is high;
- its main measured weakness is local latency/reliability;
- DA-020 is a shared rank-output adherence failure;
- DA-027 includes a final-answer entity-generation defect (`新 York`).

# 5. Evaluator State

The calibrated evaluator is frozen for Phase 2 comparison.

Primary metrics:

- Semantic Result Correctness
- Answer Correctness
- End-to-End Semantic Correctness
- Safety Correctness
- completion/reliability
- latency
- token usage
- estimated cost

`Exact SQL Match` is diagnostic only.

# 6. Verification State

User-side verification completed.

## Stage 2.4

- full pytest: PASS
- curl route smoke: PASS
- browser route smoke: PASS
- `auto → remote`: PASS
- `remote → remote`: PASS
- `local → local`: PASS

## Stage 2.5

- full pytest: PASS
- remote AUTH error + auto: no fallback — PASS
- remote connection error + auto: remote → local — PASS
- local connection error + auto: no remote fallback — PASS
- local connection error + cross_route: local → remote — PASS
- fallback metadata — PASS
- route usage accounting — PASS
- estimated remote cost — PASS

# 7. Frozen Engineering Decisions

1. Keep one Analyst Agent until evaluation demonstrates a concrete need for more orchestration.
2. SQL Validator remains the deterministic database security boundary.
3. Metadata knowledge and execution policy remain separate.
4. Model providers stay behind `LLMClient`.
5. Routing remains deterministic and outside the LLM.
6. `auto` uses the measured remote interactive default.
7. Explicit local mode is privacy-safe by default.
8. Local→remote fallback requires explicit `cross_route` permission.
9. Fallback happens at the LLM-call boundary, not by replaying the whole Agent.
10. Model quality and system reliability are measured separately.
11. Exact SQL equality is not the primary correctness measure.
12. Provider failure is not a successful security rejection.

# 8. Current API Observability

`POST /api/analyze` includes:

```text
routing_mode
selected_route
final_route
routing_reason
fallback_mode
fallback_route
fallback_used
fallback_events
route_usage
estimated_cost_usd
sql_candidate
validated_sql
query_result
final_answer
model
provider
usage
errors
trace_id
```

# 9. Phase 3 Starting Point

Phase 2 is closed. Phase 3 should extend analysis capability rather than revisit routing/security fundamentals.

Recommended direction:

```text
richer datasets / metadata
→ stronger evidence interpretation
→ controlled Python analysis capability
→ visualization
→ report-quality evidence packaging
```

Before implementation:

1. define the Phase 3 product objective;
2. define measurable acceptance criteria;
3. define deterministic execution policy for any Python/analysis tool;
4. preserve the existing SQL security and routing/fallback contracts.

Do not introduce unrestricted arbitrary Python execution.
