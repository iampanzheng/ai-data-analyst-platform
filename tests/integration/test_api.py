import os

import pytest
from fastapi.testclient import TestClient

from ai.analyst.app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def client():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not set")
    return TestClient(app)


def test_schema_endpoint_returns_metadata(client):
    response = client.get("/api/schema", headers={"X-Trace-ID": "day3-schema-test"})
    assert response.status_code == 200
    body = response.json()
    assert body["schema_name"] == "public"
    city = next(t for t in body["tables"] if t["table_name"] == "city")
    assert city["columns"]
    population = next(c for c in city["columns"] if c["name"] == "population")
    assert population["queryable"] is True


def test_query_endpoint_propagates_trace_id(client):
    trace_id = "day3-query-test"
    response = client.post(
        "/api/query",
        headers={"X-Trace-ID": trace_id},
        json={"sql": "SELECT name FROM city ORDER BY population DESC LIMIT 1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["trace_id"] == trace_id
    assert body["rows"][0][0] == "New York"


def test_query_endpoint_rejects_unsafe_sql(client):
    trace_id = "day3-unsafe-test"
    response = client.post(
        "/api/query",
        headers={"X-Trace-ID": trace_id},
        json={"sql": "DROP TABLE city"},
    )
    assert response.status_code == 400
    body = response.json()["detail"]
    assert body["code"] == "STATEMENT_NOT_READ_ONLY"
    assert body["trace_id"] == trace_id
