from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import sqlglot
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from ai.analyst.app.agent.graph import AnalystAgent
from ai.analyst.app.llm.client import create_llm_client
from ai.analyst.app.serialization import to_json_safe
from evaluation.semantic_eval import evaluate_answer, evaluate_end_to_end, evaluate_result, evaluate_safety


@dataclass(frozen=True)
class EvaluationCase:
    question_id: str
    question: str
    category: str
    difficulty: str
    expected_behavior: str
    expected_sql: str | None
    expected_tables: list[str]
    expected_columns: list[str]
    semantic_columns: list[str] | None
    expected_result: list[list[Any]]
    result_order: str
    expected_answer_contains: list[str]
    expected_error_code: str | None


@dataclass(frozen=True)
class EvaluationResult:
    question_id: str
    question: str
    category: str
    difficulty: str
    expected_behavior: str
    actual_sql: str | None
    validated_sql: str | None
    actual_result: dict[str, Any] | None
    actual_answer: str | None
    # sql_correct: bool | None
    # result_correct: bool | None
    # answer_correct: bool | None
    exact_sql_match: bool | None
    semantic_result_correct: bool | None
    semantic_result_reason: str | None
    answer_correct: bool | None
    answer_reason: str | None
    safety_correct: bool | None
    safety_reason: str | None
    semantic_correct: bool | None
    semantic_reason: str | None
    latency_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    trace_id: str
    model: str | None
    provider: str
    error_type: str | None
    error_message: str | None


def validate_dataset(payload: dict[str, Any], schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    try:
        validator.validate(payload)
    except ValidationError as exc:
        location = ".".join(str(part) for part in exc.absolute_path) or "<root>"
        raise ValueError(f"Invalid evaluation dataset at {location}: {exc.message}") from exc


def load_cases(path: Path, schema_path: Path | None = None) -> list[EvaluationCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    schema_path = schema_path or path.with_name("dataset.schema.json")
    validate_dataset(payload, schema_path)
    cases = payload["cases"]
    return [
        EvaluationCase(
            question_id=str(item["question_id"]),
            question=str(item["question"]),
            category=str(item["category"]),
            difficulty=str(item["difficulty"]),
            expected_behavior=str(item.get("expected_behavior", "answer")),
            expected_sql=item.get("expected_sql"),
            expected_tables=list(item.get("expected_tables", [])),
            expected_columns=list(item.get("expected_columns", [])),
            semantic_columns=(list(item["semantic_columns"]) if item.get("semantic_columns") is not None else None),
            expected_result=list(item.get("expected_result", [])),
            result_order=str(item.get("result_order", "ordered")),
            expected_answer_contains=list(item.get("expected_answer_contains", [])),
            expected_error_code=item.get("expected_error_code"),
        )
        for item in cases
    ]


def canonical_sql(sql: str) -> str:
    tree = sqlglot.parse_one(sql, read="postgres")
    return tree.sql(dialect="postgres", pretty=False).lower()


def sql_matches(actual: str | None, expected: str | None) -> bool | None:
    if actual is None or expected is None:
        return None
    try:
        return canonical_sql(actual) == canonical_sql(expected)
    except Exception:
        return False


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise TypeError(f"Not numeric: {value!r}") from exc


def _values_equal(left: Any, right: Any, *, numeric_tolerance: Decimal = Decimal("1e-9")) -> bool:
    if _is_number(left) and _is_number(right):
        a, b = _decimal(left), _decimal(right)
        scale = max(Decimal(1), abs(a), abs(b))
        return abs(a - b) <= numeric_tolerance * scale
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _values_equal(a, b, numeric_tolerance=numeric_tolerance) for a, b in zip(left, right)
        )
    return left == right


def result_matches(
    actual: dict[str, Any] | None,
    expected_columns: list[str],
    expected_rows: list[list[Any]],
    result_order: str = "ordered",
) -> bool | None:
    if actual is None:
        return None
    if actual.get("columns") != expected_columns:
        return False
    actual_rows = actual.get("rows") or []
    if len(actual_rows) != len(expected_rows):
        return False
    if result_order == "unordered":
        remaining = list(expected_rows)
        for row in actual_rows:
            for index, candidate in enumerate(remaining):
                if _values_equal(row, candidate):
                    remaining.pop(index)
                    break
            else:
                return False
        return not remaining
    return _values_equal(actual_rows, expected_rows)


def answer_matches(actual: str | None, expected_terms: list[str]) -> bool | None:
    if not expected_terms:
        return None
    if actual is None:
        return False
    normalized = actual.casefold()
    return all(term.casefold() in normalized for term in expected_terms)


def _usage(state_usage: dict[str, int]) -> tuple[int, int, int]:
    input_tokens = int(state_usage.get("input_tokens", state_usage.get("prompt_tokens", 0)) or 0)
    output_tokens = int(
        state_usage.get("output_tokens", state_usage.get("completion_tokens", 0)) or 0
    )
    total_tokens = int(state_usage.get("total_tokens", input_tokens + output_tokens) or 0)
    return input_tokens, output_tokens, total_tokens


def _estimated_cost(input_tokens: int, output_tokens: int) -> float:
    input_rate = Decimal(os.getenv("LLM_INPUT_COST_PER_1M", "0"))
    output_rate = Decimal(os.getenv("LLM_OUTPUT_COST_PER_1M", "0"))
    cost = (Decimal(input_tokens) / Decimal(1_000_000)) * input_rate
    cost += (Decimal(output_tokens) / Decimal(1_000_000)) * output_rate
    return float(cost)


def run_case(case: EvaluationCase, agent: AnalystAgent, provider: str) -> EvaluationResult:
    trace_id = f"eval-{case.question_id}"
    started = time.perf_counter()
    try:
        state = agent.run(case.question, trace_id)
        runtime_error = None
    except Exception as exc:  # keep one infrastructure/data failure from aborting the full run
        state = None
        runtime_error = exc
    latency_ms = round((time.perf_counter() - started) * 1000, 3)

    if state is None:
        input_tokens = output_tokens = total_tokens = 0
        error_type = "EVALUATION_RUNTIME_ERROR"
        error_message = str(runtime_error)
        sql_correct = result_correct = answer_correct = False
        actual_sql = validated_sql = actual_result = actual_answer = None
        model = None
    else:
        input_tokens, output_tokens, total_tokens = _usage(state.usage)
        error_type = state.errors[0].get("code") if state.errors else None
        error_message = state.errors[0].get("message") if state.errors else None
        actual_sql = state.sql_candidate
        validated_sql = state.validated_sql
        actual_result = state.query_result
        actual_answer = state.final_answer
        model = state.model

    if state is not None and case.expected_behavior == "reject":
        # Exact SQL match is not meaningful for a reject case. Safety is
        # evaluated separately by evaluate_safety().
        sql_correct = None
        result_correct = None
        answer_correct = None
    elif state is not None:
        sql_correct = sql_matches(state.sql_candidate, case.expected_sql)
        if sql_correct is True and case.expected_tables:
            actual_tables = set((state.query_result or {}).get("tables", []))
            sql_correct = actual_tables == set(case.expected_tables)
        result_correct = result_matches(
            state.query_result,
            case.expected_columns,
            case.expected_result,
            case.result_order,
        )
        answer_correct = answer_matches(state.final_answer, case.expected_answer_contains)

    actual_result = None
    state_errors: list[Any] = []
    state_answer: str | None = None
    state_validated_sql: str | None = None

    if state is not None:
        state_errors = list(state.errors or [])
        state_answer = state.final_answer
        state_validated_sql = state.validated_sql
        if state.query_result is not None:
            actual_result = to_json_safe(state.query_result)

    case_payload = asdict(case)

    if case.expected_behavior == "reject":
        result_check = None
        answer_check = None
    else:
        result_check = evaluate_result(case_payload, actual_result)
        answer_check = evaluate_answer(case_payload, state_answer)

    safety_check = evaluate_safety(
        case_payload,
        validated_sql=state_validated_sql,
        actual_result=actual_result,
        errors=state_errors,
    )

    semantic_check = evaluate_end_to_end(
        case_payload,
        actual_result=actual_result,
        actual_answer=state_answer,
        validated_sql=state_validated_sql,
        errors=state_errors,
    )


    return EvaluationResult(
        question_id=case.question_id,
        question=case.question,
        category=case.category,
        difficulty=case.difficulty,
        expected_behavior=case.expected_behavior,
        actual_sql=actual_sql,
        validated_sql=validated_sql,
        actual_result=actual_result,
        actual_answer=actual_answer,
        # sql_correct=sql_correct,
        # result_correct=result_correct,
        # answer_correct=answer_correct,
        # Diagnostic only.
        exact_sql_match=sql_correct,

        # Semantic evaluation.
        semantic_result_correct=(result_check.passed if result_check else None),
        semantic_result_reason=(result_check.reason if result_check else None),

        answer_correct=(answer_check.passed if answer_check else None),
        answer_reason=(answer_check.reason if answer_check else None),

        safety_correct=(
            safety_check.passed
            if case.expected_behavior == "reject"
            else None
        ),
        safety_reason=(
            safety_check.reason
            if case.expected_behavior == "reject"
            else None
        ),

        semantic_correct=semantic_check.passed,
        semantic_reason=semantic_check.reason,

        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        estimated_cost=_estimated_cost(input_tokens, output_tokens),
        trace_id=trace_id,
        model=model,
        provider=provider,
        error_type=error_type,
        error_message=error_message,
    )


def _bool_metric(results: list[EvaluationResult], field: str) -> dict[str, Any]:
    values = [getattr(result, field) for result in results if getattr(result, field) is not None]
    passed = sum(value is True for value in values)
    return {
        "passed": passed,
        "evaluated": len(values),
        "rate": round(passed / len(values), 4) if values else None,
    }


def summarize(results: list[EvaluationResult]) -> dict[str, Any]:
    import math
    import statistics
    from collections import Counter

    provider_error_codes = {
        "LLM_AUTH_ERROR", "LLM_RATE_LIMIT", "LLM_SERVER_ERROR",
        "LLM_TIMEOUT", "LLM_CONNECTION_ERROR", "LLM_INVALID_RESPONSE",
        "EVALUATION_RUNTIME_ERROR",
    }
    completed = [r for r in results if r.error_type not in provider_error_codes]
    latencies = [r.latency_ms for r in completed]

    def percentile(values: list[float], p: float) -> float | None:
        if not values:
            return None
        ordered = sorted(values)
        rank = max(1, math.ceil(p * len(ordered)))
        return round(ordered[rank - 1], 3)

    error_counts = Counter(r.error_type for r in results if r.error_type)

    return {
        "cases": len(results),
        "completed_cases": len(completed),
        "exact_sql_match_rate": _bool_metric(results, "exact_sql_match"),
        "semantic_result_correctness": _bool_metric(results, "semantic_result_correct"),
        "answer_correctness": _bool_metric(results, "answer_correct"),
        "safety_correctness": _bool_metric(results, "safety_correct"),
        "semantic_correctness": _bool_metric(results, "semantic_correct"),
        "semantic_correctness_completed": _bool_metric(completed, "semantic_correct"),
        "latency_ms": {
            "avg": round(sum(latencies) / len(latencies), 3) if latencies else None,
            "p50": round(statistics.median(latencies), 3) if latencies else None,
            "p95": percentile(latencies, 0.95),
            "max": max(latencies, default=None),
        },
        "tokens": {
            "input": sum(r.input_tokens for r in results),
            "output": sum(r.output_tokens for r in results),
            "total": sum(r.total_tokens for r in results),
        },
        "estimated_cost": round(sum(r.estimated_cost for r in results), 8),
        "errors": sum(r.error_type is not None for r in results),
        "errors_by_code": dict(sorted(error_counts.items())),
    }


def result_to_dict(result: EvaluationResult) -> dict[str, Any]:
    return {
        "question_id": result.question_id,
        "question": result.question,
        "category": result.category,
        "difficulty": result.difficulty,
        "expected_behavior": result.expected_behavior,
        "actual_sql": result.actual_sql,
        "validated_sql": result.validated_sql,
        "actual_result": result.actual_result,
        "actual_answer": result.actual_answer,
        "exact_sql_match": result.exact_sql_match,
        "semantic_result_correct": result.semantic_result_correct,
        "semantic_result_reason": result.semantic_result_reason,
        "answer_correct": result.answer_correct,
        "answer_reason": result.answer_reason,
        "safety_correct": result.safety_correct,
        "safety_reason": result.safety_reason,
        "semantic_correct": result.semantic_correct,
        "semantic_reason": result.semantic_reason,
        "latency_ms": result.latency_ms,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "total_tokens": result.total_tokens,
        "estimated_cost": result.estimated_cost,
        "trace_id": result.trace_id,
        "model": result.model,
        "provider": result.provider,
        "error_type": result.error_type,
        "error_message": result.error_message,
    }


def write_report(results: list[EvaluationResult], output_dir: Path, dataset_path: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize(results)
    provider = os.getenv("LLM_PROVIDER", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()
    run_label = os.getenv("EVALUATION_RUN_LABEL", "").strip()
    payload = {
        "dataset": str(dataset_path),
        "dataset_version": "1.0",
        "provider": provider,
        "model": model,
        "run_label": run_label,
        "summary": summary,
        "cases": [result_to_dict(result) for result in results],
    }
    if run_label:
        json_path = output_dir / f"evaluation-report-{run_label}.json"
        md_path = output_dir / f"evaluation-report-{run_label}.md"
    else:
        json_path = output_dir / "evaluation-report.json"
        md_path = output_dir / "evaluation-report.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")

    def pct(metric: dict[str, Any]) -> str:
        return "N/A" if metric["rate"] is None else f"{metric['rate'] * 100:.1f}%"

    lines = [
        "# P1 Analyst Agent v0.1 Evaluation Report",
        "",
        f"Dataset: `{dataset_path}`",
        "",
        "## Summary",
        "",
        "| Metric | Passed | Evaluated | Rate |",
        "|---|---:|---:|---:|",
        f"| Exact SQL Match rate | {summary['exact_sql_match_rate']['passed']} | {summary['exact_sql_match_rate']['evaluated']} | {pct(summary['exact_sql_match_rate'])} |",
        f"| Semantic result correctness | {summary['semantic_result_correctness']['passed']} | {summary['semantic_result_correctness']['evaluated']} | {pct(summary['semantic_result_correctness'])} |",
        f"| Answer correctness | {summary['answer_correctness']['passed']} | {summary['answer_correctness']['evaluated']} | {pct(summary['answer_correctness'])} |",
        f"| Safety correctness | {summary['safety_correctness']['passed']} | {summary['safety_correctness']['evaluated']} | {pct(summary['safety_correctness'])} |",
        f"| Semantic correctness (all cases) | {summary['semantic_correctness']['passed']} | {summary['semantic_correctness']['evaluated']} | {pct(summary['semantic_correctness'])} |",
        f"| Semantic correctness (completed cases) | {summary['semantic_correctness_completed']['passed']} | {summary['semantic_correctness_completed']['evaluated']} | {pct(summary['semantic_correctness_completed'])} |",
        "",
        f"- Cases: **{summary['cases']}**; completed without provider/runtime error: **{summary['completed_cases']}**",
        f"- Completed-case latency avg/p50/p95/max: **{summary['latency_ms']['avg']} / {summary['latency_ms']['p50']} / {summary['latency_ms']['p95']} / {summary['latency_ms']['max']} ms**",
        f"- Total tokens: **{summary['tokens']['total']}**",
        f"- Estimated cost: **${summary['estimated_cost']:.8f}**",
        f"- Cases with agent errors: **{summary['errors']}**",
        "",
        "## Case Results",
        "",
        "| ID | Category | Exact SQL | Result | Answer | Safety | Semantic | Error |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for result in results:
        def mark(value: bool | None) -> str:
            return "N/A" if value is None else ("PASS" if value else "FAIL")
        lines.append(
            f"| {result.question_id} | {result.category} | {mark(result.exact_sql_match)} | "
            f"{mark(result.semantic_result_correct)} | {mark(result.answer_correct)} | "
            f"{mark(result.safety_correct)} | {mark(result.semantic_correct)} | {result.error_type or ''} |"
        )
    lines += ["", "## Case Detail", ""]
    case_by_id = {case.question_id: case for case in load_cases(dataset_path)}
    for result in results:
        case = case_by_id[result.question_id]
        lines += [
            f"### {result.question_id} — {result.question}",
            "",
            f"- Category: `{result.category}`; difficulty: `{result.difficulty}`; behavior: `{result.expected_behavior}`",
            f"- Expected SQL: `{case.expected_sql or ''}`",
            f"- Actual SQL: `{result.actual_sql or ''}`",
            f"- Expected columns: `{case.expected_columns}`",
            f"- Actual columns: `{(result.actual_result or {}).get('columns', [])}`",
            f"- Expected rows: `{case.expected_result}`",
            f"- Actual rows: `{(result.actual_result or {}).get('rows', [])}`",
            f"- Expected answer terms: `{case.expected_answer_contains}`",
            f"- Actual answer: `{result.actual_answer or ''}`",
            f"- Latency: `{result.latency_ms} ms`; tokens: `{result.total_tokens}`; cost: `${result.estimated_cost:.8f}`",
            f"- Trace ID: `{result.trace_id}`; model: `{result.model or ''}`; error: `{result.error_type or ''}`",
            "",
        ]
    lines += [
        "## Notes", "",
        "- Exact SQL Match is a diagnostic metric based on SQLGlot canonicalization; semantically equivalent SQL may fail this metric.",
        "- Semantic result correctness allows harmless extra columns, alias differences, omitted non-required columns, numeric tolerance, and unordered comparison when ordering is not part of the user request.",
        "- Answer correctness uses normalized semantic evidence rather than raw keyword containment alone.",
        "- Reject cases pass only when the unsafe request is stopped before executable SQL reaches the database.",
        "- Completed-case latency excludes provider/runtime failures so Retry-After waits do not masquerade as model inference latency.",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path
