"""Static P1 release-candidate checks; no GitHub credentials or network required."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ["README.md", "LICENSE", "docs/RELEASE.md", "docs/PHASE4-STAGE4.5-RELEASE-PLAN.md", "docs/assets/p1-ai-data-analyst-demo.mp4", ".github/workflows/ci.yml", "PROJECT-CONTEXT.md"]

def main() -> int:
    issues = []
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            issues.append(f"missing: {rel}")
    if not issues:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        notes = (ROOT / "docs/RELEASE.md").read_text(encoding="utf-8")
        plan = (ROOT / "docs/PHASE4-STAGE4.5-RELEASE-PLAN.md").read_text(encoding="utf-8")
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        if "MIT License" not in license_text: issues.append("LICENSE must be MIT")
        if "v1.0.0" not in notes: issues.append("release notes missing version")
        if "v1.0.0" not in plan: issues.append("release plan missing version")
        if not (ROOT / "docs/assets/p1-ai-data-analyst-demo.mp4").stat().st_size: issues.append("demo video empty")
        for link in re.findall(r"\]\((docs/assets/[^)# ]+)\)", readme):
            if not (ROOT / link).is_file(): issues.append(f"README missing asset: {link}")
        if "https://github.com/user-attachments/assets/" in readme:
            issues.append("README must not depend on temporary user-attachments demo URL")
    for issue in issues: print(f"release-check: {issue}", file=sys.stderr)
    if issues: return 1
    print("release candidate static checks: PASS (not a live GitHub Release verification)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
