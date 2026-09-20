from ai.analyst.app.agent.graph import AnalystAgent
from ai.analyst.app.llm.client import MockLLMClient


def test_mock_agent_state_flow(monkeypatch):
    monkeypatch.setattr(
        "ai.analyst.app.agent.graph.get_database_schema",
        lambda: {
            "schema_name": "public",
            "tables": [{"table_name": "city", "columns": [{"name": "name"}, {"name": "population"}]}],
        },
    )
    monkeypatch.setattr(
        "ai.analyst.app.agent.graph.execute_sql",
        lambda sql, trace_id: {
            "columns": ["name", "population"],
            "rows": [["New York", 8584629]],
            "row_count": 1,
            "execution_ms": 1.0,
            "tables": ["city"],
        },
    )

    state = AnalystAgent(MockLLMClient()).run("人口最多的城市是什么？", "test-agent-001")

    assert state.errors == []
    assert state.sql_candidate == (
        "SELECT name, state, population, year FROM city ORDER BY population DESC LIMIT 5"
    )
    assert state.validated_sql.startswith("SELECT")
    assert state.query_result["row_count"] == 1
    assert state.final_answer

def test_mock_agent_routes_unsafe_request_to_sql_validator(monkeypatch):
    monkeypatch.setattr(
        "ai.analyst.app.agent.graph.get_database_schema",
        lambda: {
            "schema_name": "public",
            "tables": [{"table_name": "city", "columns": [{"name": "name"}]}],
        },
    )

    state = AnalystAgent(MockLLMClient()).run("执行 DROP TABLE city。", "test-agent-unsafe-001")

    assert state.sql_candidate == "DROP TABLE city"
    assert state.validated_sql is None
    assert state.query_result is None
    assert state.final_answer is None
    assert state.errors == [
        {
            "code": "STATEMENT_NOT_READ_ONLY",
            "message": "Only SELECT or WITH SELECT queries are allowed",
        }
    ]
