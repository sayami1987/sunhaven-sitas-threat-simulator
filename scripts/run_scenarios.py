"""Execute all packaged scenarios and retain real analysis evidence."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.comparison_engine import compare_scenario, summarize
from src.model_loader import load_controls, load_environment, load_risk_model, load_scenarios
from src.models import ModelError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controls", default="all", help="all, none or comma-separated control IDs")
    parser.add_argument("--json", type=Path, help="Optional evidence output file")
    args = parser.parse_args()
    try:
        env = load_environment(ROOT / "config/environment.json")
        controls = load_controls(ROOT / "config/controls.json", env)
        risk = load_risk_model(ROOT / "config/risk-model.json")
        scenarios = load_scenarios(ROOT / "scenarios", env)
        selected = [control.id for control in controls] if args.controls == "all" else [] if args.controls == "none" else args.controls.split(",")
        results = [compare_scenario(env, scenario, risk, controls, selected) for scenario in scenarios]
    except ModelError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    findings = [finding for result in results for finding in result["findings"]]
    result = {"environmentId": env.id, "selectedControls": sorted(set(selected)),
              "summary": summarize(findings), "scenarios": results}
    print("Scenario | Baseline | Blocked | Remaining | Reduced | Unchanged")
    for scenario in results:
        summary = scenario["summary"]
        print(" | ".join([scenario["scenarioId"], *(str(summary[key]) for key in
                       ["baselinePaths", "blockedPaths", "remainingPaths", "reducedPaths", "unchangedPaths"])]))
    print(json.dumps(result["summary"], indent=2))
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"Saved actual scenario results: {args.json}")
    print("Synthetic scenario-path records; shared relationships are not independent real-world incidents.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
