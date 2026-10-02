import csv, os, time
from pathlib import Path
import psycopg

DATABASE_URL=os.getenv("DATABASE_URL", "postgresql://analyst:analyst@postgres:5432/ai_analyst")
CITY_CSV=Path("/data/city_population_sample.csv")
ACS_CSV=Path("/data/acs_2024_city_profile_sample.csv")
OEWS_CSV=Path("/data/oews_2023_software_developers_metro_sample.csv")

for _ in range(30):
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            break
    except psycopg.OperationalError:
        time.sleep(2)
else:
    raise SystemExit("PostgreSQL not ready")

def ensure_stage32_schema(cur):
    # Existing Docker volumes do not rerun docker-entrypoint-initdb.d, so keep
    # the Stage 3.2 additions idempotent in the ETL path as well as schema.sql.
    cur.execute("ALTER TABLE employment ADD COLUMN IF NOT EXISTS occupation_code TEXT NOT NULL DEFAULT ''")
    cur.execute("ALTER TABLE employment ADD COLUMN IF NOT EXISTS geography_type TEXT NOT NULL DEFAULT 'metropolitan_area'")
    cur.execute("ALTER TABLE employment ADD COLUMN IF NOT EXISTS geography_name TEXT NOT NULL DEFAULT ''")
    cur.execute("ALTER TABLE employment ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT ''")
    cur.execute("ALTER TABLE salary ADD COLUMN IF NOT EXISTS occupation_code TEXT NOT NULL DEFAULT ''")
    cur.execute("ALTER TABLE salary ADD COLUMN IF NOT EXISTS geography_type TEXT NOT NULL DEFAULT 'metropolitan_area'")
    cur.execute("ALTER TABLE salary ADD COLUMN IF NOT EXISTS geography_name TEXT NOT NULL DEFAULT ''")
    cur.execute("ALTER TABLE salary ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT ''")
    cur.execute("ALTER TABLE education ALTER COLUMN population DROP NOT NULL")
    cur.execute("ALTER TABLE education ADD COLUMN IF NOT EXISTS value NUMERIC(12,4)")
    cur.execute("ALTER TABLE education ADD COLUMN IF NOT EXISTS unit TEXT")
    cur.execute("ALTER TABLE education ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT ''")
    cur.execute("ALTER TABLE economic_indicator ADD COLUMN IF NOT EXISTS unit TEXT NOT NULL DEFAULT ''")
    cur.execute("ALTER TABLE economic_indicator ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT ''")


def sync_stage32_metadata(cur):
    datasets = [
        ("employment", "Curated metro-area occupational employment sample anchored to demo cities; geography is explicitly metropolitan, not city-level.", "U.S. Bureau of Labor Statistics OEWS May 2023", "annual"),
        ("salary", "Curated metro-area occupational wage sample anchored to demo cities; median_salary is derived by annualizing the published OEWS median hourly wage.", "U.S. Bureau of Labor Statistics OEWS May 2023", "annual"),
        ("education", "City-level education attainment indicators for the curated richer-data sample.", "U.S. Census Bureau ACS 1-Year 2024", "annual"),
        ("economic_indicator", "Selected city-level economic indicators for the curated richer-data sample.", "U.S. Census Bureau ACS 1-Year 2024", "annual"),
    ]
    for row in datasets:
        cur.execute(
            """
            INSERT INTO dataset_metadata(dataset_name, description, source, update_frequency)
            VALUES (%s,%s,%s,%s)
            ON CONFLICT(dataset_name) DO UPDATE SET
                description=EXCLUDED.description, source=EXCLUDED.source, update_frequency=EXCLUDED.update_frequency
            """,
            row,
        )

    columns = [
        ("employment", "occupation_code", "Occupation Code", "Standard Occupational Classification code from OEWS.", "text", "category"),
        ("employment", "geography_type", "Geography Type", "Statistical geography grain; Stage 3.2 OEWS rows are metropolitan-area estimates.", "text", "geography_type"),
        ("employment", "geography_name", "Geography Name", "Official OEWS metropolitan-area name represented by the record.", "text", "geography_name"),
        ("employment", "source", "Source", "Source label for the employment estimate.", "text", "provenance"),
        ("salary", "occupation_code", "Occupation Code", "Standard Occupational Classification code from OEWS.", "text", "category"),
        ("salary", "median_salary", "Annualized Median Salary", "Derived annualized median wage: OEWS median hourly wage multiplied by 2,080 hours; not a directly published BLS annual-median field.", "numeric", "measure"),
        ("salary", "geography_type", "Geography Type", "Statistical geography grain; Stage 3.2 OEWS rows are metropolitan-area estimates.", "text", "geography_type"),
        ("salary", "geography_name", "Geography Name", "Official OEWS metropolitan-area name represented by the record.", "text", "geography_name"),
        ("salary", "source", "Source", "Source label for the wage estimate.", "text", "provenance"),
        ("education", "population", "Population", "Optional count when the source metric is a population count; null for percentage metrics.", "integer", "measure"),
        ("education", "value", "Value", "Numeric value for the education indicator.", "numeric", "measure"),
        ("education", "unit", "Unit", "Measurement unit such as percent.", "text", "unit"),
        ("education", "source", "Source", "Source label for the education estimate.", "text", "provenance"),
        ("economic_indicator", "unit", "Unit", "Measurement unit such as USD or percent.", "text", "unit"),
        ("economic_indicator", "source", "Source", "Source label for the economic indicator.", "text", "provenance"),
    ]
    for dataset_name, column_name, business_name, description, data_type, semantic_type in columns:
        cur.execute(
            """
            INSERT INTO column_metadata(dataset_id,column_name,business_name,description,data_type,semantic_type)
            SELECT id,%s,%s,%s,%s,%s FROM dataset_metadata WHERE dataset_name=%s
            ON CONFLICT(dataset_id,column_name) DO UPDATE SET
                business_name=EXCLUDED.business_name, description=EXCLUDED.description,
                data_type=EXCLUDED.data_type, semantic_type=EXCLUDED.semantic_type
            """,
            (column_name,business_name,description,data_type,semantic_type,dataset_name),
        )

def city_id(cur, city, state):
    cur.execute("SELECT id FROM city WHERE name=%s AND state=%s ORDER BY year DESC LIMIT 1", (city, state))
    row=cur.fetchone()
    if not row:
        raise RuntimeError(f"Stage 3.2 fixture city not found: {city}, {state}")
    return row[0]

with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        ensure_stage32_schema(cur)
        sync_stage32_metadata(cur)
        cur.execute("""
            TRUNCATE TABLE employment, salary, education, economic_indicator, city RESTART IDENTITY
        """)
        with CITY_CSV.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cur.execute(
                    "INSERT INTO city(name,state,population,year,source) VALUES (%s,%s,%s,%s,%s)",
                    (row["city"], row["state"], int(row["population"]), int(row["year"]), row["source"]),
                )

        with ACS_CSV.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cid=city_id(cur,row["city"],row["state"])
                year=int(row["year"]); source=row["source"]
                cur.execute(
                    "INSERT INTO education(city_id,education_level,population,value,unit,year,source) VALUES (%s,%s,NULL,%s,%s,%s,%s)",
                    (cid,"Bachelor's degree or higher",row["bachelors_degree_or_higher_pct"],"percent",year,source),
                )
                cur.execute(
                    "INSERT INTO economic_indicator(city_id,indicator,value,unit,year,source) VALUES (%s,%s,%s,%s,%s,%s)",
                    (cid,"Median household income",row["median_household_income"],"USD",year,source),
                )
                cur.execute(
                    "INSERT INTO economic_indicator(city_id,indicator,value,unit,year,source) VALUES (%s,%s,%s,%s,%s,%s)",
                    (cid,"Employment rate",row["employment_rate_pct"],"percent",year,source),
                )

        with OEWS_CSV.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cid=city_id(cur,row["city"],row["state"])
                common=(cid,row["industry"],row["occupation"],row["soc_code"],int(row["employment_count"]),int(row["year"]),row["geography_type"],row["geography_name"],row["source"])
                cur.execute(
                    "INSERT INTO employment(city_id,industry,occupation,occupation_code,employment_count,year,geography_type,geography_name,source) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    common,
                )
                cur.execute(
                    "INSERT INTO salary(city_id,occupation,occupation_code,median_salary,mean_salary,year,geography_type,geography_name,source) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (cid,row["occupation"],row["soc_code"],row["median_salary"],row["mean_salary"],int(row["year"]),row["geography_type"],row["geography_name"],row["source"]),
                )

print(f"ETL loaded city={CITY_CSV.name}, ACS={ACS_CSV.name}, OEWS={OEWS_CSV.name}")
