"""Run actual baseline and MFA comparisons on the synthetic graph catalogue."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.comparison_engine import compare_scenario
from src.model_loader import load_controls, load_environment, load_risk_model
from src.models import Scenario


def main():
    env = load_environment(ROOT / "config/environment.json")
    controls = load_controls(ROOT / "config/controls.json", env)
    risk = load_risk_model(ROOT / "config/risk-model.json")
    scenario = Scenario("control_demonstration", "Fictional care-record routes", "Whole-catalogue control example.",
                        "attacker_external", "asset_care_records", tuple(edge.id for edge in env.edges),
                        "Review remaining social-engineering routes and model assumptions.")
    for selected in ((), ("mfa",)):
        result = compare_scenario(env, scenario, risk, controls, selected)
        print(f"Selected controls: {list(selected)}")
        print(json.dumps(result["summary"], indent=2))
        for finding in result["findings"]:
            print(f"{finding['pathId']} {finding['outcome']}: {finding['explanation']}")


if __name__ == "__main__":
    main()
