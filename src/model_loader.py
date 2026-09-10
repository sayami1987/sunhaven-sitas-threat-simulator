"""Strict, bounded JSON loading for the synthetic SITAS input contracts."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from .models import (
    Control,
    Edge,
    Environment,
    ModelError,
    Node,
    RiskModel,
    Rule,
    Scenario,
    SeverityBand,
)


MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_NODES = 500
MAX_EDGES = 5_000
MAX_SCENARIOS = 1_000
MAX_CONTROLS = 100
MAX_RULES = 1_000
MAX_TAGS = 100
MAX_ATTRIBUTE_DEPTH = 32
MAX_ATTRIBUTE_ITEMS = 10_000
ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,79}$")
NODE_TYPES = frozenset(
    {
        "attacker", "actor", "identity", "credential", "session", "workstation",
        "application", "privilege", "asset", "authentication_factor",
    }
)
EXPECTED_BANDS = (
    ("Low", 1, 4),
    ("Medium", 5, 9),
    ("High", 10, 16),
    ("Critical", 17, 25),
)


def _object(
    value: Any,
    label: str,
    required: set[str],
    optional: set[str] | None = None,
) -> dict[str, Any]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise ModelError(f"{label} must be a JSON object with string keys")
    missing = required - value.keys()
    if missing:
        raise ModelError(f"{label} is missing required fields: {', '.join(sorted(missing))}")
    if value.keys() - required - (optional or set()):
        raise ModelError(f"{label} contains unsupported fields")
    return value


def _schema(value: Any, label: str, fields: set[str]) -> dict[str, Any]:
    result = _object(value, label, fields | {"schema_version"})
    if type(result["schema_version"]) is not int or result["schema_version"] != 1:
        raise ModelError(f"{label}.schema_version must be integer 1")
    return result


def _text(value: Any, label: str) -> str:
    if type(value) is not str or not value.strip():
        raise ModelError(f"{label} must be a nonempty string")
    return value


def _identifier(value: Any, label: str) -> str:
    if type(value) is not str or ID_PATTERN.fullmatch(value) is None:
        raise ModelError(f"{label} must be a valid ID of 1 to 80 letters, digits, underscores or hyphens, starting with a letter")
    return value


def _array(value: Any, label: str, maximum: int, minimum: int = 0) -> list[Any]:
    if type(value) is not list:
        raise ModelError(f"{label} must be a JSON array")
    if not minimum <= len(value) <= maximum:
        raise ModelError(f"{label} must contain between {minimum} and {maximum} items")
    return value


def _integer(value: Any, label: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ModelError(f"{label} must be an integer from {minimum} to {maximum}")
    return value


def _unique_identifiers(value: Any, label: str, maximum: int) -> tuple[str, ...]:
    result = tuple(_identifier(item, f"{label} item") for item in _array(value, label, maximum))
    if len(result) != len(set(result)):
        raise ModelError(f"{label} contains duplicate IDs or tags")
    return tuple(sorted(result))


def _attributes(value: Any, label: str) -> dict[str, Any]:
    """Copy JSON attributes while rejecting non-JSON values and excessive nesting."""
    if type(value) is not dict:
        raise ModelError(f"{label} must be a JSON object")
    visited_items = 0

    def copy_json(item: Any, depth: int) -> Any:
        nonlocal visited_items
        visited_items += 1
        if depth > MAX_ATTRIBUTE_DEPTH or visited_items > MAX_ATTRIBUTE_ITEMS:
            raise ModelError(f"{label} exceeds supported attribute size or nesting")
        if item is None or type(item) in (bool, int):
            return item
        if type(item) is float:
            if not math.isfinite(item):
                raise ModelError(f"{label} contains a non-finite number")
            return item
        if type(item) is str:
            return _text(item, label)
        if type(item) is list:
            return [copy_json(child, depth + 1) for child in item]
        if type(item) is dict:
            if any(type(key) is not str or not key.strip() for key in item):
                raise ModelError(f"{label} must use nonempty string keys")
            return {key: copy_json(child, depth + 1) for key, child in item.items()}
        raise ModelError(f"{label} contains a value that is not JSON data")

    return copy_json(value, 0)


def _unique_records(records: list[Any], label: str) -> None:
    identifiers = [record.id for record in records]
    if len(identifiers) != len(set(identifiers)):
        raise ModelError(f"{label} contains duplicate IDs")


def _read_json(path: str | Path) -> Any:
    """Read at most the input limit and reject ambiguous JSON syntax."""
    def pairs_to_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ModelError("JSON contains a duplicate object key")
            result[key] = value
        return result

    def reject_constant(_: str) -> None:
        raise ModelError("JSON contains a non-finite numeric constant")

    try:
        with Path(path).open("rb") as source:
            raw = source.read(MAX_INPUT_BYTES + 1)
    except (OSError, ValueError) as exc:
        raise ModelError("Cannot read the requested JSON file") from exc
    if len(raw) > MAX_INPUT_BYTES:
        raise ModelError(f"JSON file exceeds the {MAX_INPUT_BYTES}-byte input limit")
    try:
        return json.loads(
            raw.decode("utf-8-sig"),
            object_pairs_hook=pairs_to_object,
            parse_constant=reject_constant,
        )
    except UnicodeDecodeError as exc:
        raise ModelError("JSON file must use UTF-8 encoding") from exc
    except json.JSONDecodeError as exc:
        raise ModelError(f"Malformed JSON at line {exc.lineno}, column {exc.colno}") from exc
    except (RecursionError, OverflowError) as exc:
        raise ModelError("JSON exceeds supported nesting or numeric limits") from exc
    except ValueError as exc:
        if isinstance(exc, ModelError):
            raise
        raise ModelError("JSON contains an unsupported numeric value") from exc


def validate_environment(data: Any) -> Environment:
    """Validate a synthetic environment and return canonically ordered records."""
    data = _schema(data, "environment", {"id", "name", "synthetic", "nodes", "edges"})
    environment_id = _identifier(data["id"], "environment.id")
    name = _text(data["name"], "environment.name")
    if data["synthetic"] is not True:
        raise ModelError("environment.synthetic must be true")

    nodes: list[Node] = []
    for index, item in enumerate(_array(data["nodes"], "environment.nodes", MAX_NODES, 1)):
        label = f"environment.nodes[{index}]"
        item = _object(item, label, {"id", "name", "type", "attributes"})
        node_id = _identifier(item["id"], f"{label}.id")
        node_name = _text(item["name"], f"{label}.name")
        node_type = _text(item["type"], f"{label}.type")
        if node_type not in NODE_TYPES:
            raise ModelError(f"{label}.type is unsupported")
        attributes = _attributes(item["attributes"], f"{label}.attributes")
        if node_type == "asset":
            if "impact" not in attributes:
                raise ModelError(f"{label}.attributes is missing required asset impact")
            _integer(attributes["impact"], f"{label}.attributes.impact", 1, 5)
        nodes.append(Node(node_id, node_name, node_type, attributes))
    _unique_records(nodes, "environment.nodes")
    node_ids = {node.id for node in nodes}

    edges: list[Edge] = []
    for index, item in enumerate(_array(data["edges"], "environment.edges", MAX_EDGES)):
        label = f"environment.edges[{index}]"
        item = _object(item, label, {"id", "source", "target", "relationship", "likelihood", "tags", "explanation"})
        edge_id = _identifier(item["id"], f"{label}.id")
        source = _identifier(item["source"], f"{label}.source")
        target = _identifier(item["target"], f"{label}.target")
        if source not in node_ids or target not in node_ids:
            raise ModelError(f"{label} references an unknown node")
        relationship = _text(item["relationship"], f"{label}.relationship")
        likelihood = _integer(item["likelihood"], f"{label}.likelihood", 1, 5)
        tags = _unique_identifiers(item["tags"], f"{label}.tags", MAX_TAGS)
        explanation = _text(item["explanation"], f"{label}.explanation")
        edges.append(Edge(edge_id, source, target, relationship, likelihood, tags, explanation))
    _unique_records(edges, "environment.edges")
    return Environment(environment_id, name, tuple(sorted(nodes, key=lambda node: node.id)), tuple(sorted(edges, key=lambda edge: edge.id)))


def load_environment(path: str | Path) -> Environment:
    return validate_environment(_read_json(path))


def validate_scenario(data: Any, env: Environment) -> Scenario:
    """Resolve scenario references without inventing or modifying graph edges."""
    data = _schema(data, "scenario", {"id", "title", "description", "source", "target", "edge_ids", "recommendation"})
    scenario_id = _identifier(data["id"], "scenario.id")
    title = _text(data["title"], "scenario.title")
    description = _text(data["description"], "scenario.description")
    source = _identifier(data["source"], "scenario.source")
    target = _identifier(data["target"], "scenario.target")
    nodes = {node.id: node for node in env.nodes}
    if source not in nodes or target not in nodes:
        raise ModelError("scenario references an unknown source or target node")
    if source == target:
        raise ModelError("scenario source and target must be distinct")
    if nodes[target].type != "asset":
        raise ModelError("scenario target must be a protected asset")
    edge_ids = _unique_identifiers(data["edge_ids"], "scenario.edge_ids", MAX_EDGES)
    if set(edge_ids) - {edge.id for edge in env.edges}:
        raise ModelError("scenario.edge_ids references an unknown edge")
    recommendation = _text(data["recommendation"], "scenario.recommendation")
    return Scenario(scenario_id, title, description, source, target, edge_ids, recommendation)


def load_scenarios(directory: str | Path, env: Environment) -> tuple[Scenario, ...]:
    """Load a nonempty collection of JSON scenario files in stable ID order."""
    try:
        paths = sorted(path for path in Path(directory).iterdir() if path.is_file() and path.suffix.lower() == ".json")
    except (OSError, ValueError) as exc:
        raise ModelError("Cannot read the requested scenario directory") from exc
    if not 1 <= len(paths) <= MAX_SCENARIOS:
        raise ModelError(f"Scenario directory must contain between 1 and {MAX_SCENARIOS} JSON files")
    scenarios = [validate_scenario(_read_json(path), env) for path in paths]
    _unique_records(scenarios, "scenarios")
    return tuple(sorted(scenarios, key=lambda scenario: scenario.id))


def validate_controls(data: Any, env: Environment) -> tuple[Control, ...]:
    """Validate explicit tag/target rules; block and cap are the only actions."""
    data = _schema(data, "controls configuration", {"controls"})
    node_ids = {node.id for node in env.nodes}
    known_tags = {tag for edge in env.edges for tag in edge.tags}
    controls: list[Control] = []
    all_rules: list[Rule] = []
    for index, item in enumerate(_array(data["controls"], "controls", MAX_CONTROLS)):
        label = f"controls[{index}]"
        item = _object(item, label, {"id", "name", "description", "rules"})
        control_id = _identifier(item["id"], f"{label}.id")
        name = _text(item["name"], f"{label}.name")
        description = _text(item["description"], f"{label}.description")
        rules: list[Rule] = []
        for rule_index, raw_rule in enumerate(_array(item["rules"], f"{label}.rules", MAX_RULES, 1)):
            rule_label = f"{label}.rules[{rule_index}]"
            raw_rule = _object(raw_rule, rule_label, {"id", "tag", "action", "reason"}, {"targets", "cap"})
            rule_id = _identifier(raw_rule["id"], f"{rule_label}.id")
            tag = _identifier(raw_rule["tag"], f"{rule_label}.tag")
            if tag not in known_tags:
                raise ModelError(f"{rule_label}.tag does not appear on any environment edge")
            action = _text(raw_rule["action"], f"{rule_label}.action")
            if action not in {"block", "cap"}:
                raise ModelError(f"{rule_label}.action must be block or cap")
            reason = _text(raw_rule["reason"], f"{rule_label}.reason")
            targets = _unique_identifiers(raw_rule.get("targets", []), f"{rule_label}.targets", MAX_NODES)
            if set(targets) - node_ids:
                raise ModelError(f"{rule_label}.targets references an unknown node")
            if action == "cap":
                if "cap" not in raw_rule:
                    raise ModelError(f"{rule_label} is missing required cap")
                cap = _integer(raw_rule["cap"], f"{rule_label}.cap", 1, 5)
            else:
                if "cap" in raw_rule:
                    raise ModelError(f"{rule_label} block action must not define cap")
                cap = None
            rules.append(Rule(rule_id, tag, action, reason, targets, cap))
        all_rules.extend(rules)
        if len(all_rules) > MAX_RULES:
            raise ModelError(f"Controls configuration exceeds {MAX_RULES} total rules")
        controls.append(Control(control_id, name, description, tuple(sorted(rules, key=lambda rule: rule.id))))
    _unique_records(controls, "controls")
    _unique_records(all_rules, "control rules")
    return tuple(sorted(controls, key=lambda control: control.id))


def load_controls(path: str | Path, env: Environment) -> tuple[Control, ...]:
    return validate_controls(_read_json(path), env)


def validate_risk_model(data: Any) -> RiskModel:
    """Require the documented ordinal model and complete severity mapping."""
    data = _schema(data, "risk model", {"likelihood_method", "bands"})
    if data["likelihood_method"] != "minimum":
        raise ModelError("risk model.likelihood_method must be minimum")
    bands: list[SeverityBand] = []
    for index, item in enumerate(_array(data["bands"], "risk model.bands", 4, 4)):
        label = f"risk model.bands[{index}]"
        item = _object(item, label, {"name", "minimum", "maximum"})
        name = _text(item["name"], f"{label}.name")
        minimum = _integer(item["minimum"], f"{label}.minimum", 1, 25)
        maximum = _integer(item["maximum"], f"{label}.maximum", 1, 25)
        bands.append(SeverityBand(name, minimum, maximum))
    bands.sort(key=lambda band: band.minimum)
    if tuple((band.name, band.minimum, band.maximum) for band in bands) != EXPECTED_BANDS:
        raise ModelError("risk model bands must be Low 1-4, Medium 5-9, High 10-16, Critical 17-25")
    return RiskModel("minimum", tuple(bands))


def load_risk_model(path: str | Path) -> RiskModel:
    return validate_risk_model(_read_json(path))
