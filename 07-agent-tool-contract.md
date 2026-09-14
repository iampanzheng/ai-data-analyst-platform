# 07 Agent State / Tool Contract

## State

```text
question
intent
relevant_schema
sql_candidate
validated_sql
query_result
analysis_result
chart_artifact
final_answer
errors
trace_id
```

## Tools

### get_database_schema()
Returns relevant schema and business metadata.

### execute_sql(query)
Read-only, allowlisted, timeout-bounded.

### run_python_analysis(input)
Pandas/NumPy only against bounded query results; no OS/network/file primitives exposed to the model.

### create_chart(spec)
Produces a chart from structured data.

### generate_report(evidence)
Turns verified evidence into a concise business answer with sources/SQL/result references.
