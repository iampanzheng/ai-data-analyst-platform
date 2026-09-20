# Day 5 — Model Client + Analyst Agent v0.1

## API
`POST /api/analyze`

Request:
```json
{"question":"人口最多的 5 个城市是哪几个？"}
```

Response contains:
- `trace_id`
- `question`
- `sql_candidate`
- `validated_sql`
- `query_result`
- `final_answer`
- `model`
- `usage`
- `errors`

## Execution flow
1. Get schema + business metadata.
2. Ask the model to generate a single SELECT/WITH query.
3. Run the existing SQL Validator.
4. Execute through the existing read-only SQL path.
5. Ask the model to summarize the verified result.

## Security invariant
The model never gets direct database access. Generated SQL must pass the same Validator used by `/api/query`.

## Model providers
- `mock` — deterministic local development.
- `openai-compatible` — generic `/v1/chat/completions` HTTP adapter.

No vendor SDK is required in v0.1.
