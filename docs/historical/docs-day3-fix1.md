# Day 3 Fix 1

Fix SQLGlot Identifier handling for schema-qualified and catalog-qualified tables.
The PostgreSQL dialect represents Table.args["db"] and Table.args["catalog"] as Identifier nodes in the pinned SQLGlot version, so validator normalization now reads `.name` safely.

Also adds httpx for FastAPI TestClient and a regression case for quoted public.city.
