# Phase 2 — Stage 2.1A.2: Value Grounding + Answer-aware Smoke Evaluation

## Why this refinement exists

The first Qwen3 8B smoke runs exposed two different failure modes that a pipeline-only smoke check could not distinguish:

1. The SQL was valid but used `state = 'California'` while the database stores `CA`.
2. A correct grouped SQL result was summarized incorrectly as 13 total cities instead of 15.

Both are end-to-end semantic failures even though the application pipeline itself completed successfully.

## Value grounding

`/api/schema` now adds bounded grounding information only for explicitly approved low-cardinality semantic types.

For `geography_code`, each column may expose:

- `sample_values`: up to `VALUE_GROUNDING_MAX_VALUES` real stored values.
- `value_hint`: the mapping rule from natural-language U.S. state names/aliases to USPS two-letter codes.

The values are collected only from allowlisted tables/columns discovered through schema metadata. This is intentionally not a generic dump of arbitrary database values.

## Smoke evaluation layers

Every case now reports four separate signals:

- `pipeline_passed`: the request completed through the expected application path.
- `result_passed`: the validated SQL result matches the case expectation, or the expected security rejection occurred.
- `answer_passed`: the user-facing answer preserves the required facts from the verified result.
- `semantic_passed`: both result and answer checks pass.

This prevents a correct SQL result with a hallucinated final answer from being counted as an end-to-end success.

## Stage 2.1A.2 exit check

Run:

```bash
docker compose up --build -d
docker compose exec fastapi pytest -q
docker compose exec fastapi python -m evaluation.smoke
```

For the five-case smoke set, the target is:

- pipeline: 5/5
- result: 5/5
- answer: 5/5
- semantic: 5/5

Latency and token totals remain observational in this stage; `/no_think` is not treated as a proven optimization until repeated measurements support that conclusion.
