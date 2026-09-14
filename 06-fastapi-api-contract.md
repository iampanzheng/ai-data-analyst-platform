# 06 FastAPI API Contract

## GET /health
Returns service/database readiness.

## GET /api/schema
Returns whitelisted table/column metadata.

## POST /api/query
Request:
```json
{"sql":"SELECT city, population FROM city LIMIT 5"}
```
Response:
```json
{"columns":["city","population"],"rows":[],"row_count":0}
```

## Future endpoints
- POST /api/analysis
- POST /api/chat
- GET /api/evaluations/{id}
