"""Offline SITAS command-line coordinator and reproducible analysis API."""
import argparse
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from .comparison_engine import compare_scenario, summarize
from .model_loader import load_controls, load_environment, load_risk_model, load_scenarios
from .models import ModelError

ROOT = Path(__file__).resolve().parents[1]


def _plain(value):
    if is_dataclass(value):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _digest(value):
    return hashlib.sha256(json.dumps(_plain(value), sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _timestamp(value):
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ModelError("timestamp must be an ISO 8601 string with a timezone") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ModelError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def analyse(*, environment_path=ROOT / "config/environment.json",
            controls_path=ROOT / "config/controls.json", risk_path=ROOT / "config/risk-model.json",
            scenario_dir=ROOT / "scenarios", controls="all", scenario_ids=None,
            max_depth=12, max_paths=10000, max_expansions=100000, timestamp=None):
    """Validate a complete input snapshot, then compare independently scoped scenarios."""
    for name, value, ceiling in [("max_depth", max_depth, 500), ("max_paths", max_paths, 100000),
                                 ("max_expansions", max_expansions, 1000000)]:
        if type(value) is not int or not 1 <= value <= ceiling:
            raise ModelError(f"{name} must be an integer from 1 to {ceiling}")
    generated_at = _timestamp(timestamp)
    env = load_environment(Path(environment_path))
    configured = load_controls(Path(controls_path), env)
    risk = load_risk_model(Path(risk_path))
    scenarios = load_scenarios(Path(scenario_dir), env)
    if not isinstance(controls, str):
        raise ModelError("controls must be all, none or comma-separated control IDs")
    available = {control.id for control in configured}
    if controls == "all":
        selected = sorted(available)
    elif controls == "none":
        selected = []
    else:
        requested = [item.strip() for item in controls.split(",")]
        unknown = set(requested) - available
        if unknown:
            raise ModelError(f"unknown or empty control IDs: {sorted(unknown)}")
        selected = sorted(set(requested))
    if scenario_ids is not None:
        if not isinstance(scenario_ids, (list, tuple)) or not scenario_ids or any(
                not isinstance(item, str) for item in scenario_ids):
            raise ModelError("scenario_ids must be a nonempty list of scenario IDs")
        unknown = set(scenario_ids) - {scenario.id for scenario in scenarios}
        if unknown:
            raise ModelError(f"unknown scenario IDs: {sorted(unknown)}")
        scenarios = tuple(scenario for scenario in scenarios if scenario.id in scenario_ids)
    settings = {"selectedControls": selected, "scenarioIds": [s.id for s in scenarios],
                "maxDepth": max_depth, "maxPaths": max_paths, "maxExpansions": max_expansions}
    input_fingerprint = _digest({"environment": env, "controls": configured,
                                  "risk": risk, "scenarios": scenarios})
    engine_fingerprint = _digest({path.name: path.read_text(encoding="utf-8")
                                   for path in sorted((ROOT / "src").glob("*.py"))})
    results = [compare_scenario(env, scenario, risk, configured, selected, max_depth=max_depth,
                               max_paths=max_paths, max_expansions=max_expansions)
               for scenario in scenarios]
    findings = [finding for result in results for finding in result["findings"]]
    return {
        "schemaVersion": 1, "title": "SITAS Threat Assessment Report", "generatedAt": generated_at,
        "simulationId": "SITAS-RUN-" + _digest({"inputs": input_fingerprint,
                         "engine": engine_fingerprint, "settings": settings})[:24],
        "inputFingerprint": input_fingerprint, "engineFingerprint": engine_fingerprint,
        "environment": {"id": env.id, "name": env.name, "synthetic": True},
        "settings": settings, "summary": summarize(findings), "scenarios": results,
        "findings": findings, "nodeNames": {node.id: node.name for node in env.nodes},
        "controls": [{"id": c.id, "name": c.name, "description": c.description}
                     for c in configured if c.id in selected],
        "assumptions": [
            "All identities, devices, applications and assets are fictional synthetic data.",
            "Each scenario selects its own relationship set and protected asset.",
            "Path likelihood is the minimum edge ordinal (1 to 5); target impact is 1 to 5.",
            "Risk is likelihood multiplied by impact: Low 1–4, Medium 5–9, High 10–16, Critical 17–25.",
            "Controls remove matching edges or cap their likelihood; blocked routes have no residual score."],
        "limitations": [
            "This is an offline model, not an intrusion test, operational control or compliance assessment.",
            "Ordinal scores and their sums are illustrative indices, not probabilities or financial loss.",
            "Shared edges across scenarios can be counted more than once in scenario-path totals.",
            "Results cover only the supplied graph and simple paths within the stated edge-depth bound.",
            "Depth-pruned transitions are reported; exceeding path or expansion limits aborts the run.",
            "MFA does not guarantee prevention of social approval or existing-session reuse.",
            "Session timeout and device separation are modelled conditions, not live enforcement."],
        "references": [
            {"title": "NIST SP 800-30 Rev. 1 — risk assessment process and uncertainty",
             "url": "https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-30r1.pdf"},
            {"title": "SANS Information Security Policy library — policy context",
             "url": "https://www.sans.org/information-security-policy"},
            {"title": "ASD ISM — system access guidance",
             "url": "https://www.cyber.gov.au/business-government/asds-cyber-security-frameworks/ism/cyber-security-guidelines/guidelines-for-system-access"}]
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="SITAS offline synthetic identity attack-path simulator")
    parser.add_argument("--environment", type=Path, default=ROOT / "config/environment.json")
    parser.add_argument("--control-config", type=Path, default=ROOT / "config/controls.json")
    parser.add_argument("--risk-model", type=Path, default=ROOT / "config/risk-model.json")
    parser.add_argument("--scenario-dir", type=Path, default=ROOT / "scenarios")
    parser.add_argument("--controls", default="all", help="all, none or comma-separated control IDs")
    parser.add_argument("--scenario", action="append", help="Scenario ID; repeat to select several")
    parser.add_argument("--max-depth", type=int, default=12, help="Maximum path length in edges")
    parser.add_argument("--max-paths", type=int, default=10000)
    parser.add_argument("--max-expansions", type=int, default=100000)
    parser.add_argument("--timestamp", help="Optional timezone-aware ISO timestamp for repeatable exports")
    parser.add_argument("--output", type=Path, default=ROOT / "reports")
    parser.add_argument("--list-scenarios", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.list_scenarios:
            env = load_environment(args.environment)
            for scenario in load_scenarios(args.scenario_dir, env):
                print(f"{scenario.id}: {scenario.title}")
            return 0
        result = analyse(environment_path=args.environment, controls_path=args.control_config,
                         risk_path=args.risk_model, scenario_dir=args.scenario_dir,
                         controls=args.controls, scenario_ids=args.scenario, max_depth=args.max_depth,
                         max_paths=args.max_paths, max_expansions=args.max_expansions,
                         timestamp=args.timestamp)
        from .report_generator import write_reports
        outputs = write_reports(result, args.output)
    except (ModelError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(result["title"])
    print(f"Run: {result['simulationId']}; synthetic environment: {result['environment']['name']}")
    print(json.dumps(result["summary"], indent=2))
    for kind, path in outputs.items():
        print(f"{kind.upper()}: {path}")
    print("Scores describe the supplied model; they are not observed incident probabilities.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
