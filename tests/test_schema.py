from ai.analyst.app.main import ALLOWED_SCHEMA, ALLOWED_TABLES


def test_schema_policy_is_aligned_with_validator_allowlist():
    assert ALLOWED_SCHEMA == "public"
    assert set(ALLOWED_TABLES) == {
        "city",
        "employment",
        "salary",
        "education",
        "economic_indicator",
    }
