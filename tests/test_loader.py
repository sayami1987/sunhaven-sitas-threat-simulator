"""Independent fixtures exercise valid models and ambiguous or unsafe input."""

import copy
import json
from pathlib import Path

import pytest

from src.model_loader import (
    MAX_ATTRIBUTE_DEPTH,
    MAX_EDGES,
    MAX_INPUT_BYTES,
    MAX_NODES,
    load_controls,
    load_environment,
    load_risk_model,
    load_scenarios,
    validate_controls,
    validate_environment,
    validate_risk_model,
    validate_scenario,
)
from src.models import ModelError


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "loader-environment.json"


@pytest.fixture
def environment_data():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def env(environment_data):
    return validate_environment(environment_data)


@pytest.fixture
def scenario_data():
    return {
        "schema_version": 1,
        "id": "ScenarioTest",
        "title": "Synthetic test scenario",
        "description": "An independent loader test case.",
        "source": "Attacker",
        "target": "Asset",
        "edge_ids": ["EdgePassword", "EdgeAccess", "EdgeBypass"],
        "recommendation": "Review the modeled authentication assumptions.",
    }


@pytest.fixture
def controls_data():
    return {
        "schema_version": 1,
        "controls": [
            {
                "id": "MFA",
                "name": "Simulated MFA",
                "description": "Explicit synthetic password and bypass rules.",
                "rules": [
                    {"id": "PasswordRule", "tag": "password_only", "action": "block", "reason": "Password alone is insufficient.", "targets": ["Account"]},
                    {"id": "BypassRule", "tag": "mfa_bypass", "action": "cap", "cap": 2, "reason": "Residual modeled bypass difficulty."},
                ],
            }
        ],
    }


@pytest.fixture
def risk_data():
    return {
        "schema_version": 1,
        "likelihood_method": "minimum",
        "bands": [
            {"name": "Low", "minimum": 1, "maximum": 4},
            {"name": "Medium", "minimum": 5, "maximum": 9},
            {"name": "High", "minimum": 10, "maximum": 16},
            {"name": "Critical", "minimum": 17, "maximum": 25},
        ],
    }


def write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_SITAS_T01_valid_environment_loads_with_parallel_edges():
    environment = load_environment(FIXTURE_PATH)
    assert environment.id == "LoaderFixture"
    assert [node.id for node in environment.nodes] == ["Account", "Asset", "Attacker"]
    assert len(environment.edges) == 3
    parallel = [edge for edge in environment.edges if edge.source == "Attacker" and edge.target == "Account"]
    assert {edge.id for edge in parallel} == {"EdgePassword", "EdgeBypass"}
    assert next(node for node in environment.nodes if node.id == "Asset").attributes["impact"] == 5


@pytest.mark.parametrize("field", ["schema_version", "id", "name", "synthetic", "nodes", "edges"])
def test_SITAS_T02_missing_required_environment_field_rejected(environment_data, field):
    del environment_data[field]
    with pytest.raises(ModelError, match="missing required fields"):
        validate_environment(environment_data)


def test_SITAS_T03_malformed_json_rejected_safely(tmp_path):
    path = tmp_path / "malformed.json"
    path.write_text('{"id":', encoding="utf-8")
    with pytest.raises(ModelError, match="Malformed JSON at line 1"):
        load_environment(path)


@pytest.mark.parametrize("content", ['{"id":"a","id":"b"}', '{"outer":{"id":1,"id":2}}'])
def test_duplicate_json_keys_rejected_even_when_nested(tmp_path, content):
    path = tmp_path / "duplicate.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ModelError, match="duplicate object key"):
        load_environment(path)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_json_constants_rejected(tmp_path, constant):
    path = tmp_path / "constant.json"
    path.write_text('{"value":' + constant + '}', encoding="utf-8")
    with pytest.raises(ModelError, match="non-finite"):
        load_environment(path)


def test_file_size_limit_rejected_before_parsing(tmp_path):
    path = tmp_path / "large.json"
    path.write_bytes(b" " * (MAX_INPUT_BYTES + 1))
    with pytest.raises(ModelError, match="input limit"):
        load_environment(path)


def test_non_utf8_input_rejected(tmp_path):
    path = tmp_path / "encoding.json"
    path.write_bytes(b"\xff\xfe")
    with pytest.raises(ModelError, match="UTF-8"):
        load_environment(path)


def test_missing_input_file_has_clear_error(tmp_path):
    with pytest.raises(ModelError, match="Cannot read"):
        load_environment(tmp_path / "missing.json")


@pytest.mark.parametrize("value", [True, 0, 2, "1", 1.0])
def test_schema_version_requires_exact_supported_integer(environment_data, value):
    environment_data["schema_version"] = value
    with pytest.raises(ModelError, match="schema_version"):
        validate_environment(environment_data)


@pytest.mark.parametrize("value", [False, 1, "true", None])
def test_synthetic_marker_requires_true_boolean(environment_data, value):
    environment_data["synthetic"] = value
    with pytest.raises(ModelError, match="synthetic"):
        validate_environment(environment_data)


@pytest.mark.parametrize("level", ["environment", "node", "edge"])
def test_unknown_schema_fields_rejected(environment_data, level):
    target = environment_data if level == "environment" else environment_data[level + "s"][0]
    target["unexpected"] = "ignored?"
    with pytest.raises(ModelError, match="unsupported fields"):
        validate_environment(environment_data)


@pytest.mark.parametrize("value", ["", " ", "1startsWithDigit", "has spaces", "a/b", "A" * 81, 123])
def test_invalid_stable_ids_rejected(environment_data, value):
    environment_data["id"] = value
    with pytest.raises(ModelError, match="valid ID"):
        validate_environment(environment_data)


@pytest.mark.parametrize("collection", ["nodes", "edges"])
def test_duplicate_record_ids_rejected(environment_data, collection):
    environment_data[collection].append(copy.deepcopy(environment_data[collection][0]))
    with pytest.raises(ModelError, match="duplicate IDs"):
        validate_environment(environment_data)


@pytest.mark.parametrize("field", ["source", "target"])
def test_unknown_edge_endpoint_rejected(environment_data, field):
    environment_data["edges"][0][field] = "Unknown"
    with pytest.raises(ModelError, match="unknown node"):
        validate_environment(environment_data)


@pytest.mark.parametrize("value", [True, 0, 6, 3.5, "4", None])
def test_likelihood_requires_integer_ordinal_score(environment_data, value):
    environment_data["edges"][0]["likelihood"] = value
    with pytest.raises(ModelError, match="likelihood"):
        validate_environment(environment_data)


@pytest.mark.parametrize("value", [False, 0, 6, 4.0, "5"])
def test_asset_impact_requires_integer_ordinal_score(environment_data, value):
    environment_data["nodes"][2]["attributes"]["impact"] = value
    with pytest.raises(ModelError, match="impact"):
        validate_environment(environment_data)


def test_asset_requires_impact(environment_data):
    environment_data["nodes"][2]["attributes"] = {}
    with pytest.raises(ModelError, match="required asset impact"):
        validate_environment(environment_data)


def test_unknown_node_type_rejected(environment_data):
    environment_data["nodes"][0]["type"] = "live_tenant"
    with pytest.raises(ModelError, match="type is unsupported"):
        validate_environment(environment_data)


def test_duplicate_edge_tags_rejected(environment_data):
    environment_data["edges"][0]["tags"] = ["password_only", "password_only"]
    with pytest.raises(ModelError, match="duplicate IDs or tags"):
        validate_environment(environment_data)


@pytest.mark.parametrize("value", [None, [], "attributes", {"bad": float("inf")}, {"bad": (1, 2)}])
def test_attributes_require_finite_json_mapping(environment_data, value):
    environment_data["nodes"][0]["attributes"] = value
    with pytest.raises(ModelError, match="attributes"):
        validate_environment(environment_data)


def test_overflowing_json_exponent_rejected_in_attributes(tmp_path, environment_data):
    raw = json.dumps(environment_data).replace('"attributes": {}', '"attributes": {"value": 1e999}', 1)
    path = tmp_path / "overflow.json"
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(ModelError, match="non-finite"):
        load_environment(path)


def test_nested_attributes_are_copied_without_input_aliasing(environment_data):
    attributes = {"labels": ["fictional", {"active": True, "value": None}]}
    environment_data["nodes"][0]["attributes"] = attributes
    environment = validate_environment(environment_data)
    attributes["labels"].append("changed")
    actor = next(node for node in environment.nodes if node.id == "Attacker")
    assert len(actor.attributes["labels"]) == 2
    assert actor.attributes["labels"][0] == "fictional"
    assert dict(actor.attributes["labels"][1]) == {"active": True, "value": None}
    with pytest.raises(TypeError):
        actor.attributes["labels"] = ()
    with pytest.raises(TypeError):
        actor.attributes["labels"][1]["active"] = False


def test_excessive_attribute_nesting_rejected(environment_data):
    nested = {}
    for _ in range(MAX_ATTRIBUTE_DEPTH + 2):
        nested = {"next": nested}
    environment_data["nodes"][0]["attributes"] = nested
    with pytest.raises(ModelError, match="nesting"):
        validate_environment(environment_data)


@pytest.mark.parametrize("collection,limit", [("nodes", MAX_NODES), ("edges", MAX_EDGES)])
def test_environment_collection_limits_are_enforced(environment_data, collection, limit):
    environment_data[collection] = [environment_data[collection][0]] * (limit + 1)
    with pytest.raises(ModelError, match="items"):
        validate_environment(environment_data)


def test_empty_edge_graph_and_empty_scenario_selection_are_valid(environment_data, scenario_data):
    environment_data["edges"] = []
    scenario_data["edge_ids"] = []
    environment = validate_environment(environment_data)
    scenario = validate_scenario(scenario_data, environment)
    assert environment.edges == ()
    assert scenario.edge_ids == ()


def test_valid_scenario_preserves_meaning_and_sorts_edge_selection(env, scenario_data):
    scenario = validate_scenario(scenario_data, env)
    assert scenario.id == "ScenarioTest"
    assert scenario.source == "Attacker" and scenario.target == "Asset"
    assert scenario.edge_ids == ("EdgeAccess", "EdgeBypass", "EdgePassword")


@pytest.mark.parametrize("field,value", [("source", "Unknown"), ("target", "Unknown"), ("target", "Account"), ("source", "Asset")])
def test_invalid_scenario_endpoints_rejected(env, scenario_data, field, value):
    scenario_data[field] = value
    with pytest.raises(ModelError):
        validate_scenario(scenario_data, env)


@pytest.mark.parametrize("value", [["UnknownEdge"], ["EdgeAccess", "EdgeAccess"], "EdgeAccess"])
def test_invalid_scenario_edge_selection_rejected(env, scenario_data, value):
    scenario_data["edge_ids"] = value
    with pytest.raises(ModelError):
        validate_scenario(scenario_data, env)


@pytest.mark.parametrize("field", ["id", "title", "description", "source", "target", "edge_ids", "recommendation"])
def test_missing_scenario_fields_rejected(env, scenario_data, field):
    del scenario_data[field]
    with pytest.raises(ModelError, match="missing required fields"):
        validate_scenario(scenario_data, env)


def test_scenario_directory_returns_nonempty_tuple_sorted_by_id(tmp_path, env, scenario_data):
    scenario_data["id"] = "ScenarioZ"
    write_json(tmp_path / "a.json", scenario_data)
    scenario_data["id"] = "ScenarioA"
    write_json(tmp_path / "z.json", scenario_data)
    (tmp_path / "readme.txt").write_text("not a scenario", encoding="utf-8")
    scenarios = load_scenarios(tmp_path, env)
    assert isinstance(scenarios, tuple)
    assert [scenario.id for scenario in scenarios] == ["ScenarioA", "ScenarioZ"]


def test_duplicate_scenario_ids_across_files_rejected(tmp_path, env, scenario_data):
    write_json(tmp_path / "a.json", scenario_data)
    write_json(tmp_path / "b.json", scenario_data)
    with pytest.raises(ModelError, match="duplicate IDs"):
        load_scenarios(tmp_path, env)


def test_empty_scenario_directory_rejected(tmp_path, env):
    with pytest.raises(ModelError, match="between 1"):
        load_scenarios(tmp_path, env)


def test_missing_scenario_directory_rejected(tmp_path, env):
    with pytest.raises(ModelError, match="scenario directory"):
        load_scenarios(tmp_path / "missing", env)


def test_valid_control_file_loads_block_cap_and_target_rules(tmp_path, env, controls_data):
    controls = load_controls(write_json(tmp_path / "controls.json", controls_data), env)
    assert isinstance(controls, tuple)
    assert controls[0].id == "MFA"
    cap_rule, block_rule = controls[0].rules
    assert cap_rule.id == "BypassRule" and cap_rule.cap == 2 and cap_rule.targets == ()
    assert block_rule.action == "block" and block_rule.targets == ("Account",) and block_rule.cap is None


@pytest.mark.parametrize("field,value", [("tag", "nonexistent"), ("action", "execute"), ("targets", ["Unknown"]), ("reason", " ")])
def test_invalid_control_rule_rejected(env, controls_data, field, value):
    controls_data["controls"][0]["rules"][0][field] = value
    with pytest.raises(ModelError):
        validate_controls(controls_data, env)


@pytest.mark.parametrize("value", [True, 0, 6, 2.0, "2", None])
def test_control_caps_require_valid_ordinal_integer(env, controls_data, value):
    controls_data["controls"][0]["rules"][1]["cap"] = value
    with pytest.raises(ModelError, match="cap"):
        validate_controls(controls_data, env)


def test_cap_rule_requires_cap(env, controls_data):
    del controls_data["controls"][0]["rules"][1]["cap"]
    with pytest.raises(ModelError, match="missing required cap"):
        validate_controls(controls_data, env)


def test_block_rule_must_not_have_cap(env, controls_data):
    controls_data["controls"][0]["rules"][0]["cap"] = 1
    with pytest.raises(ModelError, match="must not define cap"):
        validate_controls(controls_data, env)


def test_control_rules_must_be_nonempty(env, controls_data):
    controls_data["controls"][0]["rules"] = []
    with pytest.raises(ModelError, match="between 1"):
        validate_controls(controls_data, env)


def test_duplicate_control_ids_rejected(env, controls_data):
    controls_data["controls"].append(copy.deepcopy(controls_data["controls"][0]))
    with pytest.raises(ModelError, match="controls contains duplicate IDs"):
        validate_controls(controls_data, env)


def test_rule_ids_are_unique_across_controls(env, controls_data):
    second = copy.deepcopy(controls_data["controls"][0])
    second["id"] = "SecondControl"
    controls_data["controls"].append(second)
    with pytest.raises(ModelError, match="control rules contains duplicate IDs"):
        validate_controls(controls_data, env)


def test_duplicate_rule_targets_rejected(env, controls_data):
    controls_data["controls"][0]["rules"][0]["targets"] = ["Account", "Account"]
    with pytest.raises(ModelError, match="duplicate IDs"):
        validate_controls(controls_data, env)


@pytest.mark.parametrize("level", ["configuration", "control", "rule"])
def test_unknown_control_fields_rejected(env, controls_data, level):
    targets = {"configuration": controls_data, "control": controls_data["controls"][0], "rule": controls_data["controls"][0]["rules"][0]}
    targets[level]["script"] = "untrusted data"
    with pytest.raises(ModelError, match="unsupported fields"):
        validate_controls(controls_data, env)


def test_empty_control_collection_is_valid_for_baseline(env):
    assert validate_controls({"schema_version": 1, "controls": []}, env) == ()


def test_valid_risk_file_loads_and_canonicalises_band_order(tmp_path, risk_data):
    risk_data["bands"].reverse()
    model = load_risk_model(write_json(tmp_path / "risk.json", risk_data))
    assert model.likelihood_method == "minimum"
    assert [(band.name, band.minimum, band.maximum) for band in model.bands] == [
        ("Low", 1, 4), ("Medium", 5, 9), ("High", 10, 16), ("Critical", 17, 25),
    ]


@pytest.mark.parametrize("method", ["product", "mean", None, True])
def test_unsupported_likelihood_method_rejected(risk_data, method):
    risk_data["likelihood_method"] = method
    with pytest.raises(ModelError, match="likelihood_method"):
        validate_risk_model(risk_data)


@pytest.mark.parametrize("mutation", ["gap", "overlap", "name", "missing", "duplicate", "boolean"])
def test_risk_bands_require_exact_documented_mapping(risk_data, mutation):
    if mutation == "gap":
        risk_data["bands"][1]["minimum"] = 6
    elif mutation == "overlap":
        risk_data["bands"][1]["minimum"] = 4
    elif mutation == "name":
        risk_data["bands"][0]["name"] = "Safe"
    elif mutation == "missing":
        risk_data["bands"].pop()
    elif mutation == "duplicate":
        risk_data["bands"][1] = copy.deepcopy(risk_data["bands"][0])
    else:
        risk_data["bands"][0]["minimum"] = True
    with pytest.raises(ModelError):
        validate_risk_model(risk_data)


@pytest.mark.parametrize("data", [None, [], "object", 1, True])
def test_top_level_requires_json_object(data):
    with pytest.raises(ModelError, match="JSON object"):
        validate_environment(data)


def test_display_text_is_preserved_as_data_without_execution(environment_data):
    name = '<script>alert("fictional")</script>'
    environment_data["name"] = name
    environment = validate_environment(environment_data)
    assert environment.name == name
