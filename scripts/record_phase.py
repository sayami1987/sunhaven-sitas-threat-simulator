"""Append actual phase records from completed work and execution logs."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", type=int)
    parser.add_argument("--title")
    parser.add_argument("--result")
    parser.add_argument("--notes", default="No additional issue recorded.")
    parser.add_argument("--status", choices=["Completed", "Partially Completed", "Blocked"], default="Completed")
    parser.add_argument("--log", action="append", default=[])
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()
    now = datetime.now(timezone.utc).isoformat()
    folder = ROOT / "evidence" / "phases"
    folder.mkdir(exist_ok=True)
    path = folder / f"phase-{args.phase:02}.json"
    if args.commit:
        record = json.loads(path.read_text(encoding="utf-8"))
        record["commit"] = git("rev-parse", "HEAD")
        record["commitRecordedUtc"] = now
        record["committedFiles"] = git("diff-tree", "--root", "--no-commit-id", "--name-status", "-r", "HEAD").splitlines()
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        for name in ["Phase-Completion-Register.md", "Development-Journal.md"]:
            with (ROOT / "evidence" / name).open("a", encoding="utf-8") as stream:
                stream.write(f"\nPhase {args.phase:02} commit: `{record['commit']}`. Publication is verified separately in push logs.\n")
        print(record["commit"])
        return
    if path.exists():
        parser.error("phase already recorded; use a new verification record rather than overwriting history")
    if not args.title or not args.result:
        parser.error("--title and --result are required")
    logs = []
    for name in args.log:
        logpath = ROOT / name
        if not logpath.exists():
            parser.error(f"evidence does not exist: {name}")
        execution = logpath.with_suffix(".execution.json")
        logs.append({"file": name, "execution": json.loads(execution.read_text(encoding="utf-8")) if execution.exists() else None})
    changed = git("status", "--short", "--untracked-files=all").splitlines()
    record = {"phase": args.phase, "title": args.title, "recordedUtc": now, "status": args.status,
              "result": args.result, "notes": args.notes, "filesAtRecording": changed,
              "evidence": logs, "commit": None}
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    text = f"\n## Phase {args.phase:02} {args.title}\n\nUTC: {now}\n\nStatus: {args.status}. {args.result}\n\nNotes: {args.notes}\n\n"
    text += "Evidence: " + (", ".join(f"`{x['file']}`" for x in logs) or "Created artefacts recorded in the phase JSON") + ".\n"
    text += f"\nExact file/command details: `phases/phase-{args.phase:02}.json`. Commit recorded after creation.\n"
    for name in ["Development-Journal.md", "Phase-Completion-Register.md"]:
        with (ROOT / "evidence" / name).open("a", encoding="utf-8") as stream:
            stream.write(text)
    print(f"Recorded phase {args.phase:02}: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
