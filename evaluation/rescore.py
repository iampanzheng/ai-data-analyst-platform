from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from evaluation.semantic_eval import (
    evaluate_answer,
    evaluate_end_to_end,
    evaluate_result,
    evaluate_safety,
)

PROVIDER_ERROR_CODES = {
    "LLM_AUTH_ERROR",
    "LLM_RATE_LIMIT",
    "LLM_SERVER_ERROR",
    "LLM_TIMEOUT",
    "LLM_CONNECTION_ERROR",
    "LLM_INVALID_RESPONSE",
    "EVALUATION_RUNTIME_ERROR",
}


def _rate(passed: int, evaluated: int) -> float | None:
    return round(passed / evaluated, 4) if evaluated else None


def _bool_metric(cases: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = [case.get(field) for case in cases if case.get(field) is not None]
    passed = sum(value is True for value in values)
    return {"passed": passed, "evaluated": len(values), "rate": _rate(passed, len(values))}


def _percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(p * len(ordered)))
    return round(ordered[rank - 1], 3)


def summarize(cases: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [case for case in cases if case.get("error_type") not in PROVIDER_ERROR_CODES]
    latencies = [float(case["latency_ms"]) for case in completed if case.get("latency_ms") is not None]
    errors = Counter(case["error_type"] for case in cases if case.get("error_type"))
    return {
        "cases": len(cases),
        "completed_cases": len(completed),
        "exact_sql_match_rate": _bool_metric(cases, "exact_sql_match"),
        "semantic_result_correctness": _bool_metric(cases, "semantic_result_correct"),
        "answer_correctness": _bool_metric(cases, "answer_correct"),
        "safety_correctness": _bool_metric(cases, "safety_correct"),
        "semantic_correctness": _bool_metric(cases, "semantic_correct"),
        "semantic_correctness_completed": _bool_metric(completed, "semantic_correct"),
        "latency_ms": {
            "avg": round(sum(latencies) / len(latencies), 3) if latencies else None,
            "p50": round(statistics.median(latencies), 3) if latencies else None,
            "p95": _percentile(latencies, 0.95),
            "max": round(max(latencies), 3) if latencies else None,
        },
        "tokens": {
            "input": sum(int(case.get("input_tokens") or 0) for case in cases),
            "output": sum(int(case.get("output_tokens") or 0) for case in cases),
            "total": sum(int(case.get("total_tokens") or 0) for case in cases),
        },
        "estimated_cost": round(sum(float(case.get("estimated_cost") or 0) for case in cases), 8),
        "errors": sum(case.get("error_type") is not None for case in cases),
        "errors_by_code": dict(sorted(errors.items())),
    }


def rescore(report: dict[str, Any], dataset: dict[str, Any]) -> dict[str, Any]:
    case_by_id = {case["question_id"]: case for case in dataset["cases"]}
    updated_cases: list[dict[str, Any]] = []

    for original in report["cases"]:
        item = dict(original)
        case = case_by_id[item["question_id"]]
        error_type = item.get("error_type")
        errors = []
        if error_type:
            errors.append({"code": error_type, "message": item.get("error_message") or ""})

        if case.get("expected_behavior") == "reject":
            item["semantic_result_correct"] = None
            item["semantic_result_reason"] = None
            item["answer_correct"] = None
            item["answer_reason"] = None
            safety = evaluate_safety(
                case,
                validated_sql=item.get("validated_sql"),
                actual_result=item.get("actual_result"),
                errors=errors,
            )
            item["safety_correct"] = safety.passed
            item["safety_reason"] = safety.reason
        else:
            result = evaluate_result(case, item.get("actual_result"))
            answer = evaluate_answer(case, item.get("actual_answer"))
            item["semantic_result_correct"] = result.passed
            item["semantic_result_reason"] = result.reason
            item["answer_correct"] = answer.passed
            item["answer_reason"] = answer.reason
            item["safety_correct"] = None
            item["safety_reason"] = None

        semantic = evaluate_end_to_end(
            case,
            actual_result=item.get("actual_result"),
            actual_answer=item.get("actual_answer"),
            validated_sql=item.get("validated_sql"),
            errors=errors,
        )
        item["semantic_correct"] = semantic.passed
        item["semantic_reason"] = semantic.reason
        updated_cases.append(item)

    result = dict(report)
    result["summary"] = summarize(updated_cases)
    result["cases"] = updated_cases
    result["rescored"] = True
    result["rescore_note"] = "Offline rescored with the frozen Stage 2.2 semantic evaluator; no model calls were made."
    return result


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    s = payload["summary"]
    def pct(metric: str) -> str:
        m = s[metric]
        return "N/A" if m["rate"] is None else f"{m['rate'] * 100:.1f}%"

    lines = [
        "# P1 Stage 2.2 Offline Rescored Evaluation Report",
        "",
        f"Model: `{payload.get('model')}`",
        f"Run label: `{payload.get('run_label')}`",
        "",
        "## Summary",
        "",
        "| Metric | Passed | Evaluated | Rate |",
        "|---|---:|---:|---:|",
    ]
    for label, key in [
        ("Exact SQL Match", "exact_sql_match_rate"),
        ("Semantic result correctness", "semantic_result_correctness"),
        ("Answer correctness", "answer_correctness"),
        ("Safety correctness", "safety_correctness"),
        ("Semantic correctness (all cases)", "semantic_correctness"),
        ("Semantic correctness (completed cases)", "semantic_correctness_completed"),
    ]:
        m = s[key]
        rate = "N/A" if m["rate"] is None else f"{m['rate'] * 100:.1f}%"
        lines.append(f"| {label} | {m['passed']} | {m['evaluated']} | {rate} |")

    l = s["latency_ms"]
    lines += [
        "",
        f"- Cases: **{s['cases']}**; completed without provider/runtime error: **{s['completed_cases']}**",
        f"- Completed-case latency avg/p50/p95/max: **{l['avg']} / {l['p50']} / {l['p95']} / {l['max']} ms**",
        f"- Total tokens: **{s['tokens']['total']}**",
        f"- Estimated cost: **${s['estimated_cost']:.8f}**",
        f"- Errors by code: `{s['errors_by_code']}`",
        "",
        "## Case Results",
        "",
        "| ID | Result | Answer | Safety | Semantic | Error |",
        "|---|---|---|---|---|---|",
    ]
    for case in payload["cases"]:
        def f(v):
            return "N/A" if v is None else ("PASS" if v else "FAIL")
        lines.append(
            f"| {case['question_id']} | {f(case.get('semantic_result_correct'))} | "
            f"{f(case.get('answer_correct'))} | {f(case.get('safety_correct'))} | "
            f"{f(case.get('semantic_correct'))} | {case.get('error_type') or ''} |"
        )
    lines += [
        "",
        "## Notes",
        "",
        "- This report was rescored offline from an existing model run; no LLM request was made.",
        "- DA-027 requires `name` and `state` semantically because the user asks to display the state; population remains a filter condition and reference-SQL diagnostic field.",
        "- Exact SQL Match remains diagnostic only.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline rescore an existing evaluation report")
    parser.add_argument("report")
    parser.add_argument("--dataset", default="evaluation/dataset.json")
    parser.add_argument("--output")
    args = parser.parse_args()

    report_path = Path(args.report)
    dataset_path = Path(args.dataset)
    payload = rescore(
        json.loads(report_path.read_text(encoding="utf-8")),
        json.loads(dataset_path.read_text(encoding="utf-8")),
    )
    output = Path(args.output) if args.output else report_path.with_name(report_path.stem + "-rescored.json")
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(payload, output.with_suffix(".md"))
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    print(f"JSON report: {output}")
    print(f"Markdown report: {output.with_suffix('.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
