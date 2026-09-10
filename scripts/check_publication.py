"""Check publishable Git files for common secret formats and private artefacts."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    patterns = {
        "GitHub credential": re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})"),
        "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "AWS key": re.compile(r"AKIA[A-Z0-9]{16}"),
        "student identifier": re.compile("1222" + "8795"),
        "JWT credential": re.compile(r"eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}"),
    }
    failures = []
    count = 0
    for name in sorted(set(names) - {""}):
        path = ROOT / name
        if not path.is_file():
            continue
        count += 1
        if path.name == ".env" or path.suffix.lower() in {".pem", ".key", ".pfx", ".p12", ".db", ".sqlite", ".zip", ".docx", ".pdf"}:
            failures.append((name, "unexpected private/binary source document or credential file"))
        data = path.read_bytes()
        if b"\0" in data:
            continue
        content = data.decode("utf-8", errors="replace")
        for label, pattern in patterns.items():
            if pattern.search(content):
                failures.append((name, label))
    for name, reason in failures:
        print(f"ERROR: {name}: {reason}; value withheld")
    print(f"Publication pattern scan: {count} files; {len(failures)} flagged files/patterns")
    print("Scope: Git-visible current files. Pattern checks supplement source and screenshot review; they do not prove absence of every possible secret.")
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
