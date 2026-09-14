from ai.analyst.app.policy import ALLOWED_SCHEMA, ALLOWED_TABLES


def test_shared_sql_policy():
    assert ALLOWED_SCHEMA == "public"
    assert ALLOWED_TABLES == {
        "city",
        "employment",
        "salary",
        "education",
        "economic_indicator",
    }
