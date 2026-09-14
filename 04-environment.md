# 04 Environment Variables

| Variable | Required | Sprint 0 |
|---|---:|---:|
| DATABASE_URL | yes | PostgreSQL connection string |
| SQL_MAX_ROWS | no | default 1000 |
| SQL_STATEMENT_TIMEOUT_MS | no | default 3000 |
| LLM_PROVIDER | no | reserved for Sprint 1 |
| LLM_MODEL | no | reserved for Sprint 1 |
| EMBEDDING_MODEL | no | reserved for RAG phase |
| LOG_LEVEL | no | reserved |

Never commit real API keys. `.env.example` is safe to commit; `.env` is ignored.
