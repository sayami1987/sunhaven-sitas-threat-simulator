"""Deterministic control effects on an immutable synthetic graph copy."""
from dataclasses import dataclass, replace
from typing import Iterable

from .graph_engine import Graph
from .models import Control, ModelError


@dataclass(frozen=True)
class ControlEffect:
    edge_id: str
    control_id: str
    rule_id: str
    action: str
    reason: str
    before_likelihood: int
    after_likelihood: int | None

    def to_dict(self) -> dict:
        return {"edgeId": self.edge_id, "controlId": self.control_id,
                "ruleId": self.rule_id, "action": self.action,
                "reason": self.reason, "beforeLikelihood": self.before_likelihood,
                "afterLikelihood": self.after_likelihood}


@dataclass(frozen=True)
class ControlResult:
    graph: Graph
    effects: tuple[ControlEffect, ...]
    selected_ids: tuple[str, ...]


def apply_controls(graph: Graph, controls: Iterable[Control],
                   selected_ids: Iterable[str]) -> ControlResult:
    """Remove blocked edges or lower their ordinal likelihood without mutation.

    A rule matches its tag and, when specified, the edge's target node. Effects
    describe each matching rule relative to the original edge; the resulting
    graph combines all matches with block precedence and the minimum cap.
    """
    control_map = {}
    rule_ids = set()
    for control in controls:
        if control.id in control_map:
            raise ModelError("Controls contain duplicate control IDs")
        control_map[control.id] = control
        for rule in control.rules:
            if rule.id in rule_ids:
                raise ModelError("Controls contain duplicate rule IDs")
            rule_ids.add(rule.id)
            if rule.action not in ("block", "cap"):
                raise ModelError("Control rule action must be block or cap")
            if rule.action == "cap":
                if type(rule.cap) is not int or not 1 <= rule.cap <= 5:
                    raise ModelError("Control rule cap must be an integer from 1 to 5")
            elif rule.cap is not None:
                raise ModelError("Block rules must not specify a cap")

    selected = tuple(selected_ids)
    if any(not isinstance(item, str) or not item for item in selected):
        raise ModelError("Selected control IDs must be nonempty strings")
    selected = tuple(sorted(set(selected)))
    if set(selected) - control_map.keys():
        raise ModelError("Selected controls contain an unknown control ID")

    effects = []
    surviving_edges = []
    for edge in graph.edges.values():
        blocked = False
        likelihood = edge.likelihood
        for control_id in selected:
            for rule in control_map[control_id].rules:
                if rule.tag not in edge.tags:
                    continue
                if rule.targets and edge.target not in rule.targets:
                    continue
                candidate = (None if rule.action == "block"
                             else min(edge.likelihood, rule.cap))
                effects.append(ControlEffect(edge.id, control_id, rule.id,
                                             rule.action, rule.reason,
                                             edge.likelihood, candidate))
                if candidate is None:
                    blocked = True
                else:
                    likelihood = min(likelihood, candidate)
        if not blocked:
            surviving_edges.append(replace(edge, likelihood=likelihood))

    effects.sort(key=lambda effect: (effect.edge_id, effect.control_id, effect.rule_id))
    return ControlResult(Graph(graph.nodes.values(), surviving_edges),
                         tuple(effects), selected)
