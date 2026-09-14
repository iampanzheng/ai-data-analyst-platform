# Sprint 0 — Day 1

## Target

```text
Public data
   ↓
raw/
   ↓
ETL
   ↓
processed/
   ↓
PostgreSQL
   ↓
SQL query
```

## Public data

- U.S. Census Bureau Vintage 2025 city population estimates.
- U.S. Bureau of Labor Statistics May 2024 OEWS metropolitan occupation/wage dataset.

The runnable Day 1 slice loads Census city population first. BLS is staged because its geography is metropolitan area rather than incorporated city; we will not create a false city-level join.

## Commands

```bash
cp .env.example .env
make data-download   # optional; refreshes public raw files
make etl
make up
```

The checked-in Census fixture lets the demo work without internet access.

## First query

```sql
SELECT name, state, population, year
FROM city
ORDER BY population DESC
LIMIT 5;
```
