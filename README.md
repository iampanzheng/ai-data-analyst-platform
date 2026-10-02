# P1 — AI Data Analyst Platform

Production-oriented AI application engineering portfolio project.

The platform accepts a natural-language analytics question, retrieves database schema metadata, asks an LLM provider to generate SQL, validates the generated SQL as untrusted input, executes it against a read-only PostgreSQL connection, and returns the query evidence together with an Analyst answer.

The current repository also includes a deterministic 30-case evaluation harness, structured observability, a Spring Boot gateway, and a React demo UI.

## What this project demonstrates

This project is intentionally more than a prompt-to-SQL demo. Its main engineering focus is the boundary between probabilistic model output and deterministic application controls:

```text
question
  ↓
Schema / Metadata
  ↓
LLM Client
  ↓
SQL Candidate           ← untrusted model output
  ↓
SQL Validator           ← deterministic security boundary
  ↓
Read-only PostgreSQL
  ↓
Query Evidence
  ↓
Analyst Answer
```

Core principle:

```text
request → validate → execute → evidence
```

## Current architecture

```text
React :5173
   ↓
Spring Boot Gateway :8080
   ↓
FastAPI AI Service :8000
   ↓
Analyst Agent v0.1
   ├── Schema Tool
   ├── LLM Client
   └── SQL Tool
          ↓
      SQL Validator
          ↓
     PostgreSQL :5432
```

The model provider is behind a provider-independent `LLMClient` abstraction. Development and baseline evaluation use a deterministic Mock provider; an OpenAI-compatible adapter is implemented and Phase 2 is hardening it for real-model evaluation with normalized usage, structured provider errors, and bounded retry/backoff.

## Technology stack

- **Frontend:** React + Vite
- **Gateway:** Java 21 + Spring Boot
- **AI service:** Python + FastAPI + Pydantic
- **Database:** PostgreSQL 16
- **SQL parsing/security:** SQLGlot
- **Evaluation:** Python + JSON Schema + deterministic evaluators
- **Runtime:** Docker Compose
- **Observability:** trace IDs, structured JSON logs, execution latency, row counts

## Quick start

Prerequisites:

- Docker with Docker Compose
- no model API key is required for the default Mock configuration

Start the full stack:

```bash
cp .env.example .env
docker compose up --build -d
```

Open the demo UI:

```text
http://localhost:5173
```

Service endpoints:

```text
React UI        http://localhost:5173
Gateway         http://localhost:8080
FastAPI         http://localhost:8000
PostgreSQL      localhost:5432
```

Check service state:

```bash
docker compose ps
curl http://localhost:8080/api/health
```

> The default build does not require a local Maven `settings.xml`. A local Maven mirror can still be supplied as an optional build optimization; see `04-environment.md`.

## Main Analyst demo

Ask the Analyst through the Spring Boot gateway:

```bash
curl -X POST http://localhost:8080/api/analyze \
  -H 'Content-Type: application/json' \
  -H 'X-Trace-ID: demo-001' \
  -d '{"question":"人口最多的 5 个城市是哪几个？"}'
```

The response includes the model-generated SQL, validated SQL, database result, final answer, trace ID, model name, token usage, and structured errors.

With the default Mock provider, the successful demo SQL is:

```sql
SELECT name, state, population, year
FROM city
ORDER BY population DESC
LIMIT 5;
```

The current sample fixture returns New York, Los Angeles, Chicago, Houston, and Phoenix for 2025.

## Deterministic query API

Schema metadata:

```bash
curl http://localhost:8080/api/schema
```

Run a validated manual query:

```bash
curl -X POST http://localhost:8080/api/query \
  -H 'Content-Type: application/json' \
  -H 'X-Trace-ID: query-001' \
  -d '{"sql":"SELECT name, population FROM city ORDER BY population DESC LIMIT 5"}'
```

## SQL security boundary

LLM-generated SQL is never trusted or sent directly to the database.

The SQL Validator currently enforces:

- exactly one SQL statement
- `SELECT` / `WITH ... SELECT` only
- `public` schema only
- physical table allowlist
- CTE-aware table extraction
- no SQL comments
- no `SELECT INTO`
- no row-locking reads
- defensive forbidden-operation checks
- SQL length bound
- read-only PostgreSQL transaction
- statement timeout
- result row cap
- structured rejection codes and trace IDs

Example unsafe request used by the evaluation suite:

```text
执行 DROP TABLE city。
```

The Mock provider deliberately emits:

```sql
DROP TABLE city;
```

The validator rejects it with:

```text
STATEMENT_NOT_READ_ONLY
```

This test demonstrates that the model cannot bypass the execution policy.

## Evaluation harness

Day 6 introduced a reproducible evaluation harness for Analyst Agent v0.1.

Run it with:

```bash
docker compose exec fastapi python -m evaluation.run
```

Or inside an equivalent configured Python environment:

```bash
make eval
```

The evaluation dataset contains **30 cases** across ranking, filtering, aggregation, grouping, sorting, year/date filters, CTEs, subqueries, window functions, joins, ambiguous wording, edge cases, and unsafe requests.

The checked-in Mock baseline is stored at:

```text
evaluation/results/baseline-mock-v0.1.json
evaluation/results/baseline-mock-v0.1.md
```

### Mock baseline

| Metric | Result |
|---|---:|
| Cases | 30 |
| SQL correctness | 2 / 30 (6.7%) |
| Result correctness | 1 / 29 (3.5%) |
| Answer correctness | 0 / 29 (0.0%) |
| Total tokens | 0 |
| Estimated cost | $0 |
| Agent errors | 1 expected security rejection |

The low correctness scores are intentional and informative: the deterministic Mock provider is not a general natural-language-to-SQL model. It mostly emits one fixed top-five query. The purpose of this baseline is to prove that the evaluation pipeline detects incorrect model behavior instead of producing an artificially high score.

Current evaluator semantics are documented in `evaluation/README.md`. In particular, SQL correctness is canonical reference-SQL equality rather than full semantic equivalence, while result correctness is the stronger objective signal for later real-model comparisons.

## Tests and verification

Run the complete Python suite against the Compose environment:

```bash
docker compose up --build -d
docker compose exec fastapi pytest -q
```

Run the evaluation baseline:

```bash
docker compose exec fastapi python -m evaluation.run
```

Run Spring Boot tests locally when Maven is available:

```bash
cd backend/springboot
mvn clean test
```

Day 7 verification completed successfully:

- **51 Python tests passed** in the Compose FastAPI environment
- the **30-case evaluation runner completed successfully**
- SQL / result / answer correctness remained **6.7% / 3.5% / 0.0%** with the deterministic Mock provider
- the latest Day 7 verification run averaged **38.238 ms** end-to-end Agent latency; local latency is environment-sensitive and is not treated as a fixed model-quality score
- **5 Spring Boot tests passed** with `BUILD SUCCESS`
- browser smoke tests passed for Schema, Ask Analyst, validated SQL/result rendering, and manual Run Query

## Phase 2 — Real LLM Integration

Phase 2 work is tracked as **Phase → Stage → Task** rather than Day N. Stage 2.1 keeps the Agent and SQL security architecture unchanged while hardening the real-model boundary with normalized token usage, structured LLM errors, bounded retry/backoff, and a five-case real-model smoke test. See `docs/PHASE2-STAGE2.1.md`.

## Model providers

Default deterministic development mode:

```env
LLM_PROVIDER=mock
```

An OpenAI-compatible Chat Completions adapter is implemented behind the same `LLMClient` interface:

```env
LLM_PROVIDER=openai-compatible
LLM_BASE_URL=https://your-compatible-endpoint.example/v1
LLM_API_KEY=...
LLM_MODEL=your-model
LLM_TIMEOUT_SECONDS=30
```

Phase 2 now builds on this baseline: first stabilize one real-model path, then run the same evaluation dataset for measured quality, token cost, latency, provider comparison, routing, and fallback decisions.

## Data and current limitations

The current portfolio fixture intentionally keeps the dataset small and reproducible.

- `city` contains 15 rows and supports the primary demo/evaluation path.
- `salary`, `employment`, `education`, and `economic_indicator` may currently be empty.
- Valid multi-table joins can therefore return zero rows.
- The current Agent does not yet expose unrestricted Python execution.
- Python analysis, chart generation, and report-generation tools remain later P1 work.
- The Mock provider is a deterministic engineering fixture, not a quality benchmark for real LLMs.

These constraints are kept explicit so that evaluation failures are not confused with infrastructure defects.

## Repository structure

```text
ai-data-analyst/
├── ai/analyst/              # FastAPI, Agent, LLM client, SQL policy
├── backend/springboot/      # Java gateway
├── frontend/web/            # React demo UI
├── db/                      # metadata / database assets
├── etl/                     # sample-data loading
├── evaluation/              # dataset, schema, evaluator, reports
├── tests/                   # unit + integration tests
├── scripts/                 # data utilities
├── docker-compose.yml
├── PROJECT-CONTEXT.md       # current P1 implementation source of truth
└── README.md
```

## Demo walkthrough

A short, repeatable demo is documented in [`docs/DEMO.md`](docs/DEMO.md). The recommended sequence is:

```text
1. Show schema metadata
2. Ask “人口最多的 5 个城市是哪几个？”
3. Show SQL candidate → validated SQL → query evidence
4. Run a manual validated SQL query
5. Demonstrate unsafe DROP TABLE rejection
6. Run the 30-case evaluation harness
```

This order highlights the engineering story: model output is useful, but deterministic controls, evidence, and evaluation decide what the application is allowed to trust.

## Portfolio talking points

See [`docs/PORTFOLIO.md`](docs/PORTFOLIO.md) for concise resume/interview wording. The core story is:

> Built a production-oriented AI data-analysis application spanning React, Spring Boot, FastAPI, PostgreSQL, provider-independent LLM integration, AST-based SQL security, structured observability, and a reproducible 30-case evaluation harness.

## Key engineering decisions

1. Use one Analyst Agent until evaluation demonstrates a need for more orchestration.
2. Treat every generated SQL statement as untrusted input.
3. Keep metadata knowledge separate from execution policy.
4. Share the table allowlist between schema exposure and SQL validation.
5. Keep model providers behind an abstraction.
6. Establish deterministic evaluation before introducing LLM-as-a-Judge.
7. Record actual latency/token/cost evidence instead of estimating quality from demos.
8. Prefer reproducible Docker-based verification and explicit known limitations.

## Next P1 phase

After the Day 7 portfolio/documentation baseline, planned work includes:

```text
Real LLM integration
    ↓
Real-model evaluation
    ↓
Model comparison
    ↓
Token / latency / cost measurement
    ↓
Model routing + fallback
    ↓
Cost controls
    ↓
Richer data + stronger evidence-backed analysis
```

The existing `LLMClient` abstraction and Day 6 evaluation harness are intentionally designed to support this progression.

## Phase 2 routing

Stage 2.4 adds deterministic LLM routing. With `LLM_ROUTING_ENABLED=true`, `/api/analyze` supports `routing_mode=auto|remote|local`. The measured Stage 2.3 default is remote/Groq for interactive use; local/Ollama remains an explicit privacy/offline option. Automatic provider fallback is intentionally deferred to Stage 2.5. See `docs/PHASE2-STAGE2.4-ROUTING-POLICY.md` and `.env.routing.example`.

## Phase 2 Closeout

Phase 2 is **closed**.

The project now includes calibrated real-model evaluation, measured Groq/Qwen baselines, deterministic `auto|remote|local` routing, privacy-aware provider fallback, sticky fallback at the LLM-call boundary, route-level token/cost telemetry, and runtime fallback observability.

| Metric | Groq / GPT-OSS 20B | Ollama / Qwen3 8B |
|---|---:|---:|
| Completed | 30/30 | 24/30 |
| End-to-end semantic | 96.7% | 73.3% |
| Completed-case semantic | 96.7% | 91.7% |
| Avg completed latency | 2.53 s | 65.95 s |
| P95 completed latency | 2.94 s | 116.30 s |
| API cost for 30-case run | ~$0.00647 | $0 |

Runtime acceptance verified:

```text
auto   → remote
remote → remote
local  → local

remote connection failure + auto       → local
local connection failure + auto        → stays local
local connection failure + cross_route → remote
authentication failure                 → no fallback
```

See `docs/PHASE2-STAGE2.6-FINAL-EVALUATION-CLOSEOUT.md` and `PROJECT-CONTEXT.md` for the complete Phase 2 closeout.

### Next phase

Phase 3 should extend evidence-backed analysis—richer data, controlled analysis tooling, visualization, and report-quality outputs—without redesigning the closed SQL-security or routing/fallback architecture.

## Phase 3 — Evidence-backed Analysis

Stage 3.1 adds deterministic dataset evidence to `GET /api/schema`: row count, availability status, and year range. The Analyst receives the same evidence through the existing Schema Tool and is instructed not to assume facts from empty datasets.

Expected current fixture:

```text
city   → 15 rows, available, 2025–2025
salary → 0 rows, empty
```

Stage 3.1 intentionally does not change SQL validation, routing, fallback, or provider configuration, and does not add unrestricted Python execution. See `docs/PHASE3-STAGE3.1-EVIDENCE-FOUNDATION.md`.

## Stage 3.2 — Richer Analytical Data

Stage 3.1 is closed: the user-side Compose pytest suite passed and `/api/schema` evidence was runtime-verified.

Stage 3.2 populates the previously empty analytical domains with a small source-backed fixture while keeping source year and geography explicit:

| Table | Rows | Year | Grain |
|---|---:|---:|---|
| `city` | 15 | 2025 | place |
| `education` | 5 | 2024 | ACS place |
| `economic_indicator` | 10 | 2024 | ACS place |
| `employment` | 5 | 2023 | OEWS metro |
| `salary` | 5 | 2023 | OEWS metro |

OEWS rows carry `occupation_code`, `geography_type`, `geography_name`, and `source`. `salary.median_salary` is a derived annualized value (`median hourly × 2,080`), while `mean_salary` is the published OEWS annual mean.

The current evaluation dataset is `1.1-stage3.2` with **35 cases**. The Stage 2.2 Groq/Qwen reports remain frozen historical **30-case** baselines.

See `docs/PHASE3-STAGE3.2-RICHER-ANALYTICAL-DATA.md` for data provenance, migration behavior, and acceptance commands.
