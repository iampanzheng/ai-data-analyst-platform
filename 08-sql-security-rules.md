# 08 SQL Security Rules

1. Only one statement.
2. SELECT / WITH only.
3. Table allowlist required.
4. Read-only transaction required.
5. Statement timeout required.
6. Result row cap required.
7. No comments or opaque dynamic SQL tricks should bypass validation.
8. Do not accept model-generated SQL as trusted input.
9. Log the normalized SQL, trace_id, execution time, row count, and rejection reason; never log secrets.
10. V2 may add column-level permissions and query cost controls.
