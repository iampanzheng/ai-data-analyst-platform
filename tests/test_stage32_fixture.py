import csv
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).parents[1]
ACS = ROOT / "data/raw/acs/acs_2024_city_profile_sample.csv"
OEWS = ROOT / "data/raw/bls/oews_2023_software_developers_metro_sample.csv"
ANCHORS = {"New York", "Los Angeles", "Chicago", "Houston", "Phoenix"}

def _rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def test_acs_stage32_fixture_contract():
    rows = _rows(ACS)
    assert {r["city"] for r in rows} == ANCHORS
    assert len(rows) == 5
    assert {r["year"] for r in rows} == {"2024"}
    assert all(Decimal(r["bachelors_degree_or_higher_pct"]) >= 0 for r in rows)
    assert all(Decimal(r["employment_rate_pct"]) >= 0 for r in rows)
    assert all(int(r["median_household_income"]) > 0 for r in rows)

def test_oews_stage32_fixture_contract_and_derived_median():
    rows = _rows(OEWS)
    assert {r["city"] for r in rows} == ANCHORS
    assert len(rows) == 5
    assert {r["year"] for r in rows} == {"2023"}
    assert {r["occupation"] for r in rows} == {"Software Developers"}
    assert {r["soc_code"] for r in rows} == {"15-1252"}
    assert {r["industry"] for r in rows} == {"All industries"}
    assert {r["geography_type"] for r in rows} == {"metropolitan_area"}
    for row in rows:
        expected = (Decimal(row["median_hourly_wage"]) * Decimal("2080")).quantize(Decimal("0.01"))
        assert Decimal(row["median_salary"]) == expected
        assert int(row["employment_count"]) > 0
        assert Decimal(row["mean_salary"]) > 0
