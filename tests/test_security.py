import pytest

from ai.analyst.app.security import SQLValidationError, validate_sql


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT name, population FROM city ORDER BY population DESC LIMIT 5",
        "SELECT c.name FROM city AS c JOIN salary AS s ON s.city_id = c.id LIMIT 5",
        "WITH x AS (SELECT name, population FROM city) SELECT * FROM x ORDER BY population DESC LIMIT 5",
        "SELECT COUNT(*) FROM public.city",
        "SELECT c.name FROM public.city c JOIN public.salary s ON s.city_id = c.id LIMIT 5",
        "WITH x AS (SELECT * FROM city), y AS (SELECT * FROM x) SELECT count(*) FROM y",
        "SELECT * FROM city;",
        'SELECT * FROM public."city"',
    ],
)
def test_allows_safe_queries(sql):
    result = validate_sql(sql)
    assert result.normalized_sql
    assert result.tables


@pytest.mark.parametrize(
    "sql,code",
    [
        ("", "SQL_EMPTY"),
        ("UPDATE city SET population = 1", "STATEMENT_NOT_READ_ONLY"),
        ("DELETE FROM city", "STATEMENT_NOT_READ_ONLY"),
        ("DROP TABLE city", "STATEMENT_NOT_READ_ONLY"),
        ("INSERT INTO city(name,state,population,year) VALUES ('x','XX',1,2025)", "STATEMENT_NOT_READ_ONLY"),
        ("SELECT * FROM city; SELECT * FROM salary", "MULTIPLE_STATEMENTS"),
        ("SELECT * FROM city -- comment", "SQL_COMMENTS_NOT_ALLOWED"),
        ("SELECT * FROM users", "TABLE_NOT_ALLOWED"),
        ("SELECT * FROM pg_catalog.pg_tables", "SCHEMA_NOT_ALLOWED"),
        ("SELECT * FROM public.city FOR UPDATE", "ROW_LOCKING_NOT_ALLOWED"),
        ("SELECT * INTO new_table FROM city", "SELECT_INTO_NOT_ALLOWED"),
        ("SELECT pg_sleep(10) FROM city", "FORBIDDEN_FUNCTION_OR_OPERATION"),
    ],
)
def test_rejects_unsafe_queries(sql, code):
    with pytest.raises(SQLValidationError) as exc:
        validate_sql(sql)
    assert exc.value.code == code


def test_rejects_cross_database_reference():
    with pytest.raises(SQLValidationError) as exc:
        validate_sql("SELECT * FROM analytics.city")
    assert exc.value.code == "SCHEMA_NOT_ALLOWED"


def test_allows_cte_name_not_as_physical_table():
    result = validate_sql("WITH x AS (SELECT * FROM city) SELECT * FROM x")
    assert result.tables == {"city"}


def test_normalizes_terminal_semicolon():
    result = validate_sql("SELECT name FROM city;")
    assert not result.normalized_sql.endswith(";")


def test_sql_length_limit():
    with pytest.raises(SQLValidationError) as exc:
        validate_sql("SELECT name FROM city " + (" " * 20_000))
    assert exc.value.code == "SQL_TOO_LONG"
