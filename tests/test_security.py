import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "ai" / "analyst"))
from app.security import validate_sql
import pytest


def test_select_allowed():
    q = validate_sql("SELECT name, population FROM city ORDER BY population DESC LIMIT 5")
    assert "SELECT" in q.normalized_sql

@pytest.mark.parametrize("sql", [
    "DELETE FROM city",
    "DROP TABLE city",
    "SELECT * FROM secret_table",
    "SELECT * FROM city; SELECT * FROM salary",
    "SELECT * FROM city -- comment",
])
def test_reject_unsafe(sql):
    with pytest.raises(ValueError):
        validate_sql(sql)
