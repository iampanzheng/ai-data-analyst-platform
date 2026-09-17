# PROJECT-CONTEXT.md — P1 AI Data Analyst Platform

> Purpose: project-local handoff file for the `ai-data-analyst` repository.
> This file is the source of truth for P1 implementation status, architecture, engineering decisions, verification state, and next actions.
> Overall AI Engineer portfolio strategy, P2/P3, career positioning, and the global roadmap live in the separate Master PROJECT-CONTEXT.md.

---

# 1. Project Identity

## Project

**P1 — AI Data Analyst Platform**

Repository:

```text
ai-data-analyst/
```

## Product goal

Build an AI-powered analytics application that accepts natural-language business/data questions, discovers relevant schema and metadata, generates SQL, validates it, executes read-only analysis, and later adds Python analysis, visualization, and evidence-backed reporting.

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

## Core engineering principle

```text
request → validate → execute → evidence
```

Generated SQL is untrusted input. The Analyst Agent must never bypass the SQL Validator.

---

# 2. Current Status

```text
Day 1  ✅ Data Pipeline
Day 2  ✅ Schema + Metadata + SQL Security
Day 3  ✅ Tests + Integration + Observability
Day 4  ✅ React + Spring Boot Gateway + FastAPI
Day 5  ✅ Model Client + Analyst Agent v0.1
Day 6  → Evaluation Harness
Day 7  → README / Demo / Polish
```

Current active milestone:

```text
P1 → Day 6: Evaluation Harness
```

Do not redesign completed work unless a concrete regression or evaluation result requires it.

---

# 3. Current Architecture

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

## Deterministic query path

```text
Client / React
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

## Analyst Agent v0.1 path

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

## Current V1 non-goals

- multi-agent architecture
- Kubernetes
- fine-tuning
- real-time BI dashboards
- large data warehouse
- arbitrary user code execution

---

# 4. Completed Milestones

## Day 1 — Data Pipeline ✅

Implemented:

- Git / monorepo skeleton
- Docker Compose
- PostgreSQL
- initial public data fixture
- `data/raw`
- ETL
- PostgreSQL schema
- first successful SQL query

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

Current minimal fixture:

- `city` contains 15 rows
- top-five population query returns New York, Los Angeles, Chicago, Houston, Phoenix for 2025

ETL reload rule:

```sql
TRUNCATE TABLE
    employment,
    salary,
    education,
    economic_indicator,
    city
RESTART IDENTITY;
```

Reason: those dependent tables reference `city` with foreign keys.

---

## Day 2 — Schema / Metadata / SQL Security ✅

Implemented:

- `GET /api/schema`
- dataset metadata
- column metadata
- shared table policy
- SQL AST validation with SQLGlot
- `SELECT` / `WITH` only
- public-schema allowlist
- table allowlist
- CTE-aware table extraction
- SQL comment rejection
- `SELECT INTO` rejection
- row-lock rejection
- statement timeout
- row cap
- structured validation errors

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

Key design:

```text
Metadata  = semantic knowledge
Validator = execution policy
```

Schema and Validator share the same table policy to prevent policy drift.

Verified examples include:

```sql
SELECT COUNT(*) FROM public.city;
```

allowed;

```sql
SELECT c.name
FROM public.city c
JOIN public.salary s ON s.city_id = c.id
LIMIT 5;
```

allowed;

```sql
SELECT * FROM pg_catalog.pg_tables;
```

rejected with `SCHEMA_NOT_ALLOWED`;

```sql
SELECT * FROM analytics.city;
```

rejected with `SCHEMA_NOT_ALLOWED`.

---

## Day 3 — Tests / Observability ✅

Implemented:

- SQL Validator unit tests
- PostgreSQL integration tests
- FastAPI schema/query integration tests
- `X-Trace-ID` propagation with UUID fallback
- structured JSON logging
- `execution_ms`
- `row_count`
- queried table list
- request timing

Verified:

```text
32 tests collected in the container
integration tests executed successfully
host-side non-integration tests passed
```

Temporary cleanup:

```text
tests/test_http_debug.py
```

must not remain in the final suite.

Temporary HTTP body debug middleware must not be part of normal runtime.

---

## Day 4 — Application Architecture ✅

Implemented:

- Spring Boot Gateway
- React scaffold
- API contract alignment
- React → Spring Boot → FastAPI → PostgreSQL
- `/api/schema` through Gateway
- `/api/query` through Gateway
- `X-Trace-ID` propagation
- browser query flow

### HTTP transport decision

Gateway → FastAPI uses Java 21 `HttpClient` with explicit HTTP/1.1:

```java
HttpClient.newBuilder()
    .version(HttpClient.Version.HTTP_1_1)
    .connectTimeout(...)
    .build();
```

This was required because the default JDK HTTP/2 preference caused a clear-text Uvicorn HTTP/1.1 upgrade compatibility issue. Symptoms included:

```text
Unsupported upgrade request
Invalid HTTP request received
```

and FastAPI observing `Content-Length` while the ASGI body was empty.

HTTP/1.1 was verified to restore the end-to-end query path.

### Maven

Gateway uses:

```text
Java 21
Spring Boot 4.1.1
Java HttpClient
```

`mvn clean test` has been verified successfully.

Obsolete `ObjectMapper` references were removed from the Gateway client tests.

### Local Maven build setup

Environment-specific Maven mirror settings must not be committed.

Use local:

```text
~/.m2/settings.xml
```

Docker builds use:

- BuildKit secret for the local Maven settings file
- BuildKit cache mounted at `/root/.m2`

Goal:

```text
local mirror for download speed
+
persistent dependency cache
+
no local credentials/mirror settings in Git
```

---

## Day 5 — Model Client + Analyst Agent v0.1 ✅

Implemented:

- provider-independent `LLMClient` abstraction
- Mock LLM provider
- OpenAI-compatible provider abstraction
- `AnalystState`
- Schema Tool
- SQL Tool
- single Analyst Agent v0.1
- `POST /api/analyze`
- React analyst flow

Agent flow:

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

```text
LLM-generated SQL
        ↓
SQL Validator
        ↓
database
```

Never:

```text
LLM
 ↓
database
```

Default development configuration:

```text
LLM_PROVIDER=mock
```

Mock provider is deterministic and requires no API key.

Verified example:

```text
Question:
人口最多的 5 个城市是哪几个？
```

Successful response included:

```text
sql_candidate
validated_sql
query_result
final_answer
trace_id
model
```

Verified SQL:

```sql
SELECT name, state, population, year
FROM city
ORDER BY population DESC
LIMIT 5
```

---

# 5. Current API Surface

## FastAPI

```text
GET  /health
GET  /api/schema
POST /api/query
POST /api/analyze
```

## Gateway

Gateway exposes corresponding `/api/...` routes to clients and forwards them to FastAPI.

## Frontend

Current React UI supports:

- viewing Schema
- submitting SQL
- viewing query results
- submitting a natural-language Analyst question
- viewing the Analyst result, SQL, and query result

The UI is intentionally minimal.

---

# 6. Current Repository Structure

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

This file is the project-local source of truth for P1 status and engineering decisions.

---

# 7. Current Data State

Current minimal dataset:

```text
city
  15 rows
```

The current fixture is sufficient for basic city questions.

Related tables such as:

```text
salary
employment
education
economic_indicator
```

may still be empty in the minimal dataset.

Therefore a valid join may currently return zero rows. Treat that as a data-expansion issue, not automatically as an API or Agent defect.

Before building a strong multi-table evaluation set, expand the dataset for these tables.

---

# 8. Day 6 — Evaluation Harness

## Goal

Run one command and produce a reproducible evaluation report for Analyst Agent v0.1.

## Deliverables

1. finalize evaluation dataset format
2. create first 30 evaluation cases
3. build deterministic evaluator runner
4. add SQL correctness checks
5. add result correctness checks
6. capture Agent execution details
7. collect latency / token / cost fields
8. produce human-reviewable evaluation output

## Initial metrics

```text
SQL correctness
Result correctness
Answer correctness
Latency
Token usage
Estimated cost
```

## Evaluation case fields

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

At minimum:

```text
filtering
aggregation
ranking
grouping
sorting
joins
year/date filters
CTEs
ambiguous wording
unsafe requests
edge cases
```

## Evaluation principle

Do not start with complex LLM-as-a-Judge.

First establish:

```text
question
→ expected behavior
→ actual SQL
→ actual DB result
→ objective comparison
```

Later, human review or LLM-assisted judging can be added.

## Day 6 implementation order

```text
1. Evaluation schema
2. 30 evaluation cases
3. Dataset loader
4. Deterministic SQL evaluator
5. Deterministic result evaluator
6. Agent evaluation runner
7. Latency/token/cost capture
8. JSON + Markdown report
9. Run first baseline
```

First baseline:

```text
LLM_PROVIDER=mock
```

The same evaluator should later be reusable for a real model.

---

# 9. Testing / Verification Rules

Before declaring a milestone complete, use actual execution results.

## Python unit tests

```bash
uv run pytest -q -m "not integration"
```

## Python integration tests

```bash
docker compose up --build -d
docker compose exec fastapi pytest -q
```

Temporary debug tests must not be part of the final suite.

## Java

```bash
cd backend/springboot
mvn clean test
```

## End-to-end minimum

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

Never mark a test, build, or runtime check as passed unless it was actually executed.

---

# 10. Engineering Decisions to Preserve

1. One Analyst Agent only; do not add multi-agent orchestration unless evaluation shows a real need.
2. Generated SQL is untrusted input and must pass the SQL Validator.
3. Analyst database access is read-only.
4. Metadata and execution policy are separate concerns.
5. Schema and Validator use the same allowlist.
6. Model provider selection stays behind an abstraction.
7. Prefer evidence-backed answers.
8. Prefer deterministic evaluation before LLM-as-a-Judge.
9. Local-only development configuration stays out of Git.
10. Docker builds remain reproducible and cache-friendly.
11. Keep commits small and reviewable.
12. Update README / architecture / docs when behavior changes.
13. Prefer real local execution evidence over assumptions.

---

# 11. Current Open Work

## Immediate

```text
- delete tests/test_http_debug.py if still present
- keep HTTP body debugging code out of normal runtime
- keep Maven BuildKit secret/cache settings local
```

## Data

Expand useful data for:

```text
salary
employment
education
economic_indicator
```

before relying on multi-table evaluation cases.

## Later P1 work

After the Evaluation Harness is stable:

```text
- stronger evidence-backed Analyst answers
- Python analysis tool
- chart tool
- report generation
- real-model evaluation
- security hardening
- cost / latency optimization
- polished demo
```

Do not advance these ahead of the evaluation milestone unless they are needed to support evaluation.

---

# 12. New Chat / Coding Agent Handoff

When continuing this repository in a new ChatGPT / Codex / Claude Code session:

1. provide the latest repository/code
2. provide this `PROJECT-CONTEXT.md`
3. treat this file and actual code as the current source of truth
4. do not reconstruct implementation details from old conversation history
5. state the exact next milestone

Recommended continuation message:

```text
这是 P1 AI Data Analyst Platform 的项目续接。

请先阅读：
1. 最新 ai-data-analyst 代码仓库
2. 根目录 PROJECT-CONTEXT.md

不要重新设计已经完成的 Day 1～Day 5。
以 PROJECT-CONTEXT.md 和实际代码为准。

现在继续：
P1 → Day 6：Evaluation Harness

请直接进入实现阶段：
- 检查当前代码
- 完成 evaluation dataset
- 建立 30 个 evaluation cases
- 实现 deterministic SQL / result evaluator
- 接入当前 Analyst Agent v0.1
- 输出可重复的 JSON + Markdown evaluation report
- 提供实际可运行的测试与命令

不要假设测试已经通过，以实际运行结果为准。
```

For later P1 milestones, change only the current milestone.

---

# 13. Relationship to Master Portfolio Context

This file intentionally does not contain:

```text
- overall AI Engineer career strategy
- resume positioning
- detailed P2 design
- detailed P3 design
- global 12-week transition plan
```

Those belong in the separate Master `PROJECT-CONTEXT.md`.

The two-level model is:

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
├── P1 engineering decisions
├── P1 verification state
├── P1 open work
└── P1 next milestone
```

When P1 is completed, this file can remain as the final project-local handoff/history, while the Master Context changes the active project to P2.

---

# 14. Current Next Action

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
