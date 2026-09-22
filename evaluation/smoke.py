from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any

from ai.analyst.app.agent.graph import AnalystAgent
from ai.analyst.app.llm.client import create_llm_client


@dataclass(frozen=True)
class SmokeCase:
    case_id: str
    question: str
    kind: str



ENTITY_ALIASES = {
    "New York": ("New York", "纽约"),
    "Los Angeles": ("Los Angeles", "洛杉矶"),
    "Chicago": ("Chicago", "芝加哥"),
    "Houston": ("Houston", "休斯敦", "休斯顿"),
    "Phoenix": ("Phoenix", "菲尼克斯", "凤凰城"),
    "San Diego": ("San Diego", "圣地亚哥"),
    "San Jose": ("San Jose", "圣何塞"),
}


def _mentions_entity(answer: str, canonical: str) -> bool:
    aliases = ENTITY_ALIASES.get(canonical, (canonical,))
    return any(alias.casefold() in answer.casefold() for alias in aliases)


def _mentions_all_entities(answer: str, canonicals: list[str]) -> bool:
    return all(_mentions_entity(answer, item) for item in canonicals)


def _extract_city_total_claims(answer: str) -> list[int]:
    patterns = [
        # Explicit city-total wording may naturally end at “13个” without repeating “城市”.
        r"(?:城市总数|总城市数|城市数量总计)\s*(?:为|是|有)?\s*(\d+)\s*(?:个(?:城市)?)?",
        # Generic total wording is only a city-total claim when the city unit is explicit.
        r"(?:共有|共计|总共|合计)\s*(?:为|是|有)?\s*(\d+)\s*个?城市",
        r"(\d+)\s*个城市(?:\s*(?:总计|总共|合计))?",
    ]
    values: list[int] = []
    for pattern in patterns:
        for match in re.finditer(pattern, answer, flags=re.IGNORECASE):
            values.append(int(match.group(1)))
    return values

SMOKE_CASES = [
    SmokeCase("SMOKE-001", "人口最多的 5 个城市是哪几个？", "top5"),
    SmokeCase("SMOKE-002", "一共有多少个城市？", "count"),
    SmokeCase("SMOKE-003", "加州有哪些城市？按人口从高到低列出。", "california"),
    SmokeCase("SMOKE-004", "每个州有多少个城市？", "group_count"),
    SmokeCase("SMOKE-005", "执行 DROP TABLE city。", "unsafe"),
]


def _tokens(usage: dict[str, int]) -> tuple[int, int, int]:
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    total_tokens = int(usage.get("total_tokens", input_tokens + output_tokens) or 0)
    return input_tokens, output_tokens, total_tokens


def _estimated_cost(input_tokens: int, output_tokens: int) -> float:
    input_rate = float(os.getenv("LLM_INPUT_COST_PER_1M", "0") or 0)
    output_rate = float(os.getenv("LLM_OUTPUT_COST_PER_1M", "0") or 0)
    return (input_tokens / 1_000_000) * input_rate + (output_tokens / 1_000_000) * output_rate


def _pipeline_passed(state: Any, case: SmokeCase) -> bool:
    if case.kind == "unsafe":
        return state.query_result is None and bool(state.errors)
    return (
        not state.errors
        and bool(state.validated_sql)
        and state.query_result is not None
        and bool(state.final_answer)
    )


def _result_check(state: Any, case: SmokeCase) -> tuple[bool, str]:
    if case.kind == "unsafe":
        codes = {item.get("code") for item in state.errors}
        ok = "STATEMENT_NOT_READ_ONLY" in codes
        return ok, "expected STATEMENT_NOT_READ_ONLY"

    result = state.query_result or {}
    rows = result.get("rows") or []
    columns = result.get("columns") or []

    if case.kind == "top5":
        if len(rows) != 5 or "name" not in columns:
            return False, "expected five rows containing a name column"
        name_index = columns.index("name")
        names = [row[name_index] for row in rows]
        expected = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]
        return names == expected, f"expected names={expected}"

    if case.kind == "count":
        value = rows[0][0] if rows and rows[0] else None
        return value == 15, "expected city count=15"

    if case.kind == "california":
        if "name" not in columns:
            return False, "expected a name column"
        name_index = columns.index("name")
        names = [row[name_index] for row in rows]
        expected = ["Los Angeles", "San Diego", "San Jose"]
        return names == expected, f"expected California cities={expected}"

    if case.kind == "group_count":
        if not {"state", "city_count"}.issubset(columns):
            return False, "expected state and city_count columns"
        state_index = columns.index("state")
        count_index = columns.index("city_count")
        counts = {row[state_index]: row[count_index] for row in rows}
        ok = len(counts) == 9 and counts.get("TX") == 5 and counts.get("CA") == 3 and sum(counts.values()) == 15
        return ok, "expected 9 states, TX=5, CA=3, total cities=15"

    return False, f"unknown smoke case kind={case.kind}"


def _answer_check(state: Any, case: SmokeCase) -> tuple[bool, str]:
    if case.kind == "unsafe":
        return True, "no final answer expected for rejected unsafe SQL"

    answer = (state.final_answer or "").strip()
    if not answer:
        return False, "expected a non-empty final answer"

    if case.kind == "top5":
        expected = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]
        return _mentions_all_entities(answer, expected), f"answer must mention semantic equivalents of {expected}"

    if case.kind == "count":
        return "15" in answer, "answer must report city count 15"

    if case.kind == "california":
        expected = ["Los Angeles", "San Diego", "San Jose"]
        return _mentions_all_entities(answer, expected), f"answer must mention semantic equivalents of {expected}"

    if case.kind == "group_count":
        has_tx = bool(re.search(r"\bTX\b\s*[:：]?\s*5(?:\s*个)?", answer, flags=re.IGNORECASE)) or bool(re.search(r"德克萨斯(?:州)?[^\d]{0,12}5\s*个?城市", answer))
        has_ca = bool(re.search(r"\bCA\b\s*[:：]?\s*3(?:\s*个)?", answer, flags=re.IGNORECASE)) or bool(re.search(r"加利福尼亚(?:州)?[^\d]{0,12}3\s*个?城市", answer))
        city_total_claims = _extract_city_total_claims(answer)
        total_consistent = all(value == 15 for value in city_total_claims)
        ok = has_tx and has_ca and total_consistent
        return ok, "answer must preserve TX=5, CA=3; any explicit city-total claim must equal 15"

    return False, f"unknown smoke case kind={case.kind}"


def _semantic_check(state: Any, case: SmokeCase) -> tuple[bool, str]:
    result_ok, result_expectation = _result_check(state, case)
    answer_ok, answer_expectation = _answer_check(state, case)
    return result_ok and answer_ok, f"result: {result_expectation}; answer: {answer_expectation}"

def main() -> int:
    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower() or "mock"
    if provider == "mock":
        print("ERROR: real-model smoke requires LLM_PROVIDER to be non-mock")
        return 2

    agent = AnalystAgent(create_llm_client())
    results = []
    semantic_failed = 0
    result_failed = 0
    answer_failed = 0
    pipeline_failed = 0

    for case in SMOKE_CASES:
        started = time.perf_counter()
        state = agent.run(case.question, f"stage21-{case.case_id.lower()}")
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        input_tokens, output_tokens, total_tokens = _tokens(state.usage)
        cost = _estimated_cost(input_tokens, output_tokens)

        pipeline_passed = _pipeline_passed(state, case)
        result_passed, result_expectation = _result_check(state, case)
        answer_passed, answer_expectation = _answer_check(state, case)
        semantic_passed = result_passed and answer_passed
        semantic_expectation = f"result: {result_expectation}; answer: {answer_expectation}"
        if not pipeline_passed:
            pipeline_failed += 1
        if not result_passed:
            result_failed += 1
        if not answer_passed:
            answer_failed += 1
        if not semantic_passed:
            semantic_failed += 1

        row = {
            "id": case.case_id,
            "pipeline_passed": pipeline_passed,
            "result_passed": result_passed,
            "answer_passed": answer_passed,
            "semantic_passed": semantic_passed,
            "semantic_expectation": semantic_expectation,
            "question": case.question,
            "provider": state.provider,
            "model": state.model,
            "sql_candidate": state.sql_candidate,
            "validated_sql": state.validated_sql,
            "columns": (state.query_result or {}).get("columns"),
            "row_count": (state.query_result or {}).get("row_count"),
            "rows": (state.query_result or {}).get("rows"),
            "final_answer": state.final_answer,
            "errors": state.errors,
            "latency_ms": latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": round(cost, 8),
        }
        results.append(row)
        print(json.dumps(row, ensure_ascii=False))

    summary = {
        "cases": len(results),
        "pipeline_passed": len(results) - pipeline_failed,
        "pipeline_failed": pipeline_failed,
        "result_passed": len(results) - result_failed,
        "result_failed": result_failed,
        "answer_passed": len(results) - answer_failed,
        "answer_failed": answer_failed,
        "semantic_passed": len(results) - semantic_failed,
        "semantic_failed": semantic_failed,
        "total_tokens": sum(r["total_tokens"] for r in results),
        "estimated_cost": round(sum(r["estimated_cost"] for r in results), 8),
        "avg_latency_ms": round(sum(r["latency_ms"] for r in results) / len(results), 3),
    }
    print("SUMMARY " + json.dumps(summary, ensure_ascii=False))
    return 0 if pipeline_failed == 0 and semantic_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
