"""Shared immutable records for validated model inputs."""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


def freeze_json(value):
    """Make validated nested attributes immutable without retaining input aliases."""
    if isinstance(value, dict):
        return MappingProxyType({key: freeze_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(freeze_json(item) for item in value)
    return value


class ModelError(ValueError):
    """Input cannot be analysed safely or unambiguously."""


@dataclass(frozen=True)
class Node:
    id: str
    name: str
    type: str
    attributes: Mapping[str, Any]

    def __post_init__(self):
        object.__setattr__(self, "attributes", freeze_json(dict(self.attributes)))


@dataclass(frozen=True)
class Edge:
    id: str
    source: str
    target: str
    relationship: str
    likelihood: int
    tags: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class Environment:
    id: str
    name: str
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    description: str
    source: str
    target: str
    edge_ids: tuple[str, ...]
    recommendation: str


@dataclass(frozen=True)
class Rule:
    id: str
    tag: str
    action: str
    reason: str
    targets: tuple[str, ...] = ()
    cap: int | None = None


@dataclass(frozen=True)
class Control:
    id: str
    name: str
    description: str
    rules: tuple[Rule, ...]


@dataclass(frozen=True)
class SeverityBand:
    name: str
    minimum: int
    maximum: int


@dataclass(frozen=True)
class RiskModel:
    likelihood_method: str
    bands: tuple[SeverityBand, ...]
