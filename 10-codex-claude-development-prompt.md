# 10 Coding Agent Development Prompt

You are the implementation agent for the P1 AI Data Analyst Platform V1.1.

Read these files before coding:
- 01-project-spec.md
- 02-architecture.md
- 03-database-schema.sql
- 06-fastapi-api-contract.md
- 07-agent-tool-contract.md
- 08-sql-security-rules.md
- 11-sprint-0-task-list.md

## Non-negotiable rules

1. Do not invent product requirements.
2. Do not add multi-agent architecture.
3. Keep security boundaries explicit.
4. Never allow arbitrary write SQL.
5. Add tests for every security rule.
6. Prefer small, reviewable commits.
7. Keep provider/model configuration behind an abstraction.
8. Update README and architecture docs when behavior changes.

## First milestone
Make this work locally:

```bash
docker compose up --build
curl http://localhost:8000/health
curl http://localhost:8000/api/schema
curl -X POST http://localhost:8000/api/query -H 'Content-Type: application/json' -d '{"sql":"SELECT name, state, population FROM city ORDER BY population DESC LIMIT 5"}'
```

Then add negative tests showing INSERT/UPDATE/DELETE/DROP and non-allowlisted tables are rejected.
