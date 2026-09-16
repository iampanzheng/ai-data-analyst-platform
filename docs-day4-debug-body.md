# Day 4 Debug: Gateway -> FastAPI request body

This temporary diagnostic version logs the outbound request in the Spring Boot gateway and the inbound HTTP request in FastAPI.

Set `DEBUG_HTTP_BODY=true` and rebuild the `fastapi` and `gateway` services.

Expected evidence:
- Gateway `[FASTAPI_OUTBOUND] ... bodyLength=... body={"sql":"..."}`
- FastAPI `http_debug_inbound ... content-type=application/json ... body_length=... body={"sql":"..."}`

Interpretation:
- Gateway bodyLength > 0 but FastAPI body_length == 0: inspect transport/client adapter.
- Gateway bodyLength == 0: request construction/conversion issue inside RestClient.
- FastAPI body contains JSON but FastAPI still says missing body: inspect request-body middleware/parsing interaction.


## Fix 1
The debug middleware must replace `request._receive` with an async callable. ASGI receive is awaitable; a synchronous lambda is invalid and can cause downstream FastAPI request parsing to observe an empty body.
