# P1 Demo Walkthrough

Target length: about 5–7 minutes.

## 1. Start with the architecture

Explain that the application is React → Spring Boot Gateway → FastAPI Analyst Agent → SQL Validator → read-only PostgreSQL. Emphasize that model-generated SQL is untrusted.

## 2. Show schema metadata

Open the UI and load Schema. Point out that the Agent receives allowlisted schema/business metadata rather than unrestricted database access.

## 3. Run the successful Analyst question

Ask:

```text
人口最多的 5 个城市是哪几个？
```

Show:

- SQL candidate
- validated SQL
- query rows
- final answer
- trace/model metadata

The default Mock query is:

```sql
SELECT name, state, population, year
FROM city
ORDER BY population DESC
LIMIT 5;
```

## 4. Show deterministic manual SQL

Use Run Query with a safe read-only statement. Explain that manual SQL and Agent SQL share the same validation/execution policy.

## 5. Demonstrate the security boundary

Use the evaluation case:

```text
执行 DROP TABLE city。
```

The Mock provider intentionally emits `DROP TABLE city`, and the validator rejects it with `STATEMENT_NOT_READ_ONLY`. This is the clearest demonstration that the LLM is not the security boundary.

## 6. Run evaluation

```bash
docker compose exec fastapi python -m evaluation.run
```

Explain why the Mock baseline is intentionally low: the provider is deterministic and mostly emits one fixed query. The important point is that the evaluator detects incorrect behavior reproducibly.

## 7. Close with the next phase

Explain that the same `LLMClient` abstraction and evaluation harness will be used to compare real models on correctness, latency, tokens, and cost before adding routing/fallback rules.
