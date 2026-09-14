from __future__ import annotations

from dataclasses import dataclass
import re
import sqlglot
from sqlglot import exp

from .policy import ALLOWED_SCHEMA, ALLOWED_TABLES
MAX_SQL_LENGTH = 20_000


class SQLValidationError(ValueError):
    """Raised when SQL violates the application query policy."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class ValidatedQuery:
    normalized_sql: str
    tables: FrozenSet[str]


def _reject(code: str, message: str) -> None:
    raise SQLValidationError(code, message)


def _strip_terminal_semicolon(sql: str) -> str:
    sql = sql.strip()
    while sql.endswith(";"):
        sql = sql[:-1].rstrip()
    return sql


def _validate_comments(sql: str) -> None:
    if "--" in sql or "/*" in sql or "*/" in sql:
        _reject("SQL_COMMENTS_NOT_ALLOWED", "SQL comments are not allowed")


def _parse(sql: str) -> exp.Expression:
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except Exception as exc:  # pragma: no cover - exact parser text varies by version
        _reject("SQL_PARSE_ERROR", f"Invalid PostgreSQL SQL: {exc}")
    if len(statements) != 1 or statements[0] is None:
        _reject("MULTIPLE_STATEMENTS", "Only one SQL statement is allowed")
    return statements[0]


def _validate_statement_type(tree: exp.Expression) -> None:
    if not isinstance(tree, (exp.Select, exp.Union)):
        _reject("STATEMENT_NOT_READ_ONLY", "Only SELECT or WITH SELECT queries are allowed")


def _validate_select_semantics(tree: exp.Expression) -> None:
    if tree.find(exp.Into) is not None:
        _reject("SELECT_INTO_NOT_ALLOWED", "SELECT INTO is not allowed")

    # Locking reads are not needed by an analytics query and can create side effects.
    normalized = tree.sql(dialect="postgres").lower()
    if re.search(r"\bfor\s+(update|no\s+key\s+update|share|key\s+share)\b", normalized):
        _reject("ROW_LOCKING_NOT_ALLOWED", "FOR UPDATE/FOR SHARE locking is not allowed")

    # Defensive rejection of statement/session/admin constructs even if a parser version
    # represents them differently in the AST.
    forbidden_patterns = (
        r"\bpg_sleep\s*\(",
        r"\bdblink\s*\(",
        r"\bpostgres_fdw\b",
        r"\bcopy\b",
        r"\bcall\b",
        r"\bdo\b",
        r"\bexecute\b",
    )
    for pattern in forbidden_patterns:
        if re.search(pattern, normalized):
            _reject("FORBIDDEN_FUNCTION_OR_OPERATION", "Query contains a forbidden PostgreSQL operation")


def _extract_table_refs(tree: exp.Expression) -> tuple[set[str], set[str]]:
    cte_names = {
        cte.alias_or_name.lower()
        for cte in tree.find_all(exp.CTE)
        if cte.alias_or_name
    }
    tables: set[str] = set()
    unexpected_schemas: set[str] = set()

    for table in tree.find_all(exp.Table):
        name = table.name.lower()
        if name in cte_names:
            continue
        db = (table.args.get("db") or "").lower()
        catalog = (table.args.get("catalog") or "").lower()
        if db and db != ALLOWED_SCHEMA:
            unexpected_schemas.add(db)
        if catalog:
            _reject("CROSS_DATABASE_REFERENCE", "Cross-database table references are not allowed")
        tables.add(name)
    return tables, unexpected_schemas


def validate_sql(sql: str) -> ValidatedQuery:
    if not isinstance(sql, str) or not sql.strip():
        _reject("SQL_EMPTY", "SQL must not be empty")
    if len(sql) > MAX_SQL_LENGTH:
        _reject("SQL_TOO_LONG", f"SQL exceeds maximum length of {MAX_SQL_LENGTH} characters")

    _validate_comments(sql)
    raw = _strip_terminal_semicolon(sql)
    if ";" in raw:
        _reject("MULTIPLE_STATEMENTS", "Only one SQL statement is allowed")

    tree = _parse(raw)
    _validate_statement_type(tree)
    _validate_select_semantics(tree)

    tables, unexpected_schemas = _extract_table_refs(tree)
    if unexpected_schemas:
        _reject(
            "SCHEMA_NOT_ALLOWED",
            f"Only schema '{ALLOWED_SCHEMA}' is allowed: {', '.join(sorted(unexpected_schemas))}",
        )
    if not tables:
        _reject("TABLE_REFERENCE_REQUIRED", "Query must reference an allowlisted table")
    unexpected = tables - ALLOWED_TABLES
    if unexpected:
        _reject("TABLE_NOT_ALLOWED", f"Table not allowlisted: {', '.join(sorted(unexpected))}")

    normalized = tree.sql(dialect="postgres", pretty=False)
    return ValidatedQuery(normalized_sql=normalized, tables=frozenset(tables))
