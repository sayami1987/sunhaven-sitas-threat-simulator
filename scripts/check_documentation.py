"""Check local documentation links and required traceability identifiers."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def main():
    documents = [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]
    failures = []
    checked = 0
    for document in documents:
        content = document.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content):
            target = target.strip("<>").split("#", 1)[0]
            if not target or re.match(r"[A-Za-z]+://", target):
                continue
            checked += 1
            if not (document.parent / target).resolve().exists():
                failures.append(f"{document.relative_to(ROOT)}: missing {target}")
    matrix = (ROOT / "docs/requirements/requirements-traceability.md").read_text(encoding="utf-8")
    for prefix, count in [("FR", 24), ("NFR", 12)]:
        for number in range(1, count + 1):
            if f"| {prefix}-{number:02} |" not in matrix:
                failures.append(f"Missing requirement row {prefix}-{number:02}")
    tests = (ROOT / "docs/testing/test-traceability.md").read_text(encoding="utf-8")
    for number in range(1, 25):
        if f"SITAS-T{number:02}" not in tests:
            failures.append(f"Missing acceptance test SITAS-T{number:02}")
    for failure in failures:
        print("ERROR: " + failure)
    print(f"Documentation: {len(documents)} files; {checked} local links; {len(failures)} issues")
    print("Identifier and link checks do not establish native diagram completion or final acceptance.")
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
