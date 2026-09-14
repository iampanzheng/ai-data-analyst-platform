# Day 2 — Schema + Metadata API

## Endpoint

`GET /api/schema`

The endpoint exposes only the application allowlisted `public` tables. It combines PostgreSQL's physical schema (`information_schema.columns`) with business metadata stored in `dataset_metadata` and `column_metadata`.

## Response shape

```json
{
  "schema_name": "public",
  "tables": [
    {
      "table_name": "city",
      "business_name": "city",
      "description": "...",
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

## Agent boundary

The metadata endpoint is the source of truth for schema-aware prompt construction. The SQL validator remains the independent policy gate. Metadata tells the model what can be queried; the validator enforces what may actually execute.
