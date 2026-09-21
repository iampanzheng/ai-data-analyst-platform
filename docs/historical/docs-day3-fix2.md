# Day 3 Fix 2

Fix SQLGlot 26.16.4 table qualifier handling. `Table.args["db"]` and `Table.args["catalog"]` may be `exp.Identifier`, not Python strings.

Changes:
- Normalize qualifier identifiers through `.name`.
- Preserve public-schema allowlist.
- Add regression coverage for qualified and quoted public table names.
- Include `httpx` because FastAPI/Starlette TestClient requires it.
