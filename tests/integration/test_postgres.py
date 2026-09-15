import os

import psycopg
import pytest

from ai.analyst.app.security import validate_sql

DATABASE_URL = os.getenv("DATABASE_URL")


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def db_url():
    if not DATABASE_URL:
        pytest.skip("DATABASE_URL is not set; run inside the FastAPI/ETL environment")
    return DATABASE_URL


def test_real_postgres_has_expected_city_rows(db_url):
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM city")
            count = cur.fetchone()[0]
            assert count >= 15


def test_real_postgres_safe_query_returns_expected_shape(db_url):
    validated = validate_sql(
        "SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5"
    )
    with psycopg.connect(db_url) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        with conn.cursor() as cur:
            cur.execute(validated.normalized_sql)
            rows = cur.fetchall()
    assert len(rows) == 5
    assert rows[0][0] == "New York"
    assert rows[0][2] == 8584629


def test_real_postgres_read_only_blocks_write(db_url):
    with psycopg.connect(db_url) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            conn.execute("DELETE FROM city")
