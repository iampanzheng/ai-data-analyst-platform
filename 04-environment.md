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


## Phase 2 real-model settings

```text
LLM_PROVIDER=openai-compatible
LLM_BASE_URL=<provider base URL>
LLM_API_KEY=<secret; never commit>
LLM_MODEL=<model id>
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
LLM_RETRY_BACKOFF_SECONDS=0.5
LLM_INPUT_COST_PER_1M=<current provider price>
LLM_OUTPUT_COST_PER_1M=<current provider price>
```

`LLM_INPUT_COST_PER_1M` and `LLM_OUTPUT_COST_PER_1M` are configuration rather than hard-coded prices because provider pricing changes over time.


## Phase 2 local Ollama provider

For Stage 2.1A, Ollama runs on the macOS host and FastAPI remains in Docker. Configure `LLM_BASE_URL=http://host.docker.internal:11434` and `LLM_MODEL=qwen3:8b`. See `docs/PHASE2-STAGE2.1A-OLLAMA.md` for the complete smoke-test sequence.
