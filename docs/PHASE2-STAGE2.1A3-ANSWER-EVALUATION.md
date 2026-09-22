# Phase 2 — Stage 2.1A.3: Multilingual Entity Normalization + Context-aware Answer Evaluation

## Why this refinement exists

The Stage 2.1A.2 Qwen3 8B smoke run reached 5/5 correct SQL/results, but two correct user-facing answers were scored as failures by the smoke evaluator:

1. `SMOKE-003` returned the correct California rows but translated `Los Angeles / San Diego / San Jose` to `洛杉矶 / 圣地亚哥 / 圣何塞`.
2. `SMOKE-004` correctly said that 9 states were represented, but the evaluator treated the phrase `总计9个州` as though it were a claim that there were 9 cities in total.

These are evaluator false negatives, not model failures.

## Changes

The smoke answer evaluator now:

- resolves a small canonical-entity alias table for the city entities used by the smoke dataset,
- accepts either English database names or their known Chinese equivalents,
- treats state-count language separately from city-total language,
- only validates the city total when the answer explicitly claims a city total,
- still rejects an explicit wrong city-total claim such as `城市总数为13个`.

The evaluator remains deterministic. This stage does not introduce LLM-as-a-Judge and does not modify the Agent, prompts, value grounding, or SQL security boundary.

## Exit check

Run:

```bash
docker compose up --build -d
docker compose exec fastapi pytest -q
docker compose exec fastapi python -m evaluation.smoke
```

Expected smoke summary:

- pipeline: 5/5
- result: 5/5
- answer: 5/5
- semantic: 5/5

If these pass, Stage 2.1A — Ollama + Qwen3 8B can be closed and Stage 2.1B can start with the next hosted provider.

## v0.2 evaluator patch

The city-total claim parser now distinguishes explicit city-total wording from state-count wording:

- `城市总数为13个` is recognized as an explicit city-total claim and is rejected when 15 is expected.
- `总计9个州被统计` is not interpreted as a city-total claim.
- Generic wording such as `共有15个城市` remains supported only when the city unit is explicit.

This patch changes evaluator parsing only; it does not change the agent, prompts, value grounding, SQL validation, or model configuration.
