# Sprint 0 Day 1 Fix 1

## Problem
ETL attempted:

```sql
TRUNCATE TABLE city RESTART IDENTITY;
```

PostgreSQL rejected this because `employment`, `salary`, `education`, and `economic_indicator` reference `city` through foreign keys.

## Fix
The Day 1 ETL now clears the dependent analytics tables and `city` together before loading the CSV:

```sql
TRUNCATE TABLE
    employment,
    salary,
    education,
    economic_indicator,
    city
RESTART IDENTITY;
```

This keeps the fixture reload deterministic without using `CASCADE`.
