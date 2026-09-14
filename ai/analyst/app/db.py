import os
from contextlib import contextmanager

import psycopg

DATABASE_URL = os.environ["DATABASE_URL"]
SQL_MAX_ROWS = int(os.getenv("SQL_MAX_ROWS", "1000"))
SQL_STATEMENT_TIMEOUT_MS = int(os.getenv("SQL_STATEMENT_TIMEOUT_MS", "3000"))


@contextmanager
def connection():
    with psycopg.connect(DATABASE_URL) as conn:
        yield conn
