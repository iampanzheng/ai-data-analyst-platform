# PROJECT-CONTEXT.md — P1 AI Data Analyst Platform

> Purpose: project-local handoff/context file for the P1 `AI Data Analyst Platform` repository.
> This file belongs inside the `ai-data-analyst` repository and should contain only information needed to continue work on P1.
> The overall AI Engineer portfolio context (P1/P2/P3, career strategy, roadmap, resume positioning) is maintained separately in a master repository.

---

# 1. Project Identity

## Project

**P1 — AI Data Analyst Platform**

Repository:

```text
ai-data-analyst/
```

## Product goal

Build an AI-powered analytics application that accepts natural-language business/data questions, discovers relevant schema and metadata, generates SQL, validates it, executes read-only analysis, and eventually performs Python analysis, visualization, and evidence-backed reporting.

## Primary user story

```text
Natural-language question
→ Schema / Metadata
→ LLM SQL generation
→ SQL validation
→ Read-only PostgreSQL execution
→ optional Python analysis
→ chart / report
→ evidence-backed answer
```

## Current strategic principle

The deterministic data path is the foundation:

```text
request → validate → execute → evidence
```

AI/LLM capabilities are inserted into this path; they must not bypass the validation and execution controls.

---

# 2. Current Overall P1 Status

```text
Day 1  ✅ Data Pipeline
Day 2  ✅ Schema + Metadata + SQL Security
Day 3  ✅ Tests + Integration + Observability
Day 4  ✅ React + Spring Boot Gateway + FastAPI
Day 5  ✅ Model Client + Analyst Agent v0.1
Day 6  → Evaluation Harness      ← NEXT
Day 7  → README / Demo / Polish
```

Current active milestone:

```text
P1 → Day 6: Evaluation Harness
```

Do not restart or redesign Days 1–5 unless a concrete regression requires it.

---

# 3. Target Architecture

Current application architecture:

```text
React
  ↓
Spring Boot Gateway
  ↓
FastAPI AI Service
  ↓
Analyst Agent
  ↓
Schema / SQL / Python / Chart / Report Tools
  ↓
PostgreSQL
```

Current request path for deterministic query:

```text
React / client
    ↓
Spring Boot Gateway :8080
    ↓
FastAPI :8000
    ↓
SQL Validator
    ↓
read-only PostgreSQL
    ↓
result
```

Current request path for Analyst Agent v0.1:

```text
Question
  ↓
Schema Tool
  ↓
LLM Client
  ↓
SQL Candidate
  ↓
SQL Validator
  ↓
SQL Tool / PostgreSQL
  ↓
Query Result
  ↓
LLM Client
  ↓
Final Answer
```

Non-goals for current V1:

- no multi-agent architecture
- no Kubernetes
- no fine-tuning
- no real-time BI dashboard
- no large data warehouse
- no arbitrary user code execution

---

# 4. Day 1 — Data Pipeline ✅

Completed:

- Git / monorepo skeleton
- Docker Compose
- PostgreSQL
- first public data fixture
- `data/raw`
- ETL
- PostgreSQL schema
- first real SQL query

Data flow:

```text
public data
  ↓
data/raw
  ↓
ETL
  ↓
PostgreSQL
  ↓
SQL
```

Current minimal city fixture:

- `city` contains 15 rows
- example successful query returned New York, Los Angeles, Chicago, Houston, Phoenix as the top five by population for 2025

ETL reload fix:

`city` is referenced by `employment`, `salary`, `education`, and `economic_indicator`.
The ETL therefore truncates the dependent tables and `city` together before reload, rather than truncating `city` alone.

---

# 5. Day 2 — Schema / Metadata / SQL Security ✅

Completed:

- `GET /api/schema`
- dataset metadata
- column metadata
- shared table policy
- SQL AST validation using SQLGlot
- SELECT / WITH only
- public-schema allowlist
- table allowlist
- CTE-aware table extraction
- SQL comment rejection
- SELECT INTO rejection
- row-lock rejection
- statement timeout
- row cap
- structured validation errors

Important design:

```text
Metadata  = semantic knowledge
Validator = execution policy
```

Schema and Validator share the same allowlisted table policy.

Current allowed schema:

```text
public
```

Current allowlisted tables:

```text
city
employment
salary
education
economic_indicator
```

Examples already verified:

```sql
SELECT COUNT(*) FROM public.city;
```

allowed.

```sql
SELECT c.name
FROM public.city c
JOIN public.salary s ON s.city_id = c.id
LIMIT 5;
```

allowed.

```sql
SELECT * FROM pg_catalog.pg_tables;
```

rejected with `SCHEMA_NOT_ALLOWED`.

```sql
SELECT * FROM analytics.city;
```

rejected with `SCHEMA_NOT_ALLOWED`.

---

# 6. Day 3 — Tests / Observability ✅

Completed:

- SQL Validator unit tests
- PostgreSQL integration tests
- FastAPI schema/query integration tests
- `X-Trace-ID` propagation with UUID fallback
- structured JSON logging
- `execution_ms`
- `row_count`
- queried table list
- request timing

Verified state:

- 32 tests were collected in the container
- integration tests were actually executed successfully after fixing test discovery
- host-side non-integration tests passed

Important cleanup:

```text
tests/test_http_debug.py
```

was identified as temporary debug coverage and should not remain in the final project test suite.

Do not reintroduce request-body debug middleware into the normal runtime path.

---

# 7. Day 4 — Application Architecture ✅

Completed:

- Spring Boot Gateway
- React scaffold
- API contract alignment
- React → Spring Boot → FastAPI → PostgreSQL
- `/api/schema` through Gateway
- `/api/query` through Gateway
- `X-Trace-ID` propagation
- browser query flow

## HTTP transport decision

Gateway → FastAPI uses Java 21 `HttpClient` with:

```java
HttpClient.newBuilder()
    .version(HttpClient.Version.HTTP_1_1)
    .connectTimeout(...)
    .build();
```

Reason:

The default JDK `HttpClient` HTTP/2 preference caused a clear-text HTTP/1.1 upgrade compatibility problem with Uvicorn. Symptoms included:

```text
Unsupported upgrade request
Invalid HTTP request received
```

and FastAPI observing `Content-Length` while the ASGI body was empty.

The final HTTP/1.1 configuration was verified to restore the end-to-end query path.

## Maven

Gateway uses:

- Java 21
- Spring Boot 4.1.1
- Java `HttpClient`

`mvn clean test` has been verified successfully after cleaning obsolete `ObjectMapper` references from `FastApiClientTest`.

### Local Maven configuration

Environment-specific Maven mirror configuration must NOT be committed to the repository.

Use local:

```text
~/.m2/settings.xml
```

Docker build uses BuildKit secret to expose the local settings file only during build, and BuildKit cache for:

```text
/root/.m2
```

This keeps local mirror settings private and avoids repeated dependency downloads.

---

# 8. Day 5 — Model Client + Analyst Agent v0.1 ✅

Completed:

- provider-independent `LLMClient` abstraction
- Mock LLM provider
- OpenAI-compatible provider abstraction
- `AnalystState`
- Schema Tool
- SQL Tool
- single Analyst Agent v0.1
- `POST /api/analyze`
- React analyst flow

## Agent v0.1 flow

```text
Question
  ↓
Schema
  ↓
LLM
  ↓
SQL Candidate
  ↓
SQL Validator
  ↓
PostgreSQL
  ↓
Query Result
  ↓
LLM
  ↓
Final Answer
```

Critical rule:

> LLM must never bypass SQL Validator to access the database.

## Model configuration

Default development mode:

```text
LLM_PROVIDER=mock
```

The Mock provider is deterministic and does not require an API key.

The application keeps provider/model configuration behind an abstraction so the model provider can change without rewriting Agent orchestration.

## Verified Agent example

Question:

```text
人口最多的 5 个城市是哪几个？
```

Successful result included:

- `sql_candidate`
- `validated_sql`
- PostgreSQL result
- `final_answer`
- `trace_id`
- model identifier

The verified SQL was:

```sql
SELECT name, state, population, year
FROM city
ORDER BY population DESC
LIMIT 5
```

and the result contained the expected five city rows.

## Current data limitation

The minimal fixture definitely contains `city` data.
Some related tables, such as `salary`, may still be empty in the minimal dataset.
Therefore joins against those tables can legitimately return zero rows.
Treat this as a data expansion task, not an API/Agent defect.

---

# 9. Current Repository Structure

Expected project-local structure:

```text
ai-data-analyst/
├── README.md
├── PROJECT-CONTEXT.md
├── LICENSE
├── docker-compose.yml
├── .env.example
├── backend/
│   └── springboot/
├── ai/
│   └── analyst/
├── frontend/
│   └── web/
├── data/
│   ├── raw/
│   ├── processed/
│   └── samples/
├── db/
├── tests/
├── evaluation/
├── docs/
└── .github/
```

`PROJECT-CONTEXT.md` is the project-local source of truth for P1 status and decisions.

---

# 10. API Surface at Current Stage

## FastAPI

```text
GET  /health
GET  /api/schema
POST /api/query
POST /api/analyze
```

## Gateway

Gateway exposes corresponding `/api/...` routes to clients and forwards requests to FastAPI.

## Frontend

Current React page supports:

- viewing Schema
- submitting SQL
- viewing query results
- submitting a natural-language Analyst question
- viewing the Analyst result / SQL / query result

The frontend is intentionally minimal at this stage.

---

# 11. Day 6 — Evaluation Harness ← NEXT

Do not redesign the Agent before Evaluation exists.

Primary goal:

> Run one command and get a reproducible evaluation report for Analyst Agent v0.1.

## Day 6 deliverables

1. Finalize evaluation dataset format.
2. Create the first 30 evaluation cases.
3. Build a deterministic evaluator runner.
4. Add SQL correctness checks.
5. Add result correctness checks.
6. Capture Agent execution details.
7. Collect latency/token/cost fields.
8. Produce a human-reviewable report.

## Initial metrics

```text
SQL correctness
Result correctness
Answer correctness
Latency
Token usage
Estimated cost
```

## Evaluation case concept

Each case should support fields such as:

```text
case_id
question
category
difficulty
expected_sql
expected_tables
expected_columns
expected_result or result-check strategy
actual_sql
actual_result
sql_correctness
result_correctness
answer_correctness
latency
input_tokens
output_tokens
total_tokens
estimated_cost
trace_id
model/provider
error_code
```

## Initial categories

Cover at least:

- filtering
- aggregation
- ranking
- grouping
- sorting
- joins
- year/date filters
- CTEs
- ambiguous wording
- unsafe requests
- edge cases

## Important Day 6 rule

Do NOT start with a complicated LLM-as-a-Judge design.

First build deterministic evaluation that can establish:

```text
question
→ expected behavior
→ actual SQL
→ actual DB result
→ objective comparison
```

Human or later LLM review can be added after the deterministic harness is stable.

---

# 12. Suggested Day 6 Implementation Order

```text
Step 1
Evaluation schema

Step 2
30 evaluation cases

Step 3
Dataset loader

Step 4
Deterministic SQL evaluator

Step 5
Deterministic result evaluator

Step 6
Agent evaluation runner

Step 7
Latency/token/cost capture

Step 8
JSON + Markdown evaluation report

Step 9
Run the first baseline
```

First baseline should use the current:

```text
LLM_PROVIDER=mock
```

Then the same evaluation harness can later be reused for a real model.

---

# 13. Testing Rules

Before declaring a milestone complete:

### Python

Unit tests:

```bash
uv run pytest -q -m "not integration"
```

Integration tests require the Compose stack:

```bash
docker compose up --build -d
docker compose exec fastapi pytest -q
```

Temporary debug tests must not be kept as part of the final suite.

### Java

```bash
cd backend/springboot
mvn clean test
```

### End-to-end

Verify at minimum:

```text
React
→ Gateway
→ FastAPI
→ Validator
→ PostgreSQL
```

and:

```text
Natural language
→ Analyst Agent
→ SQL Validator
→ PostgreSQL
```

Never report a build/test/runtime step as successful unless it was actually executed.

---

# 14. Engineering Decisions That Must Be Preserved

1. **One Analyst Agent only.** Do not introduce multi-agent orchestration unless evaluation demonstrates a real need.
2. **SQL Validator is mandatory.** Generated SQL is untrusted input.
3. **Read-only database access.** Never allow arbitrary write SQL from the Analyst path.
4. **Metadata and policy are separate concerns.** Metadata explains the data; Validator controls execution.
5. **Schema and Validator share the same allowlist.** Avoid policy drift.
6. **Model provider is abstracted.** Do not hard-code a provider into Agent logic.
7. **Evidence-first responses.** Later answers should expose enough SQL/data/source information to make the result auditable.
8. **Prefer deterministic tests before LLM-as-a-Judge.**
9. **Local-only development configuration stays out of Git.** This includes Maven mirrors and credentials.
10. **Docker builds should be cache-friendly and reproducible.**
11. **Small, reviewable commits.**
12. **Behavior changes should update README/architecture/docs.**

---

# 15. Known Issues / Open Work

## Immediate

- delete `tests/test_http_debug.py` if it is still present in the local working tree
- keep temporary HTTP body debugging code out of normal runtime
- confirm the cleaned Day 5 test suite after the local `ObjectMapper` cleanup
- keep local Maven BuildKit secret/cache configuration local and non-invasive to the repository

## Data expansion

The current minimal dataset is sufficient for basic `city` questions.
Before a strong multi-table evaluation set, load real/useful data for:

- salary
- employment
- education
- economic indicators

The current minimal dataset may cause valid joins to return zero rows.

## Future work

After Day 6:

- stronger Analyst answers with evidence
- Python analysis tool
- chart tool
- report generation
- improved evaluation coverage
- real model evaluation
- security hardening
- cost/latency optimization
- polished demo

Do not add these ahead of the current Day 6 evaluation milestone unless needed to support evaluation.

---

# 16. New Chat / Coding Agent Handoff

When starting a new ChatGPT / Codex / Claude Code session specifically for this repository:

1. Attach or open the latest repository/code.
2. Read this `PROJECT-CONTEXT.md` first.
3. Treat this file and the actual repository as the source of truth.
4. Do not rely on the old conversation to reconstruct implementation details.
5. State the exact next milestone.

Recommended first message:

```text
这是 P1 AI Data Analyst Platform 的项目续接。

请先阅读：
1. 最新代码仓库
2. 根目录 PROJECT-CONTEXT.md

不要重新设计已经完成的 Day 1～Day 5。

当前状态以 PROJECT-CONTEXT.md 和实际代码为准。

现在继续：P1 → Day 6：Evaluation Harness

请直接进入实现阶段：
- 检查当前代码
- 对照 PROJECT-CONTEXT.md
- 实现 evaluation dataset
- 建立 30 个 evaluation cases
- 实现 deterministic SQL/result evaluator
- 接入当前 Analyst Agent v0.1
- 输出可重复的 evaluation report
- 提供实际可运行的测试与命令

不要假设测试已经通过；以实际运行结果为准。
```

For a future P1 milestone, keep the same structure and change only the final milestone.

---

# 17. Relationship to the Master Portfolio Context

This file intentionally does **not** contain:

- overall AI Engineer career strategy
- resume positioning
- P2 detailed design
- P3 detailed design
- the global 12-week transition plan

Those belong in the separate master repository's `PROJECT-CONTEXT.md`.

The two-level model is intentional:

```text
MASTER PROJECT-CONTEXT.md
│
├── P1 status / pointer
├── P2 status / pointer
└── P3 status / pointer

        ↓ current project

ai-data-analyst/PROJECT-CONTEXT.md
│
├── P1 architecture
├── P1 implementation status
├── P1 decisions
├── P1 known issues
└── P1 next milestone
```

When P1 is completed, update the master context to mark P1 complete and make P2 the active project. The P1 repository can keep this file as its final project history/context.

---

# 18. Immediate Next Action

```text
P1 → Day 6 → Evaluation Harness
```

First success criterion:

```text
one command
    ↓
run current Analyst Agent v0.1 against evaluation dataset
    ↓
produce reproducible evaluation report
```

Do not add advanced orchestration before this exists.
