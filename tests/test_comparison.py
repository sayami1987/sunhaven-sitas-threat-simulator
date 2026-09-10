"""Independent small-path calculations verify comparison and reconciliation."""

from dataclasses import replace

import pytest

from src.comparison_engine import compare_scenario, summarize
from src.models import Control, Edge, Environment, ModelError, Node, RiskModel, Rule, Scenario, SeverityBand


@pytest.fixture
def risk_model():
    return RiskModel("minimum", (
        SeverityBand("Low", 1, 4), SeverityBand("Medium", 5, 9),
        SeverityBand("High", 10, 16), SeverityBand("Critical", 17, 25),
    ))


def edge(identifier, source, target, likelihood, *tags):
    return Edge(identifier, source, target, "synthetic_transition", likelihood,
                tuple(tags), "A fictional transition for a handcrafted test.")


def scenario_for(environment, identifier="ThreeRoutes"):
    return Scenario(identifier, "Synthetic route comparison", "Handcrafted fictional routes.",
                    "S", "T", tuple(item.id for item in environment.edges),
                    "Review the explicitly modelled transition controls.")


def findings_by_edges(result):
    findings = result["findings"]
    indexed = {tuple(finding["orderedEdges"]): finding for finding in findings}
    assert len(indexed) == len(findings), "Every ordered edge path must retain a distinct finding"
    return indexed


@pytest.fixture
def three_routes():
    environment = Environment("Synthetic", "Synthetic comparison environment", (
        Node("S", "Synthetic attacker", "attacker", {}),
        Node("B", "Synthetic blocked branch", "identity", {}),
        Node("R", "Synthetic reduced branch", "identity", {}),
        Node("U", "Synthetic unchanged branch", "identity", {}),
        Node("T", "Synthetic protected asset", "asset", {"impact": 5}),
    ), (
        edge("B1", "S", "B", 4, "blockable"), edge("B2", "B", "T", 5),
        edge("R1", "S", "R", 4, "reducible"), edge("R2", "R", "T", 5),
        edge("U1", "S", "U", 2), edge("U2", "U", "T", 5),
    ))
    controls = (
        Control("Block", "Synthetic blocker", "Blocks only the B branch.", (
            Rule("BlockRule", "blockable", "block", "Synthetic branch blocked."),
        )),
        Control("Cap", "Synthetic cap", "Caps only the R branch.", (
            Rule("CapRule", "reducible", "cap", "Synthetic branch capped.", cap=2),
        )),
    )
    return environment, scenario_for(environment), controls


def test_SITAS_T20_reconciles_blocked_reduced_unchanged_and_exposure(three_routes, risk_model):
    environment, scenario, controls = three_routes
    result = compare_scenario(environment, scenario, risk_model, controls, ["Block", "Cap"])
    findings = findings_by_edges(result)

    # Manually enumerated routes: B=4*5=20; R=4*5=20; U=2*5=10.
    assert set(findings) == {("B1", "B2"), ("R1", "R2"), ("U1", "U2")}
    assert {key: finding["outcome"] for key, finding in findings.items()} == {
        ("B1", "B2"): "blocked", ("R1", "R2"): "reduced", ("U1", "U2"): "unchanged",
    }
    summary = result["summary"]
    assert summary == {
        "baselinePaths": 3, "blockedPaths": 1, "remainingPaths": 2,
        "reducedPaths": 1, "unchangedPaths": 1,
        "baselineExposure": 50, "residualExposure": 20,
        "exposureReductionPercent": 60.0,
        "baselineSeverity": {"Low": 0, "Medium": 0, "High": 1, "Critical": 2},
        "remainingSeverity": {"Low": 0, "Medium": 0, "High": 2, "Critical": 0},
    }
    assert summary["baselinePaths"] == summary["blockedPaths"] + summary["remainingPaths"]
    assert summary["remainingPaths"] == summary["reducedPaths"] + summary["unchangedPaths"]
    assert summarize(result["findings"]) == summary


def test_blocked_findings_retain_baseline_without_inventing_low_residual_risk(three_routes, risk_model):
    environment, scenario, controls = three_routes
    result = compare_scenario(environment, scenario, risk_model, controls, ["Block", "Cap"])
    blocked = findings_by_edges(result)[("B1", "B2")]
    assert blocked["blocked"] is True
    assert blocked["blockedAt"] == ["B1"]
    assert blocked["residual"] is None
    assert blocked["baseline"] == {"likelihood": 4, "impact": 5, "riskScore": 20, "severity": "Critical"}
    assert {key: blocked[key] for key in blocked["baseline"]} == blocked["baseline"]
    assert blocked["controlsApplied"] == ["Block"]
    assert "Cap" not in blocked["controlsRelevant"]
    assert blocked["controlEffects"]
    assert all(effect["controlId"] == "Block" and effect["edgeId"] == "B1"
               and effect["action"] == "block" for effect in blocked["controlEffects"])
    assert blocked["explanation"] and blocked["recommendation"]


def test_reduced_finding_preserves_baseline_fields_and_records_remaining_score(three_routes, risk_model):
    environment, scenario, controls = three_routes
    result = compare_scenario(environment, scenario, risk_model, controls, ["Block", "Cap"])
    reduced = findings_by_edges(result)[("R1", "R2")]
    assert reduced["blocked"] is False
    assert reduced["blockedAt"] == []
    assert reduced["baseline"] == {"likelihood": 4, "impact": 5, "riskScore": 20, "severity": "Critical"}
    assert reduced["residual"] == {"likelihood": 2, "impact": 5, "riskScore": 10, "severity": "High"}
    assert {key: reduced[key] for key in reduced["baseline"]} == reduced["baseline"]
    assert reduced["controlsApplied"] == ["Cap"]
    assert reduced["orderedPath"] == ["S", "R", "T"]
    assert reduced["pathLength"] == 2


def test_cap_can_change_an_edge_without_changing_the_path_bottleneck(risk_model):
    environment = Environment("Bottleneck", "Synthetic bottleneck", (
        Node("S", "Synthetic attacker", "attacker", {}),
        Node("A", "Synthetic intermediate", "identity", {}),
        Node("T", "Synthetic asset", "asset", {"impact": 5}),
    ), (edge("Capped", "S", "A", 5, "cap_tag"), edge("Bottleneck", "A", "T", 2)))
    controls = (Control("Cap", "Synthetic cap", "The other transition remains the bottleneck.", (
        Rule("CapRule", "cap_tag", "cap", "Reduce this transition from five to three.", cap=3),
    )),)
    result = compare_scenario(environment, scenario_for(environment, "BottleneckCase"), risk_model, controls, ["Cap"])
    finding, = result["findings"]
    assert finding["outcome"] == "unchanged"
    assert finding["baseline"] == finding["residual"] == {
        "likelihood": 2, "impact": 5, "riskScore": 10, "severity": "High",
    }
    assert finding["controlsApplied"] == ["Cap"]
    assert any(effect["edgeId"] == "Capped" and effect["controlId"] == "Cap"
               and effect["action"] == "cap" and effect["beforeLikelihood"] == 5
               and effect["afterLikelihood"] == 3 for effect in finding["controlEffects"])
    assert result["summary"]["reducedPaths"] == 0
    assert result["summary"]["unchangedPaths"] == 1
    assert result["summary"]["exposureReductionPercent"] == 0


def test_parallel_edge_paths_are_matched_by_ordered_edge_ids(risk_model):
    environment = Environment("Parallel", "Synthetic parallel routes", (
        Node("S", "Synthetic attacker", "attacker", {}),
        Node("A", "Synthetic identity", "identity", {}),
        Node("T", "Synthetic asset", "asset", {"impact": 4}),
    ), (edge("Unsafe", "S", "A", 4, "blockable"),
        edge("Other", "S", "A", 3), edge("Tail", "A", "T", 5)))
    controls = (Control("Block", "Synthetic blocker", "Only one of two parallel transitions.", (
        Rule("BlockRule", "blockable", "block", "Block the unsafe parallel edge."),
    )),)
    result = compare_scenario(environment, scenario_for(environment, "ParallelCase"), risk_model, controls, ["Block"])
    findings = findings_by_edges(result)
    blocked, remaining = findings[("Unsafe", "Tail")], findings[("Other", "Tail")]
    assert blocked["orderedPath"] == remaining["orderedPath"] == ["S", "A", "T"]
    assert blocked["pathId"] != remaining["pathId"]
    assert blocked["findingId"] != remaining["findingId"]
    assert blocked["outcome"] == "blocked" and blocked["residual"] is None
    assert remaining["outcome"] == "unchanged" and remaining["residual"]["riskScore"] == 12
    assert result["summary"]["baselinePaths"] == 2
    assert result["summary"]["remainingPaths"] == 1


def test_all_blocked_paths_contribute_no_remaining_severity_or_exposure(three_routes, risk_model):
    environment, scenario, controls = three_routes
    environment = replace(environment, edges=tuple(
        replace(item, tags=("blockable",)) if item.source == "S" else item
        for item in environment.edges
    ))
    result = compare_scenario(environment, scenario, risk_model, controls[:1], ["Block"])
    assert result["summary"]["blockedPaths"] == result["summary"]["baselinePaths"] == 3
    assert result["summary"]["remainingPaths"] == 0
    assert result["summary"]["residualExposure"] == 0
    assert result["summary"]["exposureReductionPercent"] == 100.0
    assert result["summary"]["remainingSeverity"] == {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    assert all(finding["residual"] is None for finding in result["findings"])


def test_zero_path_analysis_has_zero_exposure_reduction(risk_model):
    environment = Environment("Disconnected", "Synthetic disconnected target", (
        Node("S", "Synthetic attacker", "attacker", {}),
        Node("T", "Synthetic asset", "asset", {"impact": 5}),
    ), ())
    result = compare_scenario(environment, scenario_for(environment, "DisconnectedCase"), risk_model, (), [])
    assert result["findings"] == []
    assert result["summary"] == summarize([]) == {
        "baselinePaths": 0, "blockedPaths": 0, "remainingPaths": 0,
        "reducedPaths": 0, "unchangedPaths": 0,
        "baselineExposure": 0, "residualExposure": 0, "exposureReductionPercent": 0,
        "baselineSeverity": {"Low": 0, "Medium": 0, "High": 0, "Critical": 0},
        "remainingSeverity": {"Low": 0, "Medium": 0, "High": 0, "Critical": 0},
    }


def test_no_selected_controls_preserves_every_baseline_path(three_routes, risk_model):
    environment, scenario, controls = three_routes
    result = compare_scenario(environment, scenario, risk_model, controls, [])
    assert result["summary"]["baselineExposure"] == result["summary"]["residualExposure"] == 50
    assert result["summary"]["unchangedPaths"] == 3
    for finding in result["findings"]:
        assert finding["baseline"] == finding["residual"]
        assert finding["outcome"] == "unchanged"
        assert finding["controlsApplied"] == []
        assert finding["controlEffects"] == []


def test_permuted_inputs_and_control_selection_preserve_canonical_findings(three_routes, risk_model):
    environment, scenario, controls = three_routes
    expected = compare_scenario(environment, scenario, risk_model, controls, ["Block", "Cap"])
    reversed_environment = replace(environment, nodes=tuple(reversed(environment.nodes)), edges=tuple(reversed(environment.edges)))
    reversed_scenario = replace(scenario, edge_ids=tuple(reversed(scenario.edge_ids)))
    actual = compare_scenario(reversed_environment, reversed_scenario, risk_model,
                              tuple(reversed(controls)), ["Cap", "Block"])
    assert actual["findings"] == expected["findings"]
    assert actual["summary"] == expected["summary"]
    assert compare_scenario(environment, scenario, risk_model, controls, ["Block", "Cap"])["findings"] == expected["findings"]
    assert {item.id: item.likelihood for item in environment.edges} == {
        "B1": 4, "B2": 5, "R1": 4, "R2": 5, "U1": 2, "U2": 5,
    }


@pytest.mark.parametrize("limits", [{"max_paths": 1}, {"max_expansions": 1}])
def test_resource_exhaustion_raises_instead_of_returning_partial_comparison(three_routes, risk_model, limits):
    environment, scenario, controls = three_routes
    with pytest.raises(ModelError):
        compare_scenario(environment, scenario, risk_model, controls, ["Block", "Cap"], **limits)


def test_depth_bound_is_retained_in_search_evidence(three_routes, risk_model):
    environment, scenario, controls = three_routes
    result = compare_scenario(environment, scenario, risk_model, controls, ["Block", "Cap"], max_depth=1)
    assert result["findings"] == []
    assert result["summary"]["baselinePaths"] == 0
    for phase in ("baseline", "controlled"):
        assert result["search"][phase]["expansions"] >= 0
        assert result["search"][phase]["depthPruned"] > 0
