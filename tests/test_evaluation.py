from types import SimpleNamespace
from pathlib import Path
import json

from evaluation.evaluator import (
    canonical_sql,
    load_cases,
    result_matches,
    run_case,
    sql_matches,
)


DATASET = Path(__file__).parents[1] / "evaluation" / "dataset.json"


def test_dataset_has_30_cases_and_unique_ids():
    cases = load_cases(DATASET)
    schema = json.loads((DATASET.parent / "dataset.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["cases"]["minItems"] == 1
    assert len(cases) == 30
    assert len({case.question_id for case in cases}) == 30
    assert {case.category for case in cases} >= {
        "filtering",
        "aggregation",
        "ranking",
        "grouping",
        "sorting",
        "year/date filters",
        "CTE",
        "ambiguous wording",
        "unsafe requests",
        "edge cases",
        "joins",
    }


def test_sql_canonicalization_accepts_formatting_difference():
    assert sql_matches(
        "select name, population from city order by population desc limit 5;",
        "SELECT name, population FROM city ORDER BY population DESC LIMIT 5",
    ) is True
    assert canonical_sql("SELECT name FROM city") == canonical_sql("select name from city")


def test_result_matching_handles_numeric_precision():
    actual = {
        "columns": ["avg_population"],
        "rows": [[2069855.4000000001]],
    }
    assert result_matches(actual, ["avg_population"], [[2069855.4]]) is True


def test_result_matching_respects_order_setting():
    actual = {"columns": ["state", "count"], "rows": [["CA", 3], ["TX", 5]]}
    expected = [["TX", 5], ["CA", 3]]
    assert result_matches(actual, ["state", "count"], expected, "ordered") is False
    assert result_matches(actual, ["state", "count"], expected, "unordered") is True


def test_run_case_captures_usage_and_error():
    case = load_cases(DATASET)[29]
    fake_state = SimpleNamespace(
        sql_candidate=None,
        validated_sql=None,
        query_result=None,
        final_answer=None,
        usage={"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
        trace_id="eval-DA-030",
        model="fake",
        errors=[{"code": "STATEMENT_NOT_READ_ONLY", "message": "blocked"}],
    )

    class FakeAgent:
        def run(self, question, trace_id):
            assert trace_id == "eval-DA-030"
            return fake_state

    result = run_case(case, FakeAgent(), "mock")
    assert result.sql_correct is True
    assert result.result_correct is None
    assert result.answer_correct is None
    assert result.total_tokens == 14
