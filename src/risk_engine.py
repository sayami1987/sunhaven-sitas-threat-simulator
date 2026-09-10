"""Explainable ordinal risk scoring, not probability estimation."""
from dataclasses import dataclass
from typing import Iterable

from .graph_engine import Graph
from .models import ModelError, RiskModel
from .pathfinder import AttackPath


@dataclass(frozen=True)
class RiskScore:
    likelihood: int
    impact: int
    risk_score: int
    severity: str

    def to_dict(self) -> dict:
        return {"likelihood": self.likelihood, "impact": self.impact,
                "riskScore": self.risk_score, "severity": self.severity}


def calculate_likelihood(values: Iterable[int]) -> int:
    values = tuple(values)
    if not values or any(type(value) is not int or not 1 <= value <= 5 for value in values):
        raise ModelError("Path likelihood requires nonempty integer edge scores from 1 to 5")
    return min(values)


def classify_severity(score: int, model: RiskModel) -> str:
    if type(score) is not int or not 1 <= score <= 25:
        raise ModelError("Risk score must be an integer from 1 to 25")
    matches = [band.name for band in model.bands if band.minimum <= score <= band.maximum]
    if len(matches) != 1:
        raise ModelError("Risk model must classify the score in exactly one severity band")
    return matches[0]


def score_path(graph: Graph, path: AttackPath, model: RiskModel) -> RiskScore:
    if model.likelihood_method != "minimum":
        raise ModelError("Unsupported likelihood method")
    if not path.edge_ids or len(path.node_ids) != len(path.edge_ids) + 1:
        raise ModelError("A scored path must have ordered nodes and at least one edge")
    if len(path.node_ids) != len(set(path.node_ids)):
        raise ModelError("Only simple paths can be scored")
    values = []
    for index, edge_id in enumerate(path.edge_ids):
        edge = graph.edges.get(edge_id)
        if edge is None or (edge.source, edge.target) != path.node_ids[index:index + 2]:
            raise ModelError("Path edge does not match its ordered node steps")
        values.append(edge.likelihood)
    target = graph.nodes.get(path.node_ids[-1])
    if target is None or target.type != "asset":
        raise ModelError("Scored path must end at a protected asset")
    impact = target.attributes.get("impact")
    if type(impact) is not int or not 1 <= impact <= 5:
        raise ModelError("Target impact must be an integer from 1 to 5")
    likelihood = calculate_likelihood(values)
    score = likelihood * impact
    return RiskScore(likelihood, impact, score, classify_severity(score, model))


def rank_paths(graph: Graph, paths: Iterable[AttackPath], model: RiskModel):
    scored = [(path, score_path(graph, path, model)) for path in paths]
    return tuple(sorted(scored, key=lambda item: (-item[1].risk_score, item[0].id)))
