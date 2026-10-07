# P1 Portfolio Positioning

## One-line project description

Built a production-oriented AI Data Analyst platform using React, Spring Boot, FastAPI, PostgreSQL, provider-independent LLM integration, AST-based SQL security, controlled analytical tools, evidence-bound reporting, deterministic delivery artifacts, observability, and repeatable evaluation/acceptance.

## 30-second summary

P1 is an AI analytics application where an LLM can propose SQL and structured analytical work, but deterministic application code controls what is allowed to execute and what may become trusted evidence. The project spans a React Analyst Workspace, Spring Boot Gateway, FastAPI Agent service, PostgreSQL, real/local model routing and fallback, SQL policy enforcement, controlled statistics/visualization/reporting, provenance, and end-to-end verification.

## Resume bullets

Choose 2–4 depending on available space.

- Designed and implemented an end-to-end AI analytics platform across React, Spring Boot, FastAPI, and PostgreSQL, with provider-independent LLM integration and explicit trust boundaries between model output and deterministic execution.
- Built an AST-based SQL security layer with schema/table allowlists, read-only execution, statement timeout, row caps, and structured rejection codes so generated SQL cannot directly reach the database unchecked.
- Implemented deterministic model routing and privacy-aware fallback across remote and local providers, with trace-level latency, token, fallback, and estimated-cost telemetry.
- Added allowlisted Python analysis, structured chart artifacts, evidence-bound reporting, and deterministic JSON/Markdown delivery packaging without executing arbitrary model-generated code.
- Built reproducible evaluation and acceptance harnesses covering model-quality comparison, SQL security, controlled analysis, visualization, reporting, delivery, and full-chain product contracts; final integrated acceptance passed 7/7 scenarios.
- Hardened the local production baseline with locked frontend dependencies, `npm ci`, health-gated startup, loopback-only published ports, structured-log secret redaction, non-root application containers, and a single `make verify` gate.

## 60-second interview narrative

> I built P1 to explore the production engineering around an AI data analyst rather than stop at a prompt-to-SQL demo. The LLM sits behind a provider abstraction and deterministic router. It can propose SQL, but SQL is treated as untrusted input and must pass an AST-based validator before a read-only PostgreSQL execution. Query rows then become verified evidence. If the question needs statistics, charts, or a report, the model only proposes bounded structured plans; deterministic application code performs allowlisted operations and assembles verified artifacts. The UI deliberately separates the model-generated answer from evidence-backed report and provenance surfaces. I also built model evaluation, routing/fallback telemetry, end-to-end acceptance, and local production/security gates so the system is measurable and reproducible rather than demo-only.

## Strong deep-dive topics

### 1. Why prompts are not a security boundary

The model can still emit unsafe SQL. The application enforces read-only SQL through deterministic parsing/policy and a read-only database transaction. An unsafe `DROP TABLE` scenario is explicitly tested and rejected.

### 2. Why controlled Python instead of a generic code interpreter

Arbitrary model-generated Python would dramatically widen the attack surface. P1 uses a structured plan and allowlisted operations such as descriptive statistics, correlation, and percent change. This is intentionally less flexible but much easier to validate and reason about.

### 3. Why the LLM Answer and Verified Report are separate

Conversational prose can contain unsupported wording or source attribution. P1 keeps that surface explicitly labeled `LLM-generated`. The verified report is assembled only from deterministic query/analysis/chart evidence, so unsupported prose does not silently become a trusted deliverable.

### 4. Why routing is deterministic

The model does not decide which provider should receive a request. Routing is application policy. P1 measured remote/local quality, latency, and cost first, then implemented deterministic `auto|remote|local` routing and bounded fallback behavior.

### 5. Why there are both evaluation and acceptance harnesses

Evaluation measures model quality and can vary by provider. Acceptance verifies stable application contracts such as security rejection, artifact creation, delivery, and the full controlled chain. Keeping them separate avoids treating provider/network variability as a deterministic build property.

### 6. Production-readiness work

Phase 4 added a repeatable local gate, dependency locking, Docker build hygiene, health-gated startup, configuration/secret checks, structured-log redaction, loopback-only ports, and non-root application containers. GitHub CI and public deployment are intentionally staged after repository/documentation cleanup.

## Measured evidence worth citing

Use measured numbers only when the context benefits from them.

- Final Phase 3 real-stack acceptance: **7/7 PASS**.
- Frontend deterministic presentation tests: **4/4 PASS**.
- Phase 2 Groq / GPT-OSS 20B evaluation: **30/30 completed**, **96.7% end-to-end semantic**, average completed latency **2.53 s**, P95 **2.94 s**, about **$0.00647** for the 30-case run.
- Local Ollama / Qwen3 8B evaluation: **24/30 completed**, **73.3% end-to-end semantic**, **91.7% completed-case semantic**, average completed latency **65.95 s**, API cost **$0**.
- Final non-root runtime verification: FastAPI/ETL/Gateway UID **10001**, Web UID **1000**.

## What not to overclaim

Do **not** claim:

- that the small checked-in fixture is a production warehouse;
- that the project is publicly deployed before Stage 4.5 is complete;
- that authentication, tenancy, or distributed rate limiting are implemented;
- that allowlisted Python analysis is a general code interpreter;
- that LLM prose is guaranteed factual;
- that the deterministic Mock provider measures real-model quality;
- that a successful local Docker baseline is equivalent to production cloud operations.

Prefer precise wording such as:

> production-oriented / production-readiness work

rather than:

> production system serving real users

until deployment evidence exists.

## Suggested GitHub repository tagline

> Evidence-backed AI Data Analyst with validated SQL, controlled analytics, deterministic reporting, model routing/evaluation, and production-oriented security boundaries.

## Suggested portfolio card

**AI Data Analyst Platform**  
React · Spring Boot · FastAPI · PostgreSQL · LLM Routing · SQL Security · Controlled Analysis · Evaluation

> Built an evidence-backed AI analytics workflow that separates probabilistic model output from deterministic execution and reporting boundaries, with measured model routing, provenance, end-to-end acceptance, and hardened Docker-based verification.


## Publication assets

The portfolio publication assets are now prepared:

- [`GITHUB-METADATA.md`](GITHUB-METADATA.md) for repository About text, topics, and public-claim guardrails;
- [`DEMO-CAPTURE-CHECKLIST.md`](DEMO-CAPTURE-CHECKLIST.md) for the completed screenshot/video capture plan;
- `assets/analyst-workspace.png`, `assets/controlled-chart.png`, `assets/evidence-report.png`, and `assets/provenance.png` as the canonical README screenshots;
- `assets/p1-ai-data-analyst-demo.mp4` as the finalized ~70-second portfolio demo.

Actual GitHub repository creation, first push, and CI remain Stage 4.4 work.
