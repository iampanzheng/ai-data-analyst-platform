# Phase 2 — Stage 2.1B: Gemini 3.8 Flash

## Goal

Run the same five-case real-model smoke suite against a hosted model without changing the Analyst Agent or SQL Security boundary.

## Provider

- Model: `gemini-3.8-flash`
- API style: OpenAI-compatible Chat Completions
- Base URL: `https://generativelanguage.googleapis.com/v1beta/openai`
- Recommended reasoning effort for this stage: `low`

The Gemini API key is supplied only through local environment configuration and must not be committed.

## Configuration

Copy `.env.gemini.example` to `.env`, replace only `LLM_API_KEY`, then recreate the FastAPI container.

```bash
cp .env.gemini.example .env
# edit .env and set LLM_API_KEY
docker compose up --build -d
```

## Connectivity check

From the FastAPI container:

```bash
docker compose exec fastapi python -c 'import os,httpx; u="https://generativelanguage.googleapis.com/v1beta/openai/models"; r=httpx.get(u,headers={"Authorization":"Bearer "+os.environ["LLM_API_KEY"]},timeout=20); print(r.status_code); print("gemini-3.8-flash" in r.text)'
```

Expected: HTTP `200` and `True`.

## Regression + smoke

```bash
docker compose exec fastapi pytest -q
docker compose exec fastapi python -m evaluation.smoke
```

Stage exit criterion:

- pipeline: 5/5
- result: 5/5
- answer: 5/5
- semantic: 5/5
- usage captured
- unsafe SQL rejected by deterministic validator

Do not run the 30-case full baseline until this smoke suite is reviewed.
