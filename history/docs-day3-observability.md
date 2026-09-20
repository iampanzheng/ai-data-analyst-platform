# Day 3 Observability Baseline

The API now accepts `X-Trace-ID`; if absent, it creates a UUID. The same trace id is returned in query responses/errors and emitted in structured JSON logs.

For SQL execution the baseline fields are:
- `event=sql_execution`
- `trace_id`
- `tables`
- `row_count`
- `execution_ms`

For request completion:
- `event=request_complete`
- `trace_id`
- `path`
- `total_execution_ms`
- `row_count`

This is intentionally a small baseline; OpenTelemetry/metrics backends are deferred until the service boundaries stabilize.
