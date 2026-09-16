# Day 4 Fix 2 — RestClient JSON body forwarding

Root cause: CorsConfig created `RestClient.builder()` itself. That bypassed Spring Boot auto-configuration and its HTTP message converters. `RestClient.body(Object)` relies on HTTP message conversion for JSON serialization.

Fix: remove the custom RestClient.Builder bean and let Spring Boot inject its auto-configured builder. FastApiQueryRequest remains an explicit DTO.

Symptom fixed: Gateway POST `/api/query` reaches FastAPI with the JSON body `{"sql":"..."}` instead of an empty body.
