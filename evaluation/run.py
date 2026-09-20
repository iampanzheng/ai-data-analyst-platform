from __future__ import annotations

import argparse
import os
from pathlib import Path

from .evaluator import load_cases, run_case, write_report
from ai.analyst.app.agent.graph import AnalystAgent
from ai.analyst.app.llm.client import create_llm_client


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Analyst Agent evaluation")
    parser.add_argument("--dataset", default="evaluation/dataset.json")
    parser.add_argument("--output-dir", default="evaluation/results")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    cases = load_cases(dataset_path)
    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower() or "mock"
    agent = AnalystAgent(create_llm_client())
    results = [run_case(case, agent, provider) for case in cases]
    json_path, md_path = write_report(results, Path(args.output_dir), dataset_path)

    summary = write_summary(results)
    print(summary)
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")
    return 0


def write_summary(results) -> str:
    from .evaluator import summarize
    summary = summarize(results)
    def rate(name: str) -> str:
        metric = summary[name]
        return "N/A" if metric["rate"] is None else f"{metric['rate'] * 100:.1f}%"
    return (
        f"cases={summary['cases']} "
        f"sql={rate('sql_correctness')} "
        f"result={rate('result_correctness')} "
        f"answer={rate('answer_correctness')} "
        f"avg_latency_ms={summary['latency_ms']['avg']} "
        f"total_tokens={summary['tokens']['total']} "
        f"estimated_cost=${summary['estimated_cost']:.8f}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
