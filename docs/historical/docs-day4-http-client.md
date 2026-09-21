# Day 4 HTTP Client Decision

The Spring Boot Gateway uses Java 21 `java.net.http.HttpClient` for calls to FastAPI.

## Why
- The Gateway-to-FastAPI path is now explicitly controlled at the HTTP request level.
- JSON is serialized with Spring Boot's Jackson `ObjectMapper`.
- The request body is sent with `HttpRequest.BodyPublishers.ofString(...)`.
- A 5-second connect timeout is configured.
- Non-2xx FastAPI responses are surfaced through `FastApiProxyException`.

## Removed
The gateway no longer depends on `RestClient` for this integration. The temporary HTTP-body debug middleware was also removed from FastAPI after the transport issue was isolated.
