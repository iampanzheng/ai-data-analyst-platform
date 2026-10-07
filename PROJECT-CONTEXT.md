# PROJECT-CONTEXT.md — P1 AI Data Analyst Platform

> Project-local source of truth for current implementation status and frozen engineering decisions.

# Current Status

```text
Phase 1 — MVP Foundation                         ✅ CLOSED
Phase 2 — Real LLM Evaluation / Routing / Cost  ✅ CLOSED
Phase 3 — Evidence-backed Analysis               ✅ CLOSED
Phase 4 — Production / Portfolio Readiness       🚧 ACTIVE

Stage 4.1 — Local Production Baseline            ✅ CLOSED
Stage 4.2 — Security / Configuration Cleanup       🚧 ACTIVE

Stage 3.1 — Evidence Foundation                  ✅ CLOSED
Stage 3.2 — Richer Analytical Data               ✅ CLOSED
Stage 3.3 — Controlled Python Analysis            ✅ CLOSED
Stage 3.4 — Controlled Visualization              ✅ CLOSED
Stage 3.5 — Controlled Reporting                  ✅ CLOSED
Stage 3.6 — Export / Deliverable Packaging        ✅ CLOSED
Stage 3.7 — Analyst Workspace / Frontend Polish   ✅ CLOSED
Stage 3.8 — End-to-End Acceptance & Regression    ✅ CLOSED
```

## Stage 3.1 verification

User-side Compose pytest passed at 100%, and `/api/schema` runtime smoke verified deterministic table evidence.

## Stage 3.2 implementation

The analytical fixture is no longer city-only. Stage 3.2 adds a curated source-backed five-city evidence set:

```text
city               15 rows / 2025 / place
education            5 rows / 2024 / ACS place
economic_indicator  10 rows / 2024 / ACS place
employment           5 rows / 2023 / OEWS metropolitan area
salary               5 rows / 2023 / OEWS metropolitan area
```

Key rules:

- OEWS records retain explicit metro geography (`geography_type`, `geography_name`).
- `city_id` on OEWS rows is an anchor, not a claim that the estimate is city-level.
- `salary.median_salary` is derived as OEWS median hourly wage × 2,080 and is explicitly documented as derived.
- existing Docker volumes receive idempotent schema + metadata upgrades through ETL.
- evaluation dataset `1.1-stage3.2` contains 35 cases; frozen Phase 2.2 reports remain 30-case historical baselines.

Packaging verification:

```text
compileall PASS
Stage 3.2 fixture tests: 2 passed
35-case dataset JSON Schema: PASS
```

User-side runtime verification completed:

```text
full Compose pytest: PASS (100%)
/api/schema evidence: PASS
salary join smoke: PASS — Los Angeles / 153566.40 / Los Angeles-Long Beach-Anaheim, CA
```

# Frozen Decisions

Do not redesign without new measured evidence:

1. SQL Validator is the deterministic database security boundary.
2. Routing remains deterministic and outside the LLM.
3. Explicit local mode remains privacy-safe by default.
4. Cross-route local→remote fallback requires explicit permission.
5. Provider fallback occurs at the LLM-call boundary, not by replaying the Agent.
6. Model quality and runtime reliability remain separate dimensions.
7. Statistical source year and geography grain must remain explicit evidence.
8. Phase 3 Python analysis must not introduce unrestricted arbitrary-code execution.

# Phase 3 Direction

```text
Stage 3.1 Evidence Foundation                 ✅
Stage 3.2 Richer Analytical Data                  ✅
Stage 3.3 Controlled Python Analysis              ✅
Stage 3.4 Controlled Visualization                ✅
Stage 3.5 Controlled Reporting                    ✅
Stage 3.6 Export / Deliverable Packaging          ✅
Stage 3.7 Analyst Workspace / Frontend Polish     ✅
Stage 3.8 End-to-End Acceptance & Regression      ✅
```


## Phase 3 closeout verification

Final Stage 3.8 acceptance completed on the integrated stack:

```text
FastAPI pytest: PASS (100%)
Frontend deterministic tests: 4/4 PASS
Frontend production build: PASS
Real-stack acceptance: 7/7 PASS
```

The final acceptance suite covers gateway health, unsafe SQL rejection, ranked query execution, controlled descriptive statistics, controlled visualization, evidence-bound report/delivery, and the full controlled analysis chain.

Phase 3 is CLOSED.

## Phase 4 current direction

```text
Stage 4.1 Local Production Baseline          ✅ CLOSED
Stage 4.2 Security / Configuration Cleanup   🚧 ACTIVE
Stage 4.3 Portfolio Documentation & Demo     planned
Stage 4.4 GitHub Repository & CI             planned
Stage 4.5 Deployment / Final Release         planned
```

Stage 4.1 is CLOSED. GitHub publication remains deferred until the repository, documentation, secret hygiene, and repeatable verification baseline are stable.

Stage 4.1 closeout establishes:

- `.dockerignore` build-context hygiene
- health-gated FastAPI → Gateway startup
- `make verify` as the deterministic local production gate
- host-side Python execution through `uv run python`
- committed `frontend/web/package-lock.json`
- Web Docker installs through `npm ci`
- safe `.env.example` coverage for current routing/fallback configuration

Final user-side verification completed on the locked dependency path:

```text
make verify                         PASS
FastAPI/Python regression suite    PASS (100%)
Frontend deterministic tests       PASS (4/4)
Frontend production build          PASS
Gateway /api/health                PASS
```

Stage 4.2 is now the active starting point.

Stage 4.1 v0.1.1 fixes host portability discovered during the first real `make verify` run: host-side Python execution is standardized on `uv run python` instead of assuming a `python` command exists. The Docker-container Python commands remain unchanged.

Stage 4.1 v0.1.2 adds the real frontend npm lockfile and changes the Web Docker build to `npm ci`. The remaining closeout gate is a fresh `make verify` using the locked dependency path.

## Stage 4.2 progress

Stage 4.2 v0.1 establishes the first security/configuration cleanup baseline without changing product behavior:

- published Compose ports bind to `127.0.0.1` by default instead of all host interfaces;
- PostgreSQL database/user/password and host ports are environment-configurable with explicitly local-development defaults;
- Gateway CORS and Web API base URL are environment-configurable;
- FastAPI `LOG_LEVEL` now affects logging configuration with safe fallback to INFO;
- structured JSON logs recursively redact sensitive keys such as API keys, passwords, authorization values, tokens, secrets, and database URLs;
- `scripts/security_check.py` provides deterministic configuration checks and is included in `make verify`;
- Stage 4.2 does not yet force non-root containers; that is deferred until ownership/test behavior is validated separately.

Current Stage 4.2 v0.1 deterministic checks: security configuration baseline PASS, logging redaction tests 3/3 PASS, Python compileall PASS. A full local `make verify` remains the candidate closeout gate.

---

# Historical context

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
analysis_result
chart_artifact
report_artifact
delivery_artifact
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

# Stage 3.3 — Controlled Python Analysis ✅ CLOSED

Goal: add bounded post-SQL numerical analysis while preserving deterministic execution control.

Final implementation baseline: `v0.1.3` hotfix, archived as the Stage 3.3 v1.0 closeout package. The hotfix corrected the `_sql_precomputes_controlled_analysis` raw-regex double-escaping regression introduced in v0.1.2.

Implemented:
- deterministic analysis-intent trigger for explicit correlation / percent-change / descriptive-statistics questions
- LLM emits JSON analysis plan only; no model-generated Python source is executed
- strict allowlist: `descriptive_stats`, `correlation`, `percent_change`
- max 1,000 input rows and max 3 operations
- strict column validation against verified SQL result
- numeric / finite-value checks and deterministic errors
- `analysis_result` carried through `AnalystState` and `/api/analyze`
- final-answer prompt may use verified SQL evidence plus controlled-analysis evidence
- deterministic guard prevents SQL from precomputing controlled statistics
- regression coverage includes correlation, descriptive aggregates / percentile, percent-change windows, and raw-row negative cases

Security invariant:
`LLM -> structured plan -> deterministic validator/executor`; never `LLM -> arbitrary Python -> exec`.

Final verification:
- Compose full pytest on v0.1.3: PASS, 100%
- remote correlation smoke: PASS; `pearson_r = 0.36675379037073685`, no fallback, no errors
- remote descriptive-statistics smoke: PASS; count/min/max/mean/median verified, no fallback, no errors
- v0.1.2 malformed-regex regression: CLOSED

# Stage 3.4 — Controlled Visualization ✅ CLOSED

Stage 3.4 is frozen on the verified v0.1.1 implementation and archived as the v1.0 closeout baseline.

Final verification:
- full Compose pytest: PASS, 100%
- remote bar-chart smoke: PASS; 5 verified points, no fallback, no errors
- combined correlation + scatter smoke: PASS; 5 rows, `pearson_r = 0.36675379037073685`, 5 scatter points, no fallback, no errors
- `education.education_level` exact-value grounding regression: CLOSED (`Bachelor's degree or higher`)
- frontend production build: PASS (`vite v8.3.1`, 15 modules transformed)

Security invariant remains `LLM -> structured chart plan -> deterministic validator -> chart artifact`; no executable plotting code is accepted.

# Stage 3.5 — Controlled Reporting ✅ CLOSED

Stage 3.5 is frozen on the verified v0.1 implementation and archived as the v1.0 closeout baseline.

Architecture:

```text
verified artifacts
→ JSON-only report selection plan
→ deterministic reference validation / assembler
→ report_artifact
→ React Report Panel / JSON export
```

Key controls:
- explicit report intent only
- report planner selects existing artifacts but does not write factual findings
- strict plan keys and bounded analysis-operation references
- deterministic key findings copied from controlled `analysis_result`
- chart references allowed only when a controlled `chart_artifact` exists
- extra/freeform payload keys rejected
- no HTML/Markdown/Python/JavaScript report execution

Final verification:
- Compose full pytest: PASS, 100%
- frontend production build: PASS (`vite v8.3.1`, 15 modules transformed)
- report-only remote smoke: PASS; 5 verified city rows, `report_artifact.source = verified_artifacts`, query evidence present, no fallback, no errors
- combined correlation + scatter + report smoke: PASS; 5 rows, `pearson_r = 0.36675379037073685`, scatter artifact present, report evidence bound to query/analysis/chart, no fallback, no errors
- deterministic report finding matched the controlled analysis value exactly

# Stage 3.6 — Export / Deliverable Packaging ✅ CLOSED

Stage 3.6 is frozen on the verified v0.1.2 implementation and archived as the v1.0 closeout baseline. It adds a deterministic delivery-packaging layer on top of verified Stage 3.5 artifacts and closes the evidence-boundary leak found during v0.1 closeout review.

Architecture:

```text
report_artifact + verified evidence
→ deterministic delivery packager
→ delivery_artifact
→ JSON / Markdown browser downloads
```

Implemented in v0.1/v0.1.2 candidate:
- no additional LLM call for export/delivery packaging
- packaging only allowed when `report_artifact.source = verified_artifacts`
- `delivery_artifact` added to Analyst state and `/api/analyze`
- versioned manifest (`p1.delivery.v1`)
- trace/question/validated-SQL provenance
- deterministic query evidence snapshot
- optional controlled analysis/chart snapshots
- deterministic Markdown renderer
- stable JSON/Markdown filenames
- React export actions for delivery JSON and Markdown
- delivery unit tests
- evidence-bound report summaries: `summary_source = deterministic_evidence`
- LLM `final_answer` remains top-level conversational output and is not copied into verified report/delivery summaries
- regression coverage prevents unsupported source-attribution text from entering verified summaries/Markdown exports
- reporting + delivery hotfix tests: 13/13 pass in packaging environment
- v0.1.2 aligns the stale Agent regression test with the deterministic-summary trust boundary; runtime behavior/API unchanged

Security invariant:
`verified artifacts -> deterministic packager -> inert JSON/Markdown`; no new factual source, model-authored export code, template execution, or arbitrary code execution.

v0.1 functional gates already verified:
- Compose full pytest: PASS, 100%
- frontend production build: PASS (`vite v8.3.1`, 15 modules transformed)
- report-only delivery smoke: PASS
- combined analysis + chart + report + delivery smoke: PASS

Final hotfix verification:
- full Compose pytest on v0.1.2: PASS, 100%
- frontend production build: PASS (`vite v8.3.1`, 15 modules transformed)
- report-only smoke: PASS; `summary_source = deterministic_evidence`, unsupported source attribution isolated to top-level LLM answer only
- combined correlation + scatter + report + delivery smoke: PASS; deterministic summary retained controlled analysis/chart evidence, no fallback, no errors

# Stage 3.7 — Analyst Workspace / Frontend Integration Polish ✅ CLOSED

Goal: consolidate the verified Answer / SQL / Query Result / Analysis / Chart / Report / Delivery / Provenance surfaces into a portfolio-ready analyst workspace without changing the backend artifact contracts.

Stage 3.7 is frontend-focused. The backend `/api/analyze` response contract and all Stage 3.1–3.6 trust boundaries remain frozen unless a concrete regression requires otherwise.

Stage 3.7 v0.1.1 presentation-polish candidate implements:
- portfolio-oriented hero + explicit trust-model summary
- responsive two-column analyst workspace
- sticky request/routing control panel
- answer execution-status strip (route, fallback, rows, latency, cost, trace)
- Data / Analysis / Chart / Report / Provenance workspace tabs
- progressive-disclosure manual SQL and schema browser
- deterministic delivery downloads retained in the Report tab
- no new frontend runtime dependency and no backend contract change

Closeout gates: full backend pytest, frontend production build, browser smoke for basic and full artifact flows, and delivery download verification.



## Stage 3.7 v0.1.1 presentation-polish update

Browser validation of v0.1 confirmed the five-tab workspace and Report JSON/Markdown downloads. The remaining presentation issues were raw Markdown in the LLM Answer and developer-oriented verified findings. v0.1.1 changes only the frontend:

- safe Markdown rendering for Answer
- human-readable verified findings and rounded display metrics
- Evidence-backed UI label for deterministic report summaries
- presentation summary separated from expandable technical evidence

Backend `/api/analyze`, report/delivery artifacts, export payloads, and Stage 3.1–3.6 trust boundaries remained unchanged. This was an intermediate v0.1.1 candidate before the final Stage 3.7 closeout.

## Stage 3.7 v0.1.2 visualization / presentation final-polish update

This frontend-only candidate follows the v0.1.1 browser review. It keeps `/api/analyze`, verified artifacts, exports, and all Stage 3.1–3.6 trust boundaries unchanged.

Changes:
- Data table presentation formats numeric values without changing raw query values; percentage-like columns render as percentages while years/IDs remain literal.
- Analysis cards map internal operation/field names to human-readable labels and preserve rounded display precision only at the UI layer.
- Controlled charts add readable axes, ticks, grid lines, human-friendly axis labels, and browser-native hover value inspection without inferring point labels absent from `chart_artifact`.
- Report presentation uses localized friendly field labels where the report title is Chinese; raw artifact fields remain unchanged.
- Provenance adds trace-ID copy affordance, presentation-friendly `Verified artifacts`, and manifest badges.
- The conversational Answer is explicitly labeled `LLM-generated`, preserving the visual distinction from verified artifacts.

This was an intermediate v0.1.2 candidate; the final v0.1.3 closeout verification is recorded below.

### Stage 3.7 v0.1.3 — Final Presentation Polish candidate

Final UI-only closeout pass:
- safe inline Markdown emphasis (`*italic*` / `_italic_`)
- rounded nice-scale chart domains/ticks
- localized presentation aliases for `bachelor_percent`-style fields

No backend/API/artifact contract changes. Final closeout verification subsequently passed and is recorded below.


## Stage 3.7 Closeout

Stage 3.7 is frozen on the verified v0.1.3 frontend implementation and archived as the v1.0 closeout baseline.

Final verification:
- backend regression suite: PASS
- frontend production build: PASS
- Data / Analysis / Chart / Report / Provenance browser regression: PASS
- Report JSON / Markdown downloads: PASS
- safe Markdown presentation, nice chart ticks, friendly report mappings: PASS
- no backend API or verified-artifact contract changes

# Stage 3.8 — End-to-End Acceptance & Regression 🚧 ACTIVE

Goal: verify the complete P1 product path with repeatable HTTP acceptance checks and deterministic frontend presentation tests before Phase 3 closeout. No new business capability is introduced.

Implemented in v0.1 candidate:
- HTTP acceptance runner using only Python standard library
- acceptance cases for health, SQL security, ranked query, controlled descriptive statistics, controlled visualization, evidence-bound report/delivery, and the full analysis chain
- JSON + Markdown acceptance reports
- frontend pure presentation helpers extracted for deterministic Node 22 tests
- frontend regression coverage for display formatting, friendly labels, nice chart scale, and safe inline Markdown emphasis
- no new frontend runtime dependency

Closeout gates:
1. full backend pytest
2. `npm test` frontend deterministic regression
3. frontend production build
4. real-stack acceptance suite (`python -m acceptance.run`)
5. review generated acceptance report and record known limitations


## Stage 3.8 v0.1.1 — FastAPI container packaging hotfix

The v0.1 candidate added `tests/test_acceptance.py`, which imports `acceptance.run`, but the FastAPI Docker image copied `tests/` without copying the new `acceptance/` package. In Compose this caused pytest collection to fail with `ModuleNotFoundError: No module named 'acceptance'`.

The FastAPI Dockerfile now includes:

```dockerfile
COPY acceptance /app/acceptance
```

No acceptance logic or runtime API behavior changed. The existing `tests/test_acceptance.py` import now also acts as a container-packaging regression check.

### Stage 3.8 v0.1.2 acceptance hardening

- Corrected the gateway health acceptance path from `/health` to `/api/health`.
- Stabilized ACC-004 around its intended descriptive-statistics contract by providing the exact stored occupation category `Software Developers`; synonym/category grounding is not the target of this acceptance case.
- Failed acceptance cases now persist a bounded diagnostic snapshot (trace, validated SQL, route/fallback, errors, row count/tables/columns, analysis operation names) without copying result rows or LLM prose.


Stage 4.2 v0.1.1 fixes a local-volume compatibility regression: PostgreSQL credentials remain environment-configurable, but the local default returns to `analyst` so existing `postgres_data` volumes continue to authenticate. Changing `POSTGRES_PASSWORD` is documented as a fresh-initialization setting, not an automatic password rotation for an existing PostgreSQL volume.
