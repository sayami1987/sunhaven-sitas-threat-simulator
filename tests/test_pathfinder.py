"""Hand-enumerated paths verify DFS completeness within declared bounds."""

from collections import deque
from dataclasses import FrozenInstanceError
import random
import re

import pytest

from src.graph_engine import Graph
from src.models import Edge, ModelError, Node
from src.pathfinder import SearchLimitError, find_paths


def graph(node_ids, transitions):
    nodes = [Node(identifier, f"Synthetic {identifier}", "identity", {}) for identifier in node_ids]
    edges = [Edge(identifier, source, target, "reaches", 3, (), "Synthetic transition") for identifier, source, target in transitions]
    return Graph(nodes, edges)


@pytest.fixture
def chain():
    return graph(["S", "A", "T"], [("First", "S", "A"), ("Second", "A", "T")])


@pytest.fixture
def diamond():
    return graph(
        ["S", "A", "B", "Join", "T"],
        [("SA", "S", "A"), ("SB", "S", "B"), ("AJ", "A", "Join"), ("BJ", "B", "Join"), ("JT", "Join", "T")],
    )


def test_SITAS_T06_basic_attack_path_has_expected_ordered_steps(chain):
    result = find_paths(chain, "S", "T")
    assert len(result.paths) == 1
    assert result.paths[0].node_ids == ("S", "A", "T")
    assert result.paths[0].edge_ids == ("First", "Second")
    assert result.expansions == 2
    assert result.depth_pruned == 0


def test_SITAS_T07_multiple_paths_share_nodes_without_suppression(diamond):
    result = find_paths(diamond, "S", "T")
    assert [path.edge_ids for path in result.paths] == [("SA", "AJ", "JT"), ("SB", "BJ", "JT")]
    assert [path.node_ids for path in result.paths] == [("S", "A", "Join", "T"), ("S", "B", "Join", "T")]
    assert result.expansions == 6


def test_SITAS_T08_valid_unreachable_target_returns_zero_paths():
    disconnected = graph(["S", "A", "T"], [("SA", "S", "A")])
    result = find_paths(disconnected, "S", "T")
    assert result.paths == ()
    assert result.expansions == 1
    assert result.depth_pruned == 0


def test_SITAS_T09_cycles_and_self_loops_do_not_repeat_nodes():
    cyclic = graph(
        ["S", "A", "T"],
        [("SA", "S", "A"), ("AS", "A", "S"), ("AA", "A", "A"), ("AT", "A", "T")],
    )
    result = find_paths(cyclic, "S", "T")
    assert [path.edge_ids for path in result.paths] == [("SA", "AT")]
    assert result.paths[0].node_ids == ("S", "A", "T")
    assert result.expansions == 4
    assert result.depth_pruned == 0


def test_SITAS_T10_maximum_depth_counts_edges_and_preserves_exact_limit(chain):
    exact = find_paths(chain, "S", "T", max_depth=2)
    bounded = find_paths(chain, "S", "T", max_depth=1)
    assert [path.edge_ids for path in exact.paths] == [("First", "Second")]
    assert exact.depth_pruned == 0
    assert bounded.paths == ()
    assert bounded.depth_pruned == 1
    assert bounded.expansions == 2


def test_depth_pruning_retains_shorter_alternative_path():
    routes = graph(
        ["S", "A", "B", "T"],
        [("Direct", "S", "T"), ("SA", "S", "A"), ("AB", "A", "B"), ("BT", "B", "T")],
    )
    result = find_paths(routes, "S", "T", max_depth=2)
    assert [path.edge_ids for path in result.paths] == [("Direct",)]
    assert result.depth_pruned == 1


def test_parallel_edges_produce_distinct_paths_even_with_same_nodes():
    parallel = graph(["S", "T"], [("Password", "S", "T"), ("Bypass", "S", "T")])
    result = find_paths(parallel, "S", "T")
    assert [path.edge_ids for path in result.paths] == [("Bypass",), ("Password",)]
    assert {path.node_ids for path in result.paths} == {("S", "T")}
    assert len({path.id for path in result.paths}) == 2


def test_ids_are_stable_when_input_order_changes(diamond):
    reversed_graph = Graph(reversed(tuple(diamond.nodes.values())), reversed(tuple(diamond.edges.values())))
    baseline = find_paths(diamond, "S", "T")
    repeated = find_paths(reversed_graph, "S", "T")
    assert baseline == repeated
    assert all(re.fullmatch(r"SITAS-AP-[0-9a-f]{16}", path.id) for path in baseline.paths)


def test_path_identity_survives_unrelated_branch_addition(chain):
    extended = Graph(
        [*chain.nodes.values(), Node("Other", "Synthetic unrelated node", "identity", {})],
        [*chain.edges.values(), Edge("AUnrelated", "S", "Other", "reaches", 2, (), "A dead-end branch")],
    )
    baseline = find_paths(chain, "S", "T")
    changed = find_paths(extended, "S", "T")
    assert changed.paths == baseline.paths
    assert changed.expansions == baseline.expansions + 1


def test_backtracking_restores_visited_nodes_for_cross_connected_routes():
    cross = graph(
        ["S", "A", "B", "T"],
        [("SA", "S", "A"), ("SB", "S", "B"), ("AB", "A", "B"), ("BA", "B", "A"), ("AT", "A", "T"), ("BT", "B", "T")],
    )
    result = find_paths(cross, "S", "T")
    assert {path.edge_ids for path in result.paths} == {
        ("SA", "AT"), ("SA", "AB", "BT"), ("SB", "BT"), ("SB", "BA", "AT"),
    }
    assert len(result.paths) == 4
    assert all(len(set(path.node_ids)) == len(path.node_ids) for path in result.paths)


def test_target_is_terminal_even_if_it_has_outgoing_edges():
    target_cycle = graph(["S", "T", "B"], [("ST", "S", "T"), ("TB", "T", "B"), ("BT", "B", "T")])
    result = find_paths(target_cycle, "S", "T")
    assert [path.edge_ids for path in result.paths] == [("ST",)]
    assert result.expansions == 1


def test_path_count_limit_allows_exact_number_and_rejects_extra_path(chain, diamond):
    assert len(find_paths(chain, "S", "T", max_paths=1).paths) == 1
    assert len(find_paths(diamond, "S", "T", max_paths=2).paths) == 2
    with pytest.raises(SearchLimitError):
        find_paths(diamond, "S", "T", max_paths=1)


def test_expansion_limit_allows_exact_work_and_rejects_next_edge(chain):
    result = find_paths(chain, "S", "T", max_expansions=2)
    assert result.expansions == 2
    with pytest.raises(SearchLimitError):
        find_paths(chain, "S", "T", max_expansions=1)


def test_cycle_edges_consume_expansion_budget():
    cyclic = graph(["S", "A", "T"], [("SA", "S", "A"), ("ALoop", "A", "A"), ("AT", "A", "T")])
    assert find_paths(cyclic, "S", "T", max_expansions=3).expansions == 3
    with pytest.raises(SearchLimitError):
        find_paths(cyclic, "S", "T", max_expansions=2)


def test_pruned_edges_consume_expansion_budget(chain):
    bounded = find_paths(chain, "S", "T", max_depth=1, max_expansions=2)
    assert bounded.paths == () and bounded.depth_pruned == 1
    with pytest.raises(SearchLimitError):
        find_paths(chain, "S", "T", max_depth=1, max_expansions=1)


def test_resource_failure_is_model_error_and_does_not_return_partial_result(diamond):
    returned = None
    with pytest.raises(ModelError) as failure:
        returned = find_paths(diamond, "S", "T", max_paths=1)
    assert isinstance(failure.value, SearchLimitError)
    assert returned is None


@pytest.mark.parametrize("source,target", [("Unknown", "T"), ("S", "Unknown"), ("S", "S")])
def test_unknown_or_equal_endpoints_rejected(chain, source, target):
    with pytest.raises(ModelError):
        find_paths(chain, source, target)


@pytest.mark.parametrize("options", [{"max_depth": True}, {"max_depth": 0}, {"max_depth": 501}, {"max_paths": 0}, {"max_paths": 100001}, {"max_expansions": 1.5}, {"max_expansions": 1000001}])
def test_invalid_search_bounds_are_rejected(chain, options):
    with pytest.raises(ModelError):
        find_paths(chain, "S", "T", **options)


def test_search_records_are_immutable(chain):
    result = find_paths(chain, "S", "T")
    assert isinstance(result.paths, tuple)
    with pytest.raises(FrozenInstanceError):
        result.expansions = 99
    with pytest.raises(FrozenInstanceError):
        result.paths[0].id = "Changed"


def test_maximum_supported_depth_handles_long_chain():
    long_chain = graph(
        [f"N{index}" for index in range(501)],
        [(f"E{index}", f"N{index}", f"N{index + 1}") for index in range(500)],
    )
    result = find_paths(long_chain, "N0", "N500", max_depth=500)
    assert len(result.paths) == 1
    assert len(result.paths[0].edge_ids) == 500
    assert result.paths[0].node_ids == tuple(f"N{index}" for index in range(501))
    assert result.depth_pruned == 0


def test_dfs_matches_independent_breadth_first_oracle_on_seeded_tiny_graphs():
    randomizer = random.Random(2026)
    identifiers = ["S", "A", "B", "C", "T"]
    for _ in range(8):
        transitions = []
        for source in identifiers:
            for target in identifiers:
                if randomizer.random() < 0.3:
                    transitions.append((f"E{len(transitions)}", source, target))
                    if randomizer.random() < 0.2:
                        transitions.append((f"E{len(transitions)}", source, target))
        tiny = graph(identifiers, transitions)
        # A queue of copied path states supplies an oracle independent of DFS backtracking.
        queue = deque([(("S",), ())])
        expected = set()
        while queue:
            nodes, edges = queue.popleft()
            if nodes[-1] == "T":
                expected.add(edges)
                continue
            for edge_id, source, target in transitions:
                if source == nodes[-1] and target not in nodes:
                    queue.append(((*nodes, target), (*edges, edge_id)))
        actual = find_paths(tiny, "S", "T", max_depth=4)
        assert {path.edge_ids for path in actual.paths} == expected
        assert len(actual.paths) == len(expected)
