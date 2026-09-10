"""Render the screenshot register from metadata for files that actually exist."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = ROOT / "evidence/screenshots/captures.json"
    rows = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    lines = ["# Screenshot Evidence Register", "",
             "These are genuine application captures. Diagram exports and command logs are stored separately and are not called screenshots.", "",
             "| Number | Filename | UTC time | Phase | Task and action | Expected | Actual | Requirement | Test | Commit |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in sorted(rows, key=lambda item: int(item["number"])):
        if not (ROOT / row["filename"]).is_file():
            raise ValueError(f"Screenshot missing: {row['filename']}")
        cells = [row["number"], row["filename"], row["captured_at_utc"], row["phase"], row["task"] + "; " + row["action"], row["expected"], row["actual"], row["requirement"], row["test"], row["commit"]]
        lines.append("| " + " | ".join(str(x).replace("|", "/").replace("\n", " ") for x in cells) + " |")
    lines += ["", "Capture methods and privacy-review notes are recorded in `screenshots/captures.json`.", "",
              "Native terminal automation is unavailable under the installed computer-use tool's rules. Actual terminal output is preserved in `logs/`. For a terminal screenshot, run the exact command in the corresponding execution JSON, then capture the command, complete result and visible application title manually. Do not replace command evidence with a drawn terminal image.", ""]
    (ROOT / "evidence/Screenshot-Evidence-Register.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Registered {len(rows)} existing genuine screenshot files")


if __name__ == "__main__":
    main()
