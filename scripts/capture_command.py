"""Execute a command and retain its actual stdout, stderr and exit status."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command[:1] == ["--"]:
        command = command[1:]
    if not command:
        parser.error("a command is required")
    actual = [sys.executable if command[0] == "python" else command[0], *command[1:]]
    started = datetime.now(timezone.utc).isoformat()
    completed = subprocess.run(actual, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True)
    finished = datetime.now(timezone.utc).isoformat()
    log = ROOT / args.log
    log.parent.mkdir(parents=True, exist_ok=True)
    result = {"command": command, "workingDirectory": ".", "pythonVersion": sys.version.split()[0],
              "startedUtc": started, "finishedUtc": finished, "exitCode": completed.returncode,
              "stdout": completed.stdout, "stderr": completed.stderr}
    log.write_text(f"Started UTC: {started}\nCommand: {json.dumps(command)}\nExit code: {completed.returncode}\n\nSTDOUT\n{completed.stdout}\nSTDERR\n{completed.stderr}", encoding="utf-8")
    log.with_suffix(".execution.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(completed.stdout, end="")
    print(completed.stderr, end="", file=sys.stderr)
    print(f"Evidence: {log.relative_to(ROOT)}; exit={completed.returncode}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
