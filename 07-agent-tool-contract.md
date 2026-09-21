# 07 Analyst Agent / Tool Contract

## Current state

The current `AnalystState` carries the core analysis lifecycle, including:

```text
question
relevant_schema
sql_candidate
validated_sql
query_result
final_answer
errors
trace_id
model
usage
```

## Implemented tools / boundaries

### Schema Tool

Returns allowlisted schema and business metadata for model context.

### LLM Client

Provider-independent interface used for SQL generation and answer generation.

Current providers:

```text
mock
openai-compatible
```

### SQL Tool

Executes only SQL that has passed the shared SQL Validator. Database execution is read-only, timeout-bounded, and row-capped.

## Planned later tools

The following are architectural extension points, not current Day 7 features:

### Python Analysis Tool

Planned bounded Pandas/NumPy analysis against verified query results. Arbitrary OS/network/file execution will not be exposed to the model.

### Chart Tool

Planned structured chart generation from verified data.

### Report Tool

Planned evidence-backed report generation using SQL/results/analysis artifacts.

## Critical invariant

Never:

```text
LLM → database
```

Always:

```text
LLM SQL candidate → SQL Validator → read-only database
```
