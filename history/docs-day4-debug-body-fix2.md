# Day 4 Debug Body Fix 2

Root cause: the HTTP body debug implementation used Starlette's `@app.middleware("http")`
layer and replaced the request receive channel. Even after using an async replacement, this
interacts with Starlette's middleware request boundary and can leave downstream FastAPI parsing
with an empty body.

Fix: replace it with a pure ASGI middleware. The wrapper observes `http.request` messages while
passing each message through unchanged. It logs the accumulated body only after downstream
processing completes. The middleware never reads/replays the body ahead of FastAPI request parsing.

Expected diagnostic result:

- Gateway outbound body length > 0
- FastAPI debug inbound body length > 0
- FastAPI `/api/query` returns 200
