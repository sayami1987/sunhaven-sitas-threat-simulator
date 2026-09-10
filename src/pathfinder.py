"""Bounded iterative depth-first enumeration of simple directed attack paths."""
from dataclasses import dataclass
import hashlib
import json

from .graph_engine import Graph
from .models import ModelError


class SearchLimitError(ModelError):
    """A work or path budget was exhausted; partial results must not be reported."""


@dataclass(frozen=True)
class AttackPath:
    id: str
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]


@dataclass(frozen=True)
class SearchResult:
    paths: tuple[AttackPath, ...]
    expansions: int
    depth_pruned: int


def path_id(edge_ids: tuple[str, ...]) -> str:
    canonical = json.dumps(edge_ids, separators=(",", ":"), ensure_ascii=True)
    return "SITAS-AP-" + hashlib.sha256(canonical.encode()).hexdigest()[:16]


def find_paths(graph: Graph, source: str, target: str, *, max_depth: int = 12,
               max_paths: int = 10_000, max_expansions: int = 100_000) -> SearchResult:
    """Return all simple paths within depth, or fail on resource exhaustion.

    A stack of adjacency iterators keeps only the current route. Backtracking
    removes nodes from the visited set, allowing alternative routes through a
    previously explored node. Work counts every examined outgoing edge.
    """
    if source not in graph.nodes or target not in graph.nodes or source == target:
        raise ModelError("Path search needs known, distinct source and target nodes")
    for label, value, ceiling in (("max_depth", max_depth, 500),
                                  ("max_paths", max_paths, 100_000),
                                  ("max_expansions", max_expansions, 1_000_000)):
        if type(value) is not int or not 1 <= value <= ceiling:
            raise ModelError(f"{label} must be an integer from 1 to {ceiling}")
    node_ids = [source]
    edge_ids = []
    visited = {source}
    stack = [iter(graph.outgoing(source))]
    paths = []
    expansions = depth_pruned = 0
    while stack:
        edge = next(stack[-1], None)
        if edge is None:
            stack.pop()
            visited.remove(node_ids.pop())
            if edge_ids:
                edge_ids.pop()
            continue
        expansions += 1
        if expansions > max_expansions:
            raise SearchLimitError("Search expansion limit exceeded; no complete analysis was produced")
        if edge.target in visited:
            continue
        if len(edge_ids) + 1 > max_depth:
            depth_pruned += 1
            continue
        if edge.target == target:
            path_edges = tuple(edge_ids) + (edge.id,)
            paths.append(AttackPath(path_id(path_edges), tuple(node_ids) + (target,), path_edges))
            if len(paths) > max_paths:
                raise SearchLimitError("Search path limit exceeded; no complete analysis was produced")
        else:
            node_ids.append(edge.target)
            edge_ids.append(edge.id)
            visited.add(edge.target)
            stack.append(iter(graph.outgoing(edge.target)))
    return SearchResult(tuple(sorted(paths, key=lambda path: path.edge_ids)), expansions, depth_pruned)
