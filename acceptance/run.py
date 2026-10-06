from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class CaseResult:
    case_id: str
    name: str
    passed: bool
    status: int | None
    elapsed_ms: float
    failures: list[str]
    error: str | None = None
    diagnostics: dict[str, Any] | None = None


def resolve_path(payload: Any, path: str) -> Any:
    current = payload
    if not path:
        return current
    for part in path.split('.'):
        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise KeyError(path)
    return current


def check_assertion(payload: Any, assertion: dict[str, Any]) -> str | None:
    path = str(assertion.get('path', ''))
    op = str(assertion['op'])
    try:
        actual = resolve_path(payload, path)
    except (KeyError, IndexError, ValueError, TypeError):
        return f"{path}: path not found"

    expected = assertion.get('value')
    if op == 'eq':
        return None if actual == expected else f"{path}: expected {expected!r}, got {actual!r}"
    if op == 'nonempty':
        return None if actual not in (None, '', [], {}) else f"{path}: expected non-empty value"
    if op == 'is_null':
        return None if actual is None else f"{path}: expected null, got {actual!r}"
    if op == 'contains':
        try:
            ok = expected in actual
        except TypeError:
            ok = False
        return None if ok else f"{path}: expected to contain {expected!r}, got {actual!r}"
    if op == 'length_eq':
        try:
            length = len(actual)
        except TypeError:
            return f"{path}: value has no length"
        return None if length == expected else f"{path}: expected length {expected}, got {length}"
    if op == 'collection_field_contains':
        field = str(assertion['field'])
        if not isinstance(actual, list):
            return f"{path}: expected list, got {type(actual).__name__}"
        values = [item.get(field) for item in actual if isinstance(item, dict)]
        return None if expected in values else f"{path}: expected some {field}={expected!r}, got {values!r}"
    return f"{path}: unsupported assertion op {op!r}"


def build_diagnostics(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    diagnostics: dict[str, Any] = {}
    for key in ("trace_id", "validated_sql", "selected_route", "fallback_used", "errors"):
        if key in payload:
            diagnostics[key] = payload[key]
    query_result = payload.get("query_result")
    if isinstance(query_result, dict):
        diagnostics["query_result"] = {
            key: query_result.get(key)
            for key in ("row_count", "tables", "columns")
            if key in query_result
        }
    analysis_result = payload.get("analysis_result")
    if isinstance(analysis_result, dict):
        operations = analysis_result.get("operations")
        if isinstance(operations, list):
            diagnostics["analysis_operations"] = [
                item.get("operation") for item in operations if isinstance(item, dict)
            ]
    return diagnostics or None


def request_json(base_url: str, case: dict[str, Any], timeout: float) -> tuple[int, Any]:
    method = str(case.get('method', 'GET')).upper()
    body = case.get('body')
    data = None if body is None else json.dumps(body).encode('utf-8')
    request = Request(
        base_url.rstrip('/') + str(case['path']),
        data=data,
        method=method,
        headers={'Content-Type': 'application/json'} if data is not None else {},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode('utf-8')
            return int(response.status), json.loads(raw) if raw else None
    except HTTPError as exc:
        raw = exc.read().decode('utf-8')
        return int(exc.code), json.loads(raw) if raw else None


def run_case(base_url: str, case: dict[str, Any], timeout: float) -> CaseResult:
    started = time.perf_counter()
    try:
        status, payload = request_json(base_url, case, timeout)
        expected_status = int(case.get('expected_status', 200))
        failures = []
        if status != expected_status:
            failures.append(f"HTTP status: expected {expected_status}, got {status}")
        for assertion in case.get('assertions', []):
            failure = check_assertion(payload, assertion)
            if failure:
                failures.append(failure)
        return CaseResult(
            case_id=str(case['id']),
            name=str(case['name']),
            passed=not failures,
            status=status,
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
            failures=failures,
            diagnostics=build_diagnostics(payload) if failures else None,
        )
    except (URLError, TimeoutError, ValueError, OSError) as exc:
        return CaseResult(
            case_id=str(case['id']),
            name=str(case['name']),
            passed=False,
            status=None,
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
            failures=[],
            error=str(exc),
        )


def write_reports(results: list[CaseResult], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    passed = sum(item.passed for item in results)
    payload = {
        'suite': 'P1 Stage 3.8 End-to-End Acceptance',
        'cases': len(results),
        'passed': passed,
        'failed': len(results) - passed,
        'results': [asdict(item) for item in results],
    }
    json_path = output_dir / 'acceptance-report.json'
    md_path = output_dir / 'acceptance-report.md'
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')

    lines = [
        '# P1 Stage 3.8 Acceptance Report', '',
        f"- Cases: {len(results)}",
        f"- Passed: {passed}",
        f"- Failed: {len(results) - passed}", '',
        '| Case | Result | HTTP | Time |',
        '| --- | --- | ---: | ---: |',
    ]
    for item in results:
        lines.append(f"| {item.case_id} — {item.name} | {'PASS' if item.passed else 'FAIL'} | {item.status or '—'} | {item.elapsed_ms:.2f} ms |")
        if item.error:
            lines.extend(['', f"**{item.case_id} error:** `{item.error}`"])
        for failure in item.failures:
            lines.extend(['', f"**{item.case_id} failure:** {failure}"])
        if item.diagnostics:
            lines.extend(['', f"**{item.case_id} diagnostics:**", '', '```json', json.dumps(item.diagnostics, indent=2, ensure_ascii=False), '```'])
    md_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description='Run P1 Stage 3.8 end-to-end acceptance suite')
    parser.add_argument('--base-url', default='http://localhost:8080')
    parser.add_argument('--cases', default='acceptance/cases.json')
    parser.add_argument('--output-dir', default='acceptance/results')
    parser.add_argument('--timeout', type=float, default=120.0)
    parser.add_argument('--case', action='append', dest='case_ids', help='Run only selected case id; repeatable')
    args = parser.parse_args()

    payload = json.loads(Path(args.cases).read_text(encoding='utf-8'))
    cases = list(payload['cases'])
    if args.case_ids:
        wanted = set(args.case_ids)
        cases = [case for case in cases if case['id'] in wanted]
    results = [run_case(args.base_url, case, args.timeout) for case in cases]
    json_path, md_path = write_reports(results, Path(args.output_dir))
    passed = sum(item.passed for item in results)
    for item in results:
        print(f"{'PASS' if item.passed else 'FAIL'} {item.case_id} {item.name} ({item.elapsed_ms:.0f} ms)")
        for failure in item.failures:
            print(f"  - {failure}")
        if item.error:
            print(f"  - {item.error}")
    print(f"summary: {passed}/{len(results)} passed")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")
    return 0 if passed == len(results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
