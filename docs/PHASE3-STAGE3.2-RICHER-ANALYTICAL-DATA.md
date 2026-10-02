# Phase 3 — Stage 3.2: Richer Analytical Data

Status: **Implemented; pending local Compose verification**

## Goal

Replace the city-only analytical fixture with a small, reproducible, source-backed multi-table dataset suitable for joins, aggregations, evidence-aware answers, and the next Python/visualization stages.

Stage 3.2 does **not** redesign SQL security, model routing, fallback, or the Analyst Agent orchestration.

## Data design

The richer fixture intentionally uses explicit source years and geography grains rather than forcing all datasets into a fictional common year/grain.

| Domain | Source | Reference year | Grain | Rows |
|---|---|---:|---|---:|
| `city` | U.S. Census population fixture | 2025 | incorporated place | 15 |
| `education` | U.S. Census Bureau ACS 1-Year | 2024 | city/place | 5 |
| `economic_indicator` | U.S. Census Bureau ACS 1-Year | 2024 | city/place | 10 |
| `employment` | U.S. BLS OEWS | 2023 | metropolitan area | 5 |
| `salary` | U.S. BLS OEWS | 2023 | metropolitan area | 5 |

Five anchor cities are shared across the richer-data fixture: New York, Los Angeles, Chicago, Houston, and Phoenix.

## ACS fixture

`data/raw/acs/acs_2024_city_profile_sample.csv` contains: 

- bachelor's degree or higher (%)
- median household income (USD)
- employment rate (%)

These are city/place-level 2024 ACS 1-Year profile values. See `data/raw/acs/README.md` for official source pages.

The ETL maps the education percentage to `education.value` with `unit=percent`; the legacy `education.population` field is nullable for percentage metrics. Median household income and employment rate are loaded as two `economic_indicator` records per city.

## OEWS fixture and geography provenance

`data/raw/bls/oews_2023_software_developers_metro_sample.csv` contains Software Developers (SOC 15-1252) data for five metropolitan areas.

OEWS area estimates are **metropolitan-area estimates**, not strict city-level measurements. Stage 3.2 therefore adds:

```text
occupation_code
geography_type
geography_name
source
```

to the employment/salary evidence model. `city_id` is an anchor that allows the demo to join these metro estimates to a familiar city; it does not change the statistical geography of the source estimate.

### Derived median salary

The static OEWS area tables publish median hourly wage and annual mean wage. To preserve the existing `median_salary` field, Stage 3.2 stores a clearly documented **derived annualized median**:

```text
median_salary = published median_hourly_wage × 2,080
```

This field must not be described as a directly published BLS annual-median estimate. `mean_salary` remains the directly published annual mean wage.

## Existing-volume migration

PostgreSQL init scripts do not rerun for an existing Docker volume. Therefore the ETL performs idempotent Stage 3.2 schema upgrades and also upserts `dataset_metadata` / `column_metadata`. This keeps existing developer databases consistent with fresh databases.

## Planner guardrails

The SQL planner now explicitly:

- respects `geography_type` / `geography_name`;
- does not relabel metro estimates as city-level facts;
- keeps materially different reference years explicit when joining datasets.

The final-answer prompt also preserves the verified statistical geography.

## Evaluation dataset

The current evaluation dataset is version `1.1-stage3.2` and contains 35 cases.

- DA-001..DA-030 retain the historical Phase 2 task set, with DA-028/029 expected results updated for the now-populated salary table.
- DA-031..DA-035 add richer-data coverage for OEWS salary/employment, ACS income/education, and a cross-year city + education join.

Frozen Stage 2.2 reports remain historical 30-case baselines and are not rewritten. Evaluation reports now read `dataset_version` from the dataset file instead of hard-coding `1.0`.

## Verification performed in packaging environment

```text
compileall                                      PASS
tests/test_stage32_fixture.py                   2 passed
evaluation/dataset.json JSON Schema validation PASS (35 cases)
```

The packaging host lacks project dependencies such as `sqlglot`/`psycopg` and has no Docker daemon, so the full authoritative suite must run in the normal Compose environment.

## Local acceptance

Run:

```bash
docker compose up -d --build postgres etl fastapi
docker compose exec fastapi pytest -q
curl -sS http://localhost:8000/api/schema
```

Expected evidence after ETL:

```text
city               15 rows  2025–2025
salary              5 rows  2023–2023
employment           5 rows  2023–2023
education            5 rows  2024–2024
economic_indicator  10 rows  2024–2024
```

Useful smoke queries:

```sql
SELECT c.name, s.median_salary, s.geography_name
FROM salary s JOIN city c ON c.id=s.city_id
ORDER BY s.median_salary DESC LIMIT 1;

SELECT c.name, e.value
FROM economic_indicator e JOIN city c ON c.id=e.city_id
WHERE e.indicator='Median household income' AND e.year=2024
ORDER BY e.value DESC LIMIT 1;
```

Expected leaders in this curated fixture: Los Angeles for derived annualized software-developer median wage, Phoenix for median household income, Chicago for bachelor's-degree-or-higher percentage, and New York metro for software-developer employment count.

## Next stage

After local Compose verification closes Stage 3.2, proceed to **Stage 3.3 — Controlled Python Analysis**. Any Python execution capability must preserve the project principle `request → validate → execute → evidence` and must not expose unrestricted arbitrary code execution.
