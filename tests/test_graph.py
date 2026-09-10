"""Small explicit graphs verify directed multigraph construction and safety."""

import pytest

from src.graph_engine import Graph, build_graph
from src.models import Edge, Environment, ModelError, Node, Scenario


def node(identifier, kind="identity"):
    return Node(identifier, f"Fictional {identifier}", kind, {"impact": 4} if kind == "asset" else {})


def edge(identifier, source, target, likelihood=3):
    return Edge(identifier, source, target, "reaches", likelihood, (), f"Synthetic {identifier} transition")


@pytest.fixture
def environment():
    return Environment(
        "GraphFixture", "Synthetic graph fixture",
        (node("Attacker", "attacker"), node("Account"), node("Asset", "asset"), node("Isolated")),
        (
            edge("Password", "Attacker", "Account"),
            edge("Bypass", "Attacker", "Account", 2),
            edge("Access", "Account", "Asset", 5),
        ),
    )


def scenario(edge_ids, source="Attacker", target="Asset"):
    return Scenario("GraphScenario", "Synthetic scenario", "Select explicit transitions.", source, target, tuple(edge_ids), "Review modeled exposure.")


def test_SITAS_T04_graph_nodes_created_correctly(environment):
    graph = Graph(iter(environment.nodes), iter(environment.edges))
    assert set(graph.nodes) == {"Attacker", "Account", "Asset", "Isolated"}
    assert graph.nodes["Asset"].type == "asset"
    assert graph.nodes["Asset"].attributes["impact"] == 4


def test_SITAS_T05_graph_edges_created_with_relationship_and_likelihood(environment):
    graph = Graph(environment.nodes, environment.edges)
    assert set(graph.edges) == {"Password", "Bypass", "Access"}
    assert graph.edges["Bypass"].source == "Attacker"
    assert graph.edges["Bypass"].target == "Account"
    assert graph.edges["Bypass"].relationship == "reaches"
    assert graph.edges["Bypass"].likelihood == 2


def test_edges_are_directed_without_implicit_reverse_relationship(environment):
    graph = build_graph(environment)
    assert [item.target for item in graph.outgoing("Account")] == ["Asset"]
    assert graph.outgoing("Asset") == ()
    assert all(item.target != "Attacker" for item in graph.outgoing("Account"))


def test_parallel_edges_remain_distinct_and_ordered(environment):
    graph = build_graph(environment)
    assert tuple(item.id for item in graph.outgoing("Attacker")) == ("Bypass", "Password")
    assert graph.outgoing("Attacker")[0].target == graph.outgoing("Attacker")[1].target == "Account"
    assert graph.summary()["parallelEdgePairs"] == 1


def test_adjacency_order_is_stable_when_input_order_changes(environment):
    first = Graph(environment.nodes, environment.edges)
    second = Graph(reversed(environment.nodes), reversed(environment.edges))
    assert dict(first.adjacency) == dict(second.adjacency)
    assert first.summary() == second.summary()


def test_graph_id_maps_and_adjacency_are_immutable(environment):
    graph = build_graph(environment)
    with pytest.raises(TypeError):
        graph.nodes["Other"] = node("Other")
    with pytest.raises(TypeError):
        graph.edges["Other"] = edge("Other", "Attacker", "Asset")
    with pytest.raises(TypeError):
        graph.adjacency["Attacker"] = ()
    assert isinstance(graph.adjacency["Attacker"], tuple)


def test_disconnected_node_is_retained_with_empty_outgoing_edges(environment):
    graph = build_graph(environment)
    assert graph.outgoing("Isolated") == ()
    assert graph.summary() == {
        "nodeCount": 4, "edgeCount": 3, "isolatedNodeCount": 1,
        "parallelEdgePairs": 1, "hasCycle": False,
    }


def test_dag_with_shared_destination_and_parallel_edges_has_no_cycle(environment):
    graph = Graph(environment.nodes, (*environment.edges, edge("Direct", "Attacker", "Asset")))
    assert graph.has_cycle() is False


def test_self_loop_is_reported_as_a_cycle():
    graph = Graph([node("A")], [edge("Loop", "A", "A")])
    assert graph.has_cycle() is True
    assert graph.summary()["hasCycle"] is True


def test_multi_node_cycle_is_detected_even_in_disconnected_component():
    graph = Graph(
        [node("Start"), node("End"), node("A"), node("B"), node("C")],
        [edge("Main", "Start", "End"), edge("AB", "A", "B"), edge("BC", "B", "C"), edge("CA", "C", "A")],
    )
    assert graph.has_cycle() is True


def test_cycle_detection_handles_long_chain_without_recursion():
    nodes = [node(f"N{index}") for index in range(1200)]
    edges = [edge(f"E{index}", f"N{index}", f"N{index + 1}") for index in range(1199)]
    assert Graph(nodes, edges).has_cycle() is False
    assert Graph(nodes, [*edges, edge("Back", "N1199", "N0")]).has_cycle() is True


def test_unknown_outgoing_node_raises_model_error(environment):
    with pytest.raises(ModelError):
        build_graph(environment).outgoing("Unknown")


def test_duplicate_node_ids_rejected(environment):
    with pytest.raises(ModelError):
        Graph((*environment.nodes, node("Account")), environment.edges)


def test_duplicate_edge_ids_rejected(environment):
    with pytest.raises(ModelError):
        Graph(environment.nodes, (*environment.edges, edge("Access", "Attacker", "Asset")))


@pytest.mark.parametrize("source,target", [("Unknown", "Asset"), ("Attacker", "Unknown")])
def test_dangling_edge_references_rejected(environment, source, target):
    with pytest.raises(ModelError):
        Graph(environment.nodes, [edge("Dangling", source, target)])


@pytest.mark.parametrize("likelihood", [True, 0, 6])
def test_invalid_edge_likelihood_rejected_at_graph_constructor(environment, likelihood):
    with pytest.raises(ModelError):
        Graph(environment.nodes, [edge("InvalidScore", "Attacker", "Asset", likelihood)])


def test_scenario_selection_retains_nodes_and_only_selected_edges(environment):
    graph = build_graph(environment, scenario(["Password", "Access"]))
    assert set(graph.nodes) == {item.id for item in environment.nodes}
    assert set(graph.edges) == {"Password", "Access"}
    assert tuple(item.id for item in graph.outgoing("Attacker")) == ("Password",)


def test_empty_scenario_selection_produces_graph_with_isolated_nodes(environment):
    graph = build_graph(environment, scenario([]))
    assert len(graph.nodes) == 4
    assert len(graph.edges) == 0
    assert graph.summary()["isolatedNodeCount"] == 4
    assert graph.has_cycle() is False


def test_build_graph_rejects_unknown_selected_edge(environment):
    with pytest.raises(ModelError):
        build_graph(environment, scenario(["UnknownEdge"]))


@pytest.mark.parametrize("source,target", [("Unknown", "Asset"), ("Attacker", "Unknown"), ("Asset", "Asset"), ("Attacker", "Account")])
def test_build_graph_revalidates_direct_scenario_endpoints(environment, source, target):
    with pytest.raises(ModelError):
        build_graph(environment, scenario(["Access"], source, target))


def test_build_graph_rejects_duplicate_direct_scenario_edge_selection(environment):
    with pytest.raises(ModelError):
        build_graph(environment, scenario(["Access", "Access"]))
