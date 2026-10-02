import os
import pytest
from ai.analyst.app.main import execute_query

pytestmark = pytest.mark.integration

@pytest.fixture(autouse=True)
def require_database():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not set")

def test_stage32_salary_and_geography_provenance():
    cols, rows, _ms, _tables = execute_query(
        "SELECT c.name, s.median_salary, s.geography_type, s.geography_name "
        "FROM salary s JOIN city c ON c.id=s.city_id ORDER BY s.median_salary DESC LIMIT 1",
        "stage32-salary",
    )
    assert cols == ["name", "median_salary", "geography_type", "geography_name"]
    assert rows[0][0] == "Los Angeles"
    assert float(rows[0][1]) == pytest.approx(153566.40)
    assert rows[0][2] == "metropolitan_area"
    assert "Los Angeles-Long Beach-Anaheim" in rows[0][3]

def test_stage32_acs_income_and_education():
    _cols, income_rows, _ms, _tables = execute_query(
        "SELECT c.name, e.value FROM economic_indicator e JOIN city c ON c.id=e.city_id "
        "WHERE e.indicator='Median household income' AND e.year=2024 ORDER BY e.value DESC LIMIT 1",
        "stage32-income",
    )
    assert income_rows[0][0] == "Phoenix"
    assert float(income_rows[0][1]) == pytest.approx(85246)

    _cols, education_rows, _ms, _tables = execute_query(
        "SELECT c.name, e.value FROM education e JOIN city c ON c.id=e.city_id "
        "WHERE e.education_level='Bachelor''s degree or higher' AND e.year=2024 ORDER BY e.value DESC LIMIT 1",
        "stage32-education",
    )
    assert education_rows[0][0] == "Chicago"
    assert float(education_rows[0][1]) == pytest.approx(46.4)

def test_stage32_expected_row_counts():
    _cols, rows, _ms, _tables = execute_query(
        "SELECT (SELECT COUNT(*) FROM salary), (SELECT COUNT(*) FROM employment), "
        "(SELECT COUNT(*) FROM education), (SELECT COUNT(*) FROM economic_indicator)",
        "stage32-counts",
    )
    assert rows == [[5, 5, 5, 10]]
