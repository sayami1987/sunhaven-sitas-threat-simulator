"""Manual ordinal calculations and malformed paths verify risk semantics."""

from dataclasses import FrozenInstanceError

import pytest

from src.graph_engine import Graph
from src.models import Edge, ModelError, Node, RiskModel, SeverityBand
from src.pathfinder import AttackPath
from src.risk_engine import calculate_likelihood, classify_severity, rank_paths, score_path


@pytest.fixture
def risk_model():
    return RiskModel("minimum", (
        SeverityBand("Low", 1, 4), SeverityBand("Medium", 5, 9),
        SeverityBand("High", 10, 16), SeverityBand("Critical", 17, 25),
    ))


@pytest.fixture
def scored_graph():
    return Graph(
        [Node("S", "Synthetic attacker", "attacker", {}), Node("A", "Synthetic identity", "identity", {}), Node("T", "Synthetic asset", "asset", {"impact": 4})],
        [Edge("First", "S", "A", "reaches", 4, (), "Synthetic transition"), Edge("Second", "A", "T", "accesses", 3, (), "Synthetic transition")],
    )


@pytest.fixture
def valid_path():
    return AttackPath("SITAS-AP-test", ("S", "A", "T"), ("First", "Second"))


def test_SITAS_T11_likelihood_is_minimum_ordinal_value():
    assert calculate_likelihood(iter([4, 3, 5])) == 3
    assert calculate_likelihood([5]) == 5
    assert calculate_likelihood([1, 5]) == 1


def test_SITAS_T12_impact_comes_from_protected_target(scored_graph, valid_path, risk_model):
    result = score_path(scored_graph, valid_path, risk_model)
    assert result.impact == 4


def test_SITAS_T13_risk_is_path_likelihood_times_target_impact(scored_graph, valid_path, risk_model):
    result = score_path(scored_graph, valid_path, risk_model)
    assert result.likelihood == 3
    assert result.risk_score == 12
    assert result.to_dict() == {"likelihood": 3, "impact": 4, "riskScore": 12, "severity": "High"}


@pytest.mark.parametrize("score,expected", [(1, "Low"), (4, "Low"), (5, "Medium"), (9, "Medium"), (10, "High"), (16, "High"), (17, "Critical"), (25, "Critical")])
def test_SITAS_T14_severity_boundaries_are_inclusive(score, expected, risk_model):
    assert classify_severity(score, risk_model) == expected


def test_likelihood_does_not_multiply_or_average_edge_scores():
    values = [4, 3, 5]
    result = calculate_likelihood(values)
    assert result == 3
    assert result != 4 * 3 * 5
    assert result != sum(values) / len(values)


@pytest.mark.parametrize("values", [[], [True, 3], [0, 3], [6], [2.5], ["3"]])
def test_invalid_likelihood_inputs_rejected(values):
    with pytest.raises(ModelError):
        calculate_likelihood(values)


@pytest.mark.parametrize("score", [True, 0, 26, 1.5])
def test_invalid_severity_score_rejected(score, risk_model):
    with pytest.raises(ModelError):
        classify_severity(score, risk_model)


def test_severity_requires_exactly_one_matching_band():
    missing = RiskModel("minimum", (SeverityBand("Low", 1, 4),))
    overlapping = RiskModel("minimum", (SeverityBand("Low", 1, 5), SeverityBand("Medium", 5, 9)))
    with pytest.raises(ModelError):
        classify_severity(10, missing)
    with pytest.raises(ModelError):
        classify_severity(5, overlapping)


def test_unsupported_risk_method_is_rejected(scored_graph, valid_path, risk_model):
    unsupported = RiskModel("product", risk_model.bands)
    with pytest.raises(ModelError):
        score_path(scored_graph, valid_path, unsupported)


def test_empty_path_cannot_receive_a_risk_score(scored_graph, risk_model):
    with pytest.raises(ModelError):
        score_path(scored_graph, AttackPath("Empty", ("T",), ()), risk_model)


def test_path_node_and_edge_count_must_agree(scored_graph, risk_model):
    with pytest.raises(ModelError):
        score_path(scored_graph, AttackPath("WrongLength", ("S", "T"), ("First", "Second")), risk_model)


def test_path_must_not_repeat_a_node(scored_graph, risk_model):
    with pytest.raises(ModelError):
        score_path(scored_graph, AttackPath("RepeatedNode", ("S", "A", "S"), ("First", "Second")), risk_model)


def test_unknown_path_edge_is_rejected(scored_graph, risk_model):
    with pytest.raises(ModelError):
        score_path(scored_graph, AttackPath("UnknownEdge", ("S", "T"), ("Missing",)), risk_model)


def test_edge_must_match_each_ordered_node_transition(scored_graph, risk_model):
    with pytest.raises(ModelError):
        score_path(scored_graph, AttackPath("ReversedEdges", ("S", "A", "T"), ("Second", "First")), risk_model)


def test_score_target_must_be_asset(scored_graph, risk_model):
    with pytest.raises(ModelError):
        score_path(scored_graph, AttackPath("IdentityTarget", ("S", "A"), ("First",)), risk_model)


@pytest.mark.parametrize("attributes", [{}, {"impact": True}, {"impact": 0}, {"impact": 6}])
def test_target_impact_is_revalidated_for_directly_constructed_graph(attributes, risk_model):
    direct = Graph(
        [Node("S", "Synthetic start", "attacker", {}), Node("T", "Synthetic asset", "asset", attributes)],
        [Edge("Direct", "S", "T", "reaches", 3, (), "Synthetic transition")],
    )
    with pytest.raises(ModelError):
        score_path(direct, AttackPath("DirectPath", ("S", "T"), ("Direct",)), risk_model)


def test_ranking_uses_descending_risk_then_stable_path_id(risk_model):
    direct = Graph(
        [Node("S", "Synthetic start", "attacker", {}), Node("T", "Synthetic asset", "asset", {"impact": 5})],
        [Edge("HighA", "S", "T", "reaches", 4, (), "Synthetic transition"), Edge("HighB", "S", "T", "reaches", 4, (), "Synthetic transition"), Edge("Lower", "S", "T", "reaches", 2, (), "Synthetic transition")],
    )
    paths = [AttackPath("PathB", ("S", "T"), ("HighB",)), AttackPath("PathC", ("S", "T"), ("Lower",)), AttackPath("PathA", ("S", "T"), ("HighA",))]
    ranked = rank_paths(direct, paths, risk_model)
    assert isinstance(ranked, tuple)
    assert [(path.id, score.risk_score) for path, score in ranked] == [("PathA", 20), ("PathB", 20), ("PathC", 10)]
    assert rank_paths(direct, reversed(paths), risk_model) == ranked


def test_empty_path_collection_has_empty_ranking(scored_graph, risk_model):
    assert rank_paths(scored_graph, (), risk_model) == ()


def test_risk_result_is_immutable(scored_graph, valid_path, risk_model):
    result = score_path(scored_graph, valid_path, risk_model)
    with pytest.raises(FrozenInstanceError):
        result.risk_score = 99
