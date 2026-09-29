from evaluation.compare_models import build_comparison, classify_case


def _report(model: str, avg_latency: float, output_tokens: int, completed: int, errors=None):
    errors = errors or {}
    return {
        "provider": "test",
        "model": model,
        "run_label": model,
        "summary": {
            "cases": 2,
            "completed_cases": completed,
            "exact_sql_match_rate": {"passed": 0, "evaluated": 1, "rate": 0.0},
            "semantic_result_correctness": {"passed": 1, "evaluated": 1, "rate": 1.0},
            "answer_correctness": {"passed": 1, "evaluated": 1, "rate": 1.0},
            "safety_correctness": {"passed": 1, "evaluated": 1, "rate": 1.0},
            "semantic_correctness": {"passed": 2, "evaluated": 2, "rate": 1.0},
            "semantic_correctness_completed": {"passed": completed, "evaluated": completed, "rate": 1.0},
            "latency_ms": {"avg": avg_latency, "p50": avg_latency, "p95": avg_latency, "max": avg_latency},
            "tokens": {"input": 100, "output": output_tokens, "total": 100 + output_tokens},
            "estimated_cost": 0.0,
            "errors": sum(errors.values()),
            "errors_by_code": errors,
        },
        "cases": [],
    }


def test_classify_provider_timeout():
    assert classify_case({"error_type": "LLM_TIMEOUT"}) == "provider_or_runtime_failure"


def test_classify_answer_failure():
    case = {
        "expected_behavior": "answer",
        "semantic_result_correct": True,
        "answer_correct": False,
        "semantic_correct": False,
        "error_type": None,
    }
    assert classify_case(case) == "answer_generation_failure"


def test_classify_expected_safety_rejection():
    case = {
        "expected_behavior": "reject",
        "safety_correct": True,
        "semantic_correct": True,
        "error_type": "STATEMENT_NOT_READ_ONLY",
    }
    assert classify_case(case) == "expected_safety_rejection"


def test_build_comparison_computes_ratios():
    slow = _report("slow", 10000.0, 500, 2)
    fast = _report("fast", 1000.0, 100, 2)
    comparison = build_comparison([slow, fast])
    assert comparison["derived"]["latency_ratio"]["ratio"] == 10.0
    assert comparison["derived"]["output_token_ratio"]["ratio"] == 5.0
