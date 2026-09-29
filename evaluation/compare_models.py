from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

PROVIDER_RUNTIME_ERRORS = {
    "LLM_AUTH_ERROR",
    "LLM_RATE_LIMIT",
    "LLM_SERVER_ERROR",
    "LLM_TIMEOUT",
    "LLM_CONNECTION_ERROR",
    "LLM_INVALID_RESPONSE",
    "EVALUATION_RUNTIME_ERROR",
}


def load_report(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _pct(rate: float | None) -> float | None:
    if rate is None:
        return None
    return round(rate * 100.0, 2)


def summarize_report(report: dict[str, Any]) -> dict[str, Any]:
    summary = report["summary"]
    cases = int(summary["cases"])
    completed = int(summary["completed_cases"])
    errors_by_code = dict(summary.get("errors_by_code") or {})

    provider_runtime_failures = sum(
        int(count)
        for code, count in errors_by_code.items()
        if code in PROVIDER_RUNTIME_ERRORS
    )

    validation_rejections = sum(
        int(count)
        for code, count in errors_by_code.items()
        if code not in PROVIDER_RUNTIME_ERRORS
    )

    return {
        "provider": report.get("provider"),
        "model": report.get("model"),
        "run_label": report.get("run_label"),
        "cases": cases,
        "completed_cases": completed,
        "completion_rate": round(completed / cases, 4) if cases else 0.0,
        "exact_sql_match": summary.get("exact_sql_match_rate"),
        "semantic_result_correctness": summary.get("semantic_result_correctness"),
        "answer_correctness": summary.get("answer_correctness"),
        "safety_correctness": summary.get("safety_correctness"),
        "semantic_correctness_all": summary.get("semantic_correctness"),
        "semantic_correctness_completed": summary.get("semantic_correctness_completed"),
        "latency_ms": summary.get("latency_ms"),
        "tokens": summary.get("tokens"),
        "estimated_cost": float(summary.get("estimated_cost") or 0.0),
        "provider_runtime_failures": provider_runtime_failures,
        "validation_rejections": validation_rejections,
        "errors_by_code": errors_by_code,
    }


def classify_case(case: dict[str, Any]) -> str:
    error_type = case.get("error_type")
    if error_type in PROVIDER_RUNTIME_ERRORS:
        return "provider_or_runtime_failure"

    if case.get("expected_behavior") == "reject":
        if case.get("safety_correct"):
            return "expected_safety_rejection"
        return "safety_failure"

    if case.get("semantic_correct"):
        return "pass"

    if case.get("semantic_result_correct") is False and case.get("answer_correct") is True:
        return "semantic_result_or_instruction_failure"

    if case.get("semantic_result_correct") is True and case.get("answer_correct") is False:
        return "answer_generation_failure"

    if case.get("semantic_result_correct") is False and case.get("answer_correct") is False:
        return "result_and_answer_failure"

    return "semantic_failure"


def failure_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in report.get("cases", []):
        classification = classify_case(case)
        if classification in {"pass", "expected_safety_rejection"}:
            continue
        rows.append(
            {
                "model": report.get("model"),
                "question_id": case.get("question_id"),
                "category": case.get("category"),
                "difficulty": case.get("difficulty"),
                "classification": classification,
                "error_type": case.get("error_type"),
                "semantic_result_correct": case.get("semantic_result_correct"),
                "answer_correct": case.get("answer_correct"),
                "safety_correct": case.get("safety_correct"),
                "semantic_correct": case.get("semantic_correct"),
                "semantic_reason": case.get("semantic_reason"),
            }
        )
    return rows


def build_comparison(reports: list[dict[str, Any]]) -> dict[str, Any]:
    models = [summarize_report(report) for report in reports]
    failures = [row for report in reports for row in failure_rows(report)]

    derived: dict[str, Any] = {}
    if len(models) == 2:
        a, b = models
        a_avg = float((a.get("latency_ms") or {}).get("avg") or 0.0)
        b_avg = float((b.get("latency_ms") or {}).get("avg") or 0.0)
        a_out = int((a.get("tokens") or {}).get("output") or 0)
        b_out = int((b.get("tokens") or {}).get("output") or 0)

        if a_avg > 0 and b_avg > 0:
            faster = a if a_avg < b_avg else b
            slower = b if faster is a else a
            derived["latency_ratio"] = {
                "faster_model": faster["model"],
                "slower_model": slower["model"],
                "ratio": round(
                    float((slower["latency_ms"] or {})["avg"])
                    / float((faster["latency_ms"] or {})["avg"]),
                    2,
                ),
            }

        if a_out > 0 and b_out > 0:
            lower = a if a_out < b_out else b
            higher = b if lower is a else a
            derived["output_token_ratio"] = {
                "lower_output_model": lower["model"],
                "higher_output_model": higher["model"],
                "ratio": round(
                    int((higher["tokens"] or {})["output"])
                    / int((lower["tokens"] or {})["output"]),
                    2,
                ),
            }

    return {
        "stage": "2.3",
        "title": "Model Comparison & Failure Analysis",
        "source": "Stage 2.2 frozen calibrated 30-case baselines",
        "models": models,
        "derived": derived,
        "failures": failures,
        "routing_implications": {
            "interactive_default_evidence": (
                "Prefer the hosted Groq path for latency-sensitive interactive requests: "
                "it completed all measured cases, had higher end-to-end semantic correctness, "
                "and substantially lower measured latency."
            ),
            "local_path_evidence": (
                "Retain Qwen3 8B/Ollama as a local/private/offline path: completed-case semantic "
                "correctness remained high and API cost was zero, but the measured setup had six "
                "timeouts and much higher latency."
            ),
            "shared_failure": (
                "DA-020 is a shared instruction-adherence failure: both models returned the correct "
                "top three cities but omitted the explicit rank output required by the task contract."
            ),
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def write_failure_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "model",
        "question_id",
        "category",
        "difficulty",
        "classification",
        "error_type",
        "semantic_result_correct",
        "answer_correct",
        "safety_correct",
        "semantic_correct",
        "semantic_reason",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, comparison: dict[str, Any]) -> None:
    models = comparison["models"]
    failures = comparison["failures"]

    lines = [
        "# Phase 2 — Stage 2.3 Model Comparison",
        "",
        "Source: Stage 2.2 frozen calibrated 30-case baselines.",
        "",
        "## Measured comparison",
        "",
        "| Metric | " + " | ".join(model["model"] for model in models) + " |",
        "|---|" + "---:|" * len(models),
    ]

    def metric_row(label: str, getter) -> None:
        vals = [getter(model) for model in models]
        lines.append("| " + label + " | " + " | ".join(vals) + " |")

    metric_row("Cases", lambda m: str(m["cases"]))
    metric_row("Completed", lambda m: f'{m["completed_cases"]}/{m["cases"]} ({_pct(m["completion_rate"])}%)')
    metric_row(
        "Semantic result",
        lambda m: f'{m["semantic_result_correctness"]["passed"]}/{m["semantic_result_correctness"]["evaluated"]} ({_pct(m["semantic_result_correctness"]["rate"])}%)',
    )
    metric_row(
        "Answer",
        lambda m: f'{m["answer_correctness"]["passed"]}/{m["answer_correctness"]["evaluated"]} ({_pct(m["answer_correctness"]["rate"])}%)',
    )
    metric_row(
        "Safety",
        lambda m: f'{m["safety_correctness"]["passed"]}/{m["safety_correctness"]["evaluated"]} ({_pct(m["safety_correctness"]["rate"])}%)',
    )
    metric_row(
        "End-to-end semantic (all cases)",
        lambda m: f'{m["semantic_correctness_all"]["passed"]}/{m["semantic_correctness_all"]["evaluated"]} ({_pct(m["semantic_correctness_all"]["rate"])}%)',
    )
    metric_row(
        "End-to-end semantic (completed)",
        lambda m: f'{m["semantic_correctness_completed"]["passed"]}/{m["semantic_correctness_completed"]["evaluated"]} ({_pct(m["semantic_correctness_completed"]["rate"])}%)',
    )
    metric_row("Avg latency", lambda m: f'{m["latency_ms"]["avg"] / 1000:.3f}s')
    metric_row("P95 latency", lambda m: f'{m["latency_ms"]["p95"] / 1000:.3f}s')
    metric_row("Input tokens", lambda m: f'{m["tokens"]["input"]:,}')
    metric_row("Output tokens", lambda m: f'{m["tokens"]["output"]:,}')
    metric_row("Total tokens", lambda m: f'{m["tokens"]["total"]:,}')
    metric_row("Estimated API cost", lambda m: f'${m["estimated_cost"]:.8f}')
    metric_row("Provider/runtime failures", lambda m: str(m["provider_runtime_failures"]))

    lines.extend(["", "## Derived signals", ""])
    latency = comparison["derived"].get("latency_ratio")
    if latency:
        lines.append(
            f'- **Latency:** `{latency["faster_model"]}` was approximately **{latency["ratio"]}× faster** '
            f'than `{latency["slower_model"]}` by measured average completed-case latency.'
        )
    output_ratio = comparison["derived"].get("output_token_ratio")
    if output_ratio:
        lines.append(
            f'- **Output-token footprint:** `{output_ratio["higher_output_model"]}` produced approximately '
            f'**{output_ratio["ratio"]}×** as many output tokens as `{output_ratio["lower_output_model"]}`.'
        )

    lines.extend([
        "",
        "## Failure taxonomy",
        "",
        "| Model | Case | Category | Classification | Error | Semantic reason |",
        "|---|---|---|---|---|---|",
    ])
    for row in failures:
        lines.append(
            "| {model} | {question_id} | {category} | {classification} | {error_type} | {semantic_reason} |".format(
                **{key: ("" if value is None else str(value).replace("|", "\\|")) for key, value in row.items()}
            )
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- **Model quality and system reliability must remain separate.** Qwen3 8B retained high completed-case semantic correctness, but six local inference timeouts reduced end-to-end reliability.",
        "- **Latency is the strongest measured routing signal.** The hosted Groq path remained in the low-single-digit-second range while the local Qwen path was around a minute on average in this setup.",
        "- **DA-020 is a shared instruction-adherence weakness.** Both models produced the correct top three cities but omitted the explicit rank output required by the evaluation contract.",
        "- **Qwen DA-027 is an answer-generation quality failure.** The result was accepted, but the final answer contained the malformed entity `新 York`; this remains a real failure rather than an evaluator exception.",
        "- **Exact SQL match remains diagnostic only.** Qwen matched the reference form more often, while Groq achieved stronger semantic correctness; reference-form agreement is therefore not a suitable primary quality metric.",
        "",
        "## Stage 2.4 evidence boundary",
        "",
        "This stage does **not** implement routing. It records evidence for a deterministic Stage 2.4 policy:",
        "",
        "- hosted Groq path for latency-sensitive interactive requests;",
        "- local Qwen path when privacy/offline operation or zero API spend is prioritized;",
        "- future fallback behavior should be justified by reliability measurements rather than model branding.",
    ])

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare frozen Stage 2.2 evaluation reports.")
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--md-out", type=Path, required=True)
    parser.add_argument("--failures-out", type=Path, required=True)
    args = parser.parse_args()

    reports = [load_report(path) for path in args.reports]
    comparison = build_comparison(reports)
    write_json(args.json_out, comparison)
    write_markdown(args.md_out, comparison)
    write_failure_csv(args.failures_out, comparison["failures"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
