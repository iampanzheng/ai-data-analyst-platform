# 06 FastAPI API Contract

## GET /health
Returns service/database readiness.

## GET /api/schema
Returns the application allowlisted PostgreSQL schema together with business metadata.

Response:

```json
{
  "schema_name": "public",
  "tables": [
    {
      "table_name": "city",
      "business_name": "city",
      "description": "Annual resident population estimates for incorporated U.S. places.",
      "source": "U.S. Census Bureau Vintage 2025",
      "update_frequency": "annual",
      "columns": [
        {
          "name": "population",
          "business_name": "Population",
          "description": "Estimated resident population.",
          "data_type": "bigint",
          "semantic_type": "measure",
          "nullable": false,
          "queryable": true
        }
      ]
    }
  ]
}
```

The endpoint combines the physical schema from `information_schema.columns` with `dataset_metadata` and `column_metadata`.

## POST /api/query
Request:

```json
{"sql":"SELECT name, population FROM city LIMIT 5"}
```

Response:

```json
{
  "columns": ["name", "population"],
  "rows": [["New York", 8584629]],
  "row_count": 1,
  "trace_id": "...",
  "execution_ms": 11.64
}
```

Validation failures return HTTP 400 with:

```json
{
  "detail": {
    "code": "TABLE_NOT_ALLOWED",
    "message": "Table not allowlisted: users",
    "trace_id": "..."
  }
}
```

## Future endpoints
- POST /api/analysis
- POST /api/chat
- GET /api/evaluations/{id}
