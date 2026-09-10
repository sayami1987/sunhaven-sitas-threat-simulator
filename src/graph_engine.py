"""Directed multigraph construction and structural inspection."""
from collections import Counter, deque
from types import MappingProxyType
from typing import Iterable

from .models import Edge, Environment, ModelError, Node, Scenario


class Graph:
    """Immutable indexes preserve parallel edges and deterministic adjacency."""

    def __init__(self, nodes: Iterable[Node], edges: Iterable[Edge]):
        nodes = tuple(nodes)
        edges = tuple(edges)
        node_map = {node.id: node for node in nodes}
        edge_map = {edge.id: edge for edge in edges}
        if len(node_map) != len(nodes) or len(edge_map) != len(edges):
            raise ModelError("Graph contains duplicate node or edge IDs")
        adjacency = {node_id: [] for node_id in sorted(node_map)}
        for edge in sorted(edges, key=lambda item: item.id):
            if edge.source not in node_map or edge.target not in node_map:
                raise ModelError("Graph edge references an unknown node")
            if type(edge.likelihood) is not int or not 1 <= edge.likelihood <= 5:
                raise ModelError("Graph edge likelihood must be an integer from 1 to 5")
            adjacency[edge.source].append(edge)
        self.nodes = MappingProxyType(dict(sorted(node_map.items())))
        self.edges = MappingProxyType(dict(sorted(edge_map.items())))
        self.adjacency = MappingProxyType({key: tuple(value) for key, value in adjacency.items()})

    def outgoing(self, node_id: str) -> tuple[Edge, ...]:
        if node_id not in self.nodes:
            raise ModelError("Unknown graph node")
        return self.adjacency[node_id]

    def has_cycle(self) -> bool:
        """Kahn's topological elimination detects cycles without recursion."""
        indegree = {node_id: 0 for node_id in self.nodes}
        for edge in self.edges.values():
            indegree[edge.target] += 1
        queue = deque(node_id for node_id, degree in indegree.items() if degree == 0)
        processed = 0
        while queue:
            node_id = queue.popleft()
            processed += 1
            for edge in self.outgoing(node_id):
                indegree[edge.target] -= 1
                if indegree[edge.target] == 0:
                    queue.append(edge.target)
        return processed != len(self.nodes)

    def summary(self) -> dict:
        pairs = Counter((edge.source, edge.target) for edge in self.edges.values())
        incident = {value for pair in pairs for value in pair}
        return {"nodeCount": len(self.nodes), "edgeCount": len(self.edges),
                "isolatedNodeCount": len(set(self.nodes) - incident),
                "parallelEdgePairs": sum(count > 1 for count in pairs.values()),
                "hasCycle": self.has_cycle()}


def build_graph(env: Environment, scenario: Scenario | None = None) -> Graph:
    if scenario is None:
        return Graph(env.nodes, env.edges)
    nodes = {node.id: node for node in env.nodes}
    edges = {edge.id: edge for edge in env.edges}
    if scenario.source not in nodes or scenario.target not in nodes:
        raise ModelError("Scenario references an unknown source or target")
    if scenario.source == scenario.target or nodes[scenario.target].type != "asset":
        raise ModelError("Scenario requires a distinct protected asset target")
    if len(scenario.edge_ids) != len(set(scenario.edge_ids)):
        raise ModelError("Scenario contains duplicate edge selections")
    if set(scenario.edge_ids) - edges.keys():
        raise ModelError("Scenario references an unknown edge")
    return Graph(env.nodes, (edges[edge_id] for edge_id in scenario.edge_ids))
