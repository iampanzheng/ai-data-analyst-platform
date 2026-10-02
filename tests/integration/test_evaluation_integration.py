import os
from pathlib import Path

import pytest

from evaluation.evaluator import load_cases, run_case, summarize
from ai.analyst.app.agent.graph import AnalystAgent
from ai.analyst.app.llm.client import MockLLMClient

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def database_url():
    value = os.getenv("DATABASE_URL")
    if not value:
        pytest.skip("DATABASE_URL is not set; run inside the FastAPI/ETL environment")
    return value


def test_real_agent_evaluation_dataset(database_url):
    assert database_url
    dataset = Path(__file__).parents[2] / "evaluation" / "dataset.json"
    cases = load_cases(dataset)
    results = [run_case(case, AnalystAgent(MockLLMClient()), "mock") for case in cases]
    summary = summarize(results)

    assert summary["cases"] == 35
    assert summary["tokens"]["total"] == 0
    assert summary["estimated_cost"] == 0.0
    assert results[0].trace_id == "eval-DA-001"
    assert results[0].actual_result["row_count"] == 5
