"""Compare baseline and simulated-control exposure using canonical path identity."""
import hashlib
import json

from .control_engine import apply_controls
from .graph_engine import build_graph
from .models import ModelError
from .pathfinder import find_paths
from .risk_engine import score_path

SEVERITIES = ("Low", "Medium", "High", "Critical")


def summarize(findings) -> dict:
    findings = tuple(findings)
    baseline_severity = {name: 0 for name in SEVERITIES}
    remaining_severity = {name: 0 for name in SEVERITIES}
    baseline_exposure = residual_exposure = 0
    counts = {name: 0 for name in ("blocked", "reduced", "unchanged")}
    for finding in findings:
        before = finding["baseline"]
        after = finding["residual"]
        baseline_severity[before["severity"]] += 1
        baseline_exposure += before["riskScore"]
        counts[finding["outcome"]] += 1
        if after is not None:
            remaining_severity[after["severity"]] += 1
            residual_exposure += after["riskScore"]
    return {"baselinePaths": len(findings), "blockedPaths": counts["blocked"],
            "remainingPaths": counts["reduced"] + counts["unchanged"],
            "reducedPaths": counts["reduced"], "unchangedPaths": counts["unchanged"],
            "baselineExposure": baseline_exposure, "residualExposure": residual_exposure,
            "exposureReductionPercent": round(100 * (baseline_exposure - residual_exposure) / baseline_exposure, 2) if baseline_exposure else 0.0,
            "baselineSeverity": baseline_severity, "remainingSeverity": remaining_severity}


def compare_scenario(env, scenario, risk_model, controls, selected_ids, *,
                     max_depth=12, max_paths=10_000, max_expansions=100_000) -> dict:
    controls = tuple(controls)
    graph = build_graph(env, scenario)
    bounds = {"max_depth": max_depth, "max_paths": max_paths, "max_expansions": max_expansions}
    baseline = find_paths(graph, scenario.source, scenario.target, **bounds)
    applied = apply_controls(graph, controls, selected_ids)
    controlled = find_paths(applied.graph, scenario.source, scenario.target, **bounds)
    before_by_edges = {path.edge_ids: path for path in baseline.paths}
    after_by_edges = {path.edge_ids: path for path in controlled.paths}
    if after_by_edges.keys() - before_by_edges.keys():
        raise ModelError("Control simulation unexpectedly introduced a new attack path")
    effects_by_edge = {edge_id: [] for edge_id in graph.edges}
    for effect in applied.effects:
        effects_by_edge[effect.edge_id].append(effect)
    relevant_by_edge = {
        edge.id: {control.id for control in controls for rule in control.rules
                  if rule.tag in edge.tags and (not rule.targets or edge.target in rule.targets)}
        for edge in graph.edges.values()
    }
    findings = []
    for key, path in before_by_edges.items():
        before = score_path(graph, path, risk_model)
        remaining = after_by_edges.get(key)
        after = score_path(applied.graph, remaining, risk_model) if remaining else None
        if after and after.risk_score > before.risk_score:
            raise ModelError("Control simulation unexpectedly increased path risk")
        effects = sorted((effect for edge_id in key for effect in effects_by_edge[edge_id]),
                         key=lambda effect: (effect.edge_id, effect.control_id, effect.rule_id))
        blocked_at = [edge_id for edge_id in key if any(effect.edge_id == edge_id and effect.action == "block" for effect in effects)]
        if (after is None) != bool(blocked_at):
            raise ModelError("A missing path must have a recorded blocking transition")
        relevant = sorted({control_id for edge_id in key for control_id in relevant_by_edge[edge_id]})
        outcome = "blocked" if after is None else "reduced" if after.risk_score < before.risk_score else "unchanged"
        reasons = [f"{effect.control_id}/{effect.rule_id} at {effect.edge_id}: {effect.reason}" for effect in effects]
        if outcome == "blocked":
            explanation = "The simulated path is blocked at " + ", ".join(blocked_at) + "."
        elif outcome == "reduced":
            explanation = f"The path remains; ordinal risk decreases from {before.risk_score} to {after.risk_score}."
        else:
            explanation = "The path remains with unchanged ordinal risk."
            if effects:
                explanation += " Matched control rules do not lower the path's minimum likelihood."
            else:
                explanation += " No selected rule matches its transitions."
        if reasons:
            explanation += " " + " ".join(reasons)
        finding_id = "SITAS-F-" + hashlib.sha256(json.dumps([scenario.id, key], separators=(",", ":")).encode()).hexdigest()[:16]
        finding = {"findingId": finding_id, "pathId": path.id, "scenarioId": scenario.id,
                   "title": scenario.title, "sourceNode": scenario.source, "targetNode": scenario.target,
                   "orderedPath": list(path.node_ids), "orderedEdges": list(key), "pathLength": len(key),
                   **before.to_dict(), "baseline": before.to_dict(), "residual": after.to_dict() if after else None,
                   "controlsRelevant": relevant, "controlsApplied": sorted({effect.control_id for effect in effects}),
                   "blocked": after is None, "blockedAt": blocked_at, "outcome": outcome,
                   "controlEffects": [effect.to_dict() for effect in effects],
                   "explanation": explanation, "recommendation": scenario.recommendation}
        findings.append(finding)
    findings.sort(key=lambda item: (-item["riskScore"], item["pathId"]))
    return {"scenarioId": scenario.id, "title": scenario.title, "description": scenario.description,
            "sourceNode": scenario.source, "targetNode": scenario.target, "edgeIds": list(scenario.edge_ids),
            "summary": summarize(findings), "findings": findings,
            "search": {"baseline": {"expansions": baseline.expansions, "depthPruned": baseline.depth_pruned},
                       "controlled": {"expansions": controlled.expansions, "depthPruned": controlled.depth_pruned}}}
