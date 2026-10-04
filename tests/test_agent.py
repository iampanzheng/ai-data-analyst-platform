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
    assert state.provider == "mock"

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


def test_agent_runs_controlled_analysis_only_for_analysis_question(monkeypatch):
    from ai.analyst.app.llm.client import LLMClient
    from ai.analyst.app.llm.models import LLMResponse

    class AnalysisLLM(LLMClient):
        provider = "test"
        disable_thinking = False

        def __init__(self):
            self.calls = []

        def chat(self, messages, *, temperature=0.0):
            user = next((m.content for m in reversed(messages) if m.role == "user"), "")
            self.calls.append(user)
            if "Generate SQL" in user:
                return LLMResponse(
                    content="SELECT population, year FROM city ORDER BY year",
                    model="test-model",
                    provider=self.provider,
                )
            if "Generate analysis plan" in user:
                return LLMResponse(
                    content='{"operations":[{"operation":"percent_change","column":"population"}]}',
                    model="test-model",
                    provider=self.provider,
                )
            return LLMResponse(
                content="population increased by 50%",
                model="test-model",
                provider=self.provider,
            )

    monkeypatch.setattr(
        "ai.analyst.app.agent.graph.get_database_schema",
        lambda: {"schema_name": "public", "tables": []},
    )
    monkeypatch.setattr(
        "ai.analyst.app.agent.graph.execute_sql",
        lambda sql, trace_id: {
            "columns": ["population", "year"],
            "rows": [[100, 2024], [150, 2025]],
            "row_count": 2,
            "execution_ms": 1.0,
            "tables": ["city"],
        },
    )

    llm = AnalysisLLM()
    state = AnalystAgent(llm).run("人口增长率是多少？", "test-analysis-001")

    assert state.errors == []
    assert state.analysis_result == {
        "operations": [
            {
                "operation": "percent_change",
                "column": "population",
                "first": 100.0,
                "last": 150.0,
                "percent_change": 50.0,
            }
        ]
    }
    assert len(llm.calls) == 3
    assert "Controlled analysis result" in llm.calls[-1]


def test_agent_skips_controlled_analysis_for_plain_query(monkeypatch):
    monkeypatch.setattr(
        "ai.analyst.app.agent.graph.get_database_schema",
        lambda: {"schema_name": "public", "tables": []},
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

    state = AnalystAgent(MockLLMClient()).run("人口最多的城市是什么？", "test-analysis-skip-001")

    assert state.errors == []
    assert state.analysis_result is None


def test_agent_repairs_precomputed_correlation_sql_before_execution(monkeypatch):
    from ai.analyst.app.llm.client import LLMClient
    from ai.analyst.app.llm.models import LLMResponse

    class RepairLLM(LLMClient):
        provider = "test"
        disable_thinking = False

        def __init__(self):
            self.calls = []

        def chat(self, messages, *, temperature=0.0):
            user = next((m.content for m in reversed(messages) if m.role == "user"), "")
            self.calls.append(user)
            if "Regenerate raw-row SQL" in user:
                return LLMResponse(
                    content=(
                        "SELECT c.population, e.value AS bachelor_pct "
                        "FROM city c JOIN education e ON c.id = e.city_id "
                        "WHERE c.year = 2025 AND e.year = 2024 "
                        "AND e.education_level = 'Bachelor''s degree or higher'"
                    ),
                    model="test-model",
                    provider=self.provider,
                )
            if "Generate SQL" in user:
                return LLMResponse(
                    content=(
                        "SELECT CORR(c.population::numeric, e.value::numeric) AS correlation "
                        "FROM city c JOIN education e ON c.id = e.city_id"
                    ),
                    model="test-model",
                    provider=self.provider,
                )
            if "Generate analysis plan" in user:
                return LLMResponse(
                    content='{"operations":[{"operation":"correlation","x":"population","y":"bachelor_pct"}]}',
                    model="test-model",
                    provider=self.provider,
                )
            return LLMResponse(
                content="相关系数为 1.0。",
                model="test-model",
                provider=self.provider,
            )

    monkeypatch.setattr(
        "ai.analyst.app.agent.graph.get_database_schema",
        lambda: {"schema_name": "public", "tables": []},
    )
    executed = []
    def fake_execute(sql, trace_id):
        executed.append(sql)
        return {
            "columns": ["population", "bachelor_pct"],
            "rows": [[100, 10], [200, 20], [300, 30]],
            "row_count": 3,
            "execution_ms": 1.0,
            "tables": ["city", "education"],
        }
    monkeypatch.setattr("ai.analyst.app.agent.graph.execute_sql", fake_execute)

    llm = RepairLLM()
    state = AnalystAgent(llm).run("分析人口与本科及以上比例的相关性。", "test-analysis-repair-001")

    assert state.errors == []
    assert len(executed) == 1
    assert "CORR(" not in executed[0].upper()
    assert state.analysis_result["operations"][0]["operation"] == "correlation"
    assert state.analysis_result["operations"][0]["pearson_r"] == 1.0
    assert len(llm.calls) == 4


def test_sql_precompute_guard_is_scoped_by_analysis_kind():
    from ai.analyst.app.agent.graph import _sql_precomputes_controlled_analysis

    assert _sql_precomputes_controlled_analysis(
        "SELECT CORR(x, y) FROM city", "correlation"
    )
    assert _sql_precomputes_controlled_analysis(
        "SELECT MIN(x), MAX(x), AVG(x) FROM city", "descriptive_stats"
    )
    assert _sql_precomputes_controlled_analysis(
        "SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY x) FROM city", "descriptive_stats"
    )
    assert _sql_precomputes_controlled_analysis(
        "SELECT LAG(x) OVER (ORDER BY id) FROM city", "percent_change"
    )
    assert not _sql_precomputes_controlled_analysis(
        "SELECT MIN(x) FROM city", "correlation"
    )
    assert not _sql_precomputes_controlled_analysis(
        "SELECT x, y FROM city", "correlation"
    )


def test_agent_builds_controlled_chart_only_for_visualization_question(monkeypatch):
    from ai.analyst.app.llm.client import LLMClient
    from ai.analyst.app.llm.models import LLMResponse

    class ChartLLM(LLMClient):
        provider = "test"
        disable_thinking = False

        def __init__(self):
            self.calls = []

        def chat(self, messages, *, temperature=0.0):
            user = next((m.content for m in reversed(messages) if m.role == "user"), "")
            self.calls.append(user)
            if "Generate SQL" in user:
                return LLMResponse(
                    content="SELECT name, population FROM city ORDER BY population DESC LIMIT 5",
                    model="test-model",
                    provider=self.provider,
                )
            if "Generate chart plan" in user:
                return LLMResponse(
                    content='{"chart_type":"bar","x":"name","y":"population","title":"Top city population"}',
                    model="test-model",
                    provider=self.provider,
                )
            return LLMResponse(
                content="A has the largest population.",
                model="test-model",
                provider=self.provider,
            )

    monkeypatch.setattr(
        "ai.analyst.app.agent.graph.get_database_schema",
        lambda: {"schema_name": "public", "tables": []},
    )
    monkeypatch.setattr(
        "ai.analyst.app.agent.graph.execute_sql",
        lambda sql, trace_id: {
            "columns": ["name", "population"],
            "rows": [["A", 30], ["B", 20], ["C", 10]],
            "row_count": 3,
            "execution_ms": 1.0,
            "tables": ["city"],
        },
    )

    llm = ChartLLM()
    state = AnalystAgent(llm).run("用柱状图显示人口最多的城市。", "test-chart-001")

    assert state.errors == []
    assert state.chart_artifact == {
        "chart_type": "bar",
        "title": "Top city population",
        "x": {"column": "name"},
        "y": {"column": "population"},
        "points": [
            {"x": "A", "y": 30.0},
            {"x": "B", "y": 20.0},
            {"x": "C", "y": 10.0},
        ],
        "point_count": 3,
        "source": "verified_query_result",
    }
    assert len(llm.calls) == 3
    assert "Generate chart plan" in llm.calls[1]


def test_agent_skips_chart_for_plain_question(monkeypatch):
    monkeypatch.setattr(
        "ai.analyst.app.agent.graph.get_database_schema",
        lambda: {"schema_name": "public", "tables": []},
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

    state = AnalystAgent(MockLLMClient()).run("人口最多的城市是什么？", "test-chart-skip-001")
    assert state.errors == []
    assert state.chart_artifact is None
