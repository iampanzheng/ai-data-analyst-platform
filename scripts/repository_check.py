from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_TRACKED_BYTES = 20 * 1024 * 1024
MAX_SECRET_SCAN_BYTES = 2 * 1024 * 1024

FORBIDDEN_TRACKED_PATTERNS = (
    re.compile(r"(^|/)\.env$"),
    re.compile(r"(^|/)\.venv(/|$)"),
    re.compile(r"(^|/)node_modules(/|$)"),
    re.compile(r"(^|/)dist(/|$)"),
    re.compile(r"(^|/)__pycache__(/|$)"),
    re.compile(r"\.zip$", re.IGNORECASE),
    re.compile(r"\.tar(?:\.gz)?$", re.IGNORECASE),
)

FORBIDDEN_HISTORY_PATHS = (
    re.compile(r"(^|/)\.env$"),
    re.compile(r"\.zip$", re.IGNORECASE),
    re.compile(r"\.tar(?:\.gz)?$", re.IGNORECASE),
)

SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "Groq secret": re.compile(r"\bgsk_[A-Za-z0-9]{20,}\b"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
}

REQUIRED_PUBLIC_ASSETS = (
    "README.md",
    "LICENSE",
    "docs/GITHUB-METADATA.md",
    "docs/DEMO.md",
    "docs/PORTFOLIO.md",
    "docs/assets/analyst-workspace.png",
    "docs/assets/controlled-chart.png",
    "docs/assets/evidence-report.png",
    "docs/assets/provenance.png",
    "docs/assets/p1-ai-data-analyst-demo.mp4",
    ".github/workflows/ci.yml",
)


@dataclass(frozen=True)
class Finding:
    kind: str
    location: str
    detail: str


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def ensure_git_repository() -> None:
    result = run_git("rev-parse", "--is-inside-work-tree", check=False)
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise SystemExit("repository-check requires execution inside the project Git working tree")


def tracked_paths() -> list[str]:
    result = run_git("ls-files", "-z")
    return [item for item in result.stdout.split("\0") if item]


def decode_text(data: bytes) -> str | None:
    if b"\x00" in data[:4096]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def scan_text(location: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for label, pattern in SECRET_PATTERNS.items():
        if pattern.search(text):
            findings.append(Finding("secret", location, f"matched {label} pattern"))
    return findings


def check_current_tree(paths: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    path_set = set(paths)

    for required in REQUIRED_PUBLIC_ASSETS:
        if required not in path_set:
            findings.append(Finding("missing", required, "required public/CI asset is not tracked"))

    for rel in paths:
        if any(pattern.search(rel) for pattern in FORBIDDEN_TRACKED_PATTERNS):
            findings.append(Finding("tracked-path", rel, "forbidden generated/local artifact is tracked"))
            continue

        path = ROOT / rel
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            continue

        if size > MAX_TRACKED_BYTES:
            findings.append(
                Finding("large-file", rel, f"tracked file is {size / (1024 * 1024):.1f} MiB (>20 MiB)")
            )

        if size <= MAX_SECRET_SCAN_BYTES:
            try:
                data = path.read_bytes()
            except OSError:
                continue
            text = decode_text(data)
            if text is not None:
                findings.extend(scan_text(rel, text))

    return findings


def history_objects() -> list[tuple[str, str]]:
    result = run_git("rev-list", "--objects", "--all")
    objects: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        oid, sep, path = line.partition(" ")
        if oid and sep and path:
            objects.append((oid, path))
    return objects


def check_history() -> list[Finding]:
    findings: list[Finding] = []
    seen_blobs: set[str] = set()

    for oid, path in history_objects():
        if any(pattern.search(path) for pattern in FORBIDDEN_HISTORY_PATHS):
            findings.append(Finding("history-path", path, "sensitive/local artifact exists in Git history"))

        if oid in seen_blobs:
            continue
        seen_blobs.add(oid)

        size_result = run_git("cat-file", "-s", oid, check=False)
        if size_result.returncode != 0:
            continue
        try:
            size = int(size_result.stdout.strip())
        except ValueError:
            continue
        if size > MAX_TRACKED_BYTES:
            findings.append(
                Finding("history-large-file", path, f"historical object is {size / (1024 * 1024):.1f} MiB (>20 MiB)")
            )
        if size > MAX_SECRET_SCAN_BYTES:
            continue

        blob = subprocess.run(
            ["git", "cat-file", "blob", oid],
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        if blob.returncode != 0:
            continue
        text = decode_text(blob.stdout)
        if text is not None:
            findings.extend(scan_text(f"history:{path}@{oid[:12]}", text))

    # Deduplicate identical path/detail findings that can arise from many historical blobs.
    unique = {(f.kind, f.location, f.detail): f for f in findings}
    return list(unique.values())



def check_ci_workflow_policy() -> list[Finding]:
    path = ROOT / ".github/workflows/ci.yml"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [Finding("ci-policy", str(path.relative_to(ROOT)), "CI workflow is missing")]

    findings: list[Finding] = []
    if "pull_request_target:" in text:
        findings.append(Finding("ci-policy", ".github/workflows/ci.yml", "pull_request_target is not allowed"))
    if "permissions:\n  contents: read" not in text:
        findings.append(Finding("ci-policy", ".github/workflows/ci.yml", "workflow must keep contents: read permissions"))

    action_uses = re.findall(r"^\s*uses:\s*([^\s#]+)", text, flags=re.MULTILINE)
    for action in action_uses:
        if action.startswith("./") or action.startswith("docker://"):
            continue
        ref = action.rsplit("@", 1)[-1] if "@" in action else ""
        if not re.fullmatch(r"[0-9a-fA-F]{40}", ref):
            findings.append(
                Finding("ci-policy", ".github/workflows/ci.yml", f"third-party action is not pinned to a full commit SHA: {action}")
            )
    return findings

def print_findings(findings: list[Finding]) -> None:
    for finding in sorted(findings, key=lambda item: (item.kind, item.location, item.detail)):
        print(f"ERROR [{finding.kind}] {finding.location}: {finding.detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check P1 repository publication hygiene.")
    parser.add_argument(
        "--history",
        action="store_true",
        help="also scan all Git history for forbidden paths and strong secret patterns",
    )
    args = parser.parse_args()

    ensure_git_repository()
    paths = tracked_paths()
    findings = check_current_tree(paths)
    findings.extend(check_ci_workflow_policy())
    if args.history:
        findings.extend(check_history())

    if findings:
        print_findings(findings)
        return 1

    mode = "current tree + Git history" if args.history else "current tracked tree"
    print(f"repository publication hygiene: PASS ({mode})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
