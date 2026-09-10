"""Validate local SITAS configuration without executing an analysis."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.model_loader import load_controls, load_environment, load_risk_model, load_scenarios
from src.models import ModelError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", type=Path, default=ROOT / "config/environment.json")
    parser.add_argument("--controls", type=Path, default=ROOT / "config/controls.json")
    parser.add_argument("--risk", type=Path, default=ROOT / "config/risk-model.json")
    parser.add_argument("--scenarios", type=Path)
    args = parser.parse_args()
    try:
        env = load_environment(args.environment)
        controls = load_controls(args.controls, env)
        risk = load_risk_model(args.risk)
        scenarios = load_scenarios(args.scenarios, env) if args.scenarios else ()
    except ModelError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"VALID: {env.id} ({env.name})")
    print(f"Synthetic model: {len(env.nodes)} nodes, {len(env.edges)} directed edges")
    print(f"Controls: {len(controls)}; severity bands: {len(risk.bands)}; likelihood: {risk.likelihood_method}")
    print(f"Scenarios validated: {len(scenarios)}" if args.scenarios else "Scenario directory not selected for this validation run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
