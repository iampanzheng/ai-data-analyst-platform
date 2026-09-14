from dataclasses import dataclass
import re

import sqlglot
from sqlglot import exp

ALLOWED_TABLES = {"city", "employment", "salary", "education", "economic_indicator"}
FORBIDDEN_WORDS = {
    "insert", "update", "delete", "drop", "alter", "truncate", "create",
    "grant", "revoke", "comment", "copy", "call", "do", "execute", "merge",
}


@dataclass(frozen=True)
class ValidatedQuery:
    normalized_sql: str


def validate_sql(sql: str) -> ValidatedQuery:
    if not sql or not sql.strip():
        raise ValueError("SQL must not be empty")
    raw = sql.strip()
    if ";" in raw.rstrip(";"):
        raise ValueError("only one SQL statement is allowed")
    raw = raw.rstrip(";").strip()
    if "--" in raw or "/*" in raw or "*/" in raw:
        raise ValueError("SQL comments are not allowed")
    try:
        statements = sqlglot.parse(raw, read="postgres")
    except Exception as exc:
        raise ValueError(f"invalid SQL: {exc}") from exc
    if len(statements) != 1:
        raise ValueError("only one SQL statement is allowed")
    tree = statements[0]
    if not isinstance(tree, (exp.Select, exp.Union, exp.With)):
        raise ValueError("only SELECT or WITH queries are allowed")
    lowered = raw.lower()
    for word in FORBIDDEN_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            raise ValueError(f"forbidden SQL operation: {word}")
    tables = {t.name.lower() for t in tree.find_all(exp.Table)}
    if not tables:
        raise ValueError("query must reference an allowlisted table")
    unexpected = tables - ALLOWED_TABLES
    if unexpected:
        raise ValueError(f"table not allowed: {', '.join(sorted(unexpected))}")
    return ValidatedQuery(normalized_sql=tree.sql(dialect="postgres"))
