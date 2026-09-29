from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
import time

from ai.analyst.app.logging_config import configure_logging

from .evaluator import load_cases, run_case, write_report
from ai.analyst.app.agent.graph import AnalystAgent
from ai.analyst.app.llm.client import create_llm_client

configure_logging()
logger = logging.getLogger("ai.analyst.api")

def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Analyst Agent evaluation")
    parser.add_argument("--dataset", default="evaluation/dataset.json")
    parser.add_argument("--output-dir", default="evaluation/results")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    cases = load_cases(dataset_path)
    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower() or "mock"
    agent = AnalystAgent(create_llm_client())
    eval_delay_seconds = float(
        os.getenv("LLM_EVAL_DELAY_SECONDS", "0")
    )
    results = []
    for index, case in enumerate(cases):
        # if index > len(cases) - 3:
            results.append(run_case(case, agent, provider))
            if (
                eval_delay_seconds > 0
                and index < len(cases) - 1
            ):
                logger.info(
                    "evaluation_pacing",
                    extra={
                        "event": "evaluation_pacing",
                        "case_id": case.question_id,
                        "delay_seconds": eval_delay_seconds,
                    },
                )
                time.sleep(eval_delay_seconds)
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
        f"sql={rate('exact_sql_match_rate')} "
        f"result={rate('semantic_result_correctness')} "
        f"answer={rate('answer_correctness')} "
        f"semantic_completed={rate('semantic_correctness_completed')} "
        f"avg_latency_ms={summary['latency_ms']['avg']} "
        f"total_tokens={summary['tokens']['total']} "
        f"estimated_cost=${summary['estimated_cost']:.8f}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
