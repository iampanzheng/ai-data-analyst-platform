# Day 5 — Model Client + Analyst Agent v0.1

## Scope
- Model client abstraction
- Deterministic mock model for local development
- OpenAI-compatible HTTP chat-completions adapter
- Explicit AnalystState
- Schema and SQL tool interfaces implemented against existing deterministic services
- Single-agent orchestration, no LangGraph/multi-agent complexity
- `POST /api/analyze`

## Flow
question → schema → LLM SQL generation → SQL validation → PostgreSQL → LLM answer

## Local mode
`LLM_PROVIDER=mock` requires no model API key and returns deterministic SQL/answer content.

## Real model mode
Set:
- `LLM_PROVIDER=openai-compatible`
- `LLM_BASE_URL` (provider host, e.g. `https://example.com`)
- `LLM_API_KEY`
- `LLM_MODEL`

The client posts to `/v1/chat/completions`.

## Non-goals
- multi-agent
- LangGraph orchestration
- tool selection by LLM
- Python/chart/report tools execution
- streaming
- RAG
