# Phase 3 — Stage 3.4: Controlled Visualization

Status: **IN PROGRESS — v0.1 candidate**

## Objective

Add visualization without weakening the deterministic evidence path established in Stages 3.1–3.3.

The Stage 3.4 execution boundary is:

```text
natural-language question
→ SQL planner
→ SQL Validator
→ PostgreSQL verified rows
→ optional Controlled Python Analysis
→ structured chart plan
→ deterministic chart validator / artifact builder
→ frontend renderer
→ evidence-backed answer
```

The model never emits executable visualization code.

## v0.1 scope

Supported chart types:

- `bar`
- `line`
- `scatter`

Visualization is activated only for explicit visualization intent such as chart / plot / visualize / 图表 / 可视化 / 柱状图 / 折线图 / 散点图 / 趋势图 / 画图.

The LLM may emit only this chart-plan shape:

```json
{
  "chart_type": "bar|line|scatter",
  "x": "verified_result_column",
  "y": "verified_result_column",
  "title": "short title"
}
```

The application validates the plan against the verified SQL result and builds `chart_artifact` itself.

## Deterministic controls

- chart type allowlist only
- `x` and `y` must be columns in the verified SQL result
- `y` must contain finite numeric values
- scatter `x` must also be finite numeric values
- no extra plan keys
- no JavaScript / Python / SQL / HTML / SVG code accepted from the model
- maximum 100 chart points; larger results must be narrowed in SQL rather than silently truncated
- empty results do not generate charts

## API artifact

`POST /api/analyze` now includes:

```json
{
  "chart_artifact": {
    "chart_type": "bar",
    "title": "Top city population",
    "x": {"column": "name"},
    "y": {"column": "population"},
    "points": [
      {"x": "New York", "y": 8584629.0}
    ],
    "point_count": 1,
    "source": "verified_query_result"
  }
}
```

`chart_artifact` is `null` when visualization was not requested.

## Frontend

The React UI renders the controlled artifact with a small in-repo SVG renderer. No new charting-library dependency is introduced in v0.1.

## Verification state

Verified in the packaging environment:

- `python -m compileall -q ai/analyst/app tests`: PASS
- `python -m pytest tests/test_visualization.py -q`: PASS (5 tests)

Not claimed as verified here:

- full pytest, because the packaging host does not have the repo's `sqlglot` dependency installed
- frontend Docker/Vite build
- remote-provider end-to-end chart smoke

Those are Stage 3.4 v0.1 candidate gates to run in the existing Compose environment.

## Candidate acceptance checks

1. full `pytest -q` passes in the FastAPI container
2. frontend build succeeds
3. explicit bar-chart question returns a valid `chart_artifact`
4. explicit scatter-chart/correlation question returns verified raw rows + controlled correlation result + valid scatter `chart_artifact`
5. plain non-visual question keeps `chart_artifact = null`
6. invalid model chart plans are rejected deterministically

## Suggested real-provider smoke questions

Bar chart:

```text
用柱状图显示 2025 年人口最多的 5 个城市及人口。
```

Correlation scatter:

```text
用散点图展示现有数据中城市人口与本科及以上人口比例的关系，并给出相关系数。
```


## v0.1.1 value-grounding regression fix

The first real combined correlation + scatter smoke exposed an upstream semantic-value issue rather than a visualization defect. The remote SQL planner used the nonexistent education category `Bachelor's or higher` instead of the stored value `Bachelor's degree or higher`, so the verified query returned zero rows.

The fix deliberately reuses the existing bounded value-grounding mechanism:

- `education.education_level` is now a value-grounded categorical column.
- `/api/schema` exposes its bounded distinct sample values.
- Its `value_hint` instructs the SQL planner to use exact stored category labels rather than paraphrasing them.
- Integration coverage asserts that `Bachelor's degree or higher` is present in the schema evidence.

No SQL auto-rewrite or arbitrary retry logic was added. The deterministic SQL validator, Controlled Python Analysis boundary, and Controlled Visualization boundary remain unchanged.
