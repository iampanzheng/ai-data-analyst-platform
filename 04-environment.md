# 04 Environment Variables

## Runtime variables

| Variable | Required | Default / purpose |
|---|---:|---|
| `DATABASE_URL` | yes in service runtime | PostgreSQL connection string |
| `SQL_MAX_ROWS` | no | `1000`; maximum returned rows |
| `SQL_STATEMENT_TIMEOUT_MS` | no | `3000`; PostgreSQL statement timeout |
| `LLM_PROVIDER` | no | `mock`; `openai-compatible` is also supported |
| `LLM_BASE_URL` | real model only | OpenAI-compatible API base URL |
| `LLM_API_KEY` | provider-dependent | API credential; never commit it |
| `LLM_MODEL` | real model only | provider model identifier |
| `LLM_TIMEOUT_SECONDS` | no | `30` |
| `LOG_LEVEL` | no | application logging level |
| `EMBEDDING_MODEL` | no | reserved for later RAG work |

Copy `.env.example` to `.env` for local development. `.env` is ignored by Git.

## Default model mode

```env
LLM_PROVIDER=mock
```

The Mock provider requires no API key and is used by the checked-in Day 6 baseline.

## Optional local Maven mirror

The default Docker build must work without a host `~/.m2/settings.xml`.

`backend/springboot/Dockerfile` accepts an optional BuildKit secret named `maven_settings` and always uses a BuildKit Maven dependency cache. Developers who use a private/local Maven mirror may opt in with the committed override file:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.maven-local.yml \
  up --build -d
```

The override references `${HOME}/.m2/settings.xml`; use it only on machines where that file exists.

Never commit real API keys, Maven credentials, or machine-specific settings files.
