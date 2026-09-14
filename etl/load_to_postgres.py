import csv, os, time
from pathlib import Path
import psycopg

DATABASE_URL=os.getenv("DATABASE_URL", "postgresql://analyst:analyst@postgres:5432/ai_analyst")
CSV_PATH=Path("/data/city_population_sample.csv")
for _ in range(30):
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            break
    except psycopg.OperationalError:
        time.sleep(2)
else:
    raise SystemExit("PostgreSQL not ready")

with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        # Day 1 ETL owns the demo analytics dataset. Clear dependent tables first
        # so city can be reloaded without violating foreign-key constraints.
        cur.execute("""
            TRUNCATE TABLE
                employment,
                salary,
                education,
                economic_indicator,
                city
            RESTART IDENTITY
        """)
        with CSV_PATH.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cur.execute(
                    "INSERT INTO city(name,state,population,year,source) VALUES (%s,%s,%s,%s,%s)",
                    (row["city"], row["state"], int(row["population"]), int(row["year"]), row["source"]),
                )
print(f"ETL loaded city rows from {CSV_PATH}")
