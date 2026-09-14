# 01 Project Spec — V1.1

## Product
AI Data Analyst Platform

## Primary user story
A user asks a natural-language business/data question. The system discovers relevant schema/metadata, generates SQL, validates it, executes read-only analysis, optionally performs Python analysis, creates a chart, and returns an evidence-backed report.

## V1 scope
1. PostgreSQL data layer
2. Schema + metadata
3. Deterministic read-only SQL API
4. SQL safety validator
5. LLM-to-SQL agent
6. Python/Pandas analysis tool
7. Chart tool
8. Evidence-backed report
9. React UI
10. Spring Boot gateway
11. Evaluation dataset
12. Docker Compose

## Explicitly out of scope for V1
- multi-agent architecture
- Kubernetes
- fine-tuning
- real-time BI dashboards
- large data warehouse
- arbitrary code execution from users

## Definition of Done for Sprint 0
- `docker compose up --build` succeeds
- PostgreSQL is initialized with sample data
- `/health` works
- `/api/schema` returns whitelisted schema metadata
- `/api/query` accepts safe SELECT/WITH queries
- unsafe SQL is rejected
- README documents first query
