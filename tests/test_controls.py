"""Explicit synthetic edge conditions verify each control and composition."""

from dataclasses import FrozenInstanceError

import pytest

from src.control_engine import apply_controls
from src.graph_engine import Graph
from src.models import Control, Edge, ModelError, Node, Rule


def control(identifier, *rules):
    return Control(identifier, f"Simulated {identifier}", "Synthetic control for an explicit condition.", tuple(rules))


def rule(identifier, tag, action="block", cap=None, targets=()):
    return Rule(identifier, tag, action, f"Synthetic reason for {identifier}.", tuple(targets), cap)


@pytest.fixture
def graph():
    nodes = [Node(identifier, f"Synthetic {identifier}", "identity", {}) for identifier in ("S", "Account", "Former", "Session", "Admin", "Asset")]
    definitions = [
        ("Password", "S", "Account", "password_only"),
        ("Bypass", "S", "Account", "mfa_bypass"),
        ("Token", "S", "Session", "stolen_session"),
        ("Stale", "S", "Session", "stale_session"),
        ("Fresh", "S", "Session", "fresh_session"),
        ("Privilege", "Account", "Asset", "excessive_privilege"),
        ("FormerAuthentication", "S", "Former", "account_authentication"),
        ("ActiveAuthentication", "S", "Account", "account_authentication"),
        ("AdminAccess", "Admin", "Asset", "admin_privilege"),
        ("Reauth", "Admin", "Asset", "privileged_operation"),
        ("SharedAccount", "S", "Account", "shared_account"),
        ("SharedDevice", "S", "Session", "shared_device_session"),
    ]
    return Graph(nodes, [Edge(identifier, source, target, "reaches", 4, (tag,), f"Synthetic {tag} condition.") for identifier, source, target, tag in definitions])


@pytest.fixture
def controls():
    return (
        control("MFA", rule("PasswordBlock", "password_only"), rule("BypassCap", "mfa_bypass", "cap", 2)),
        control("RBAC", rule("PrivilegeBlock", "excessive_privilege")),
        control("Disablement", rule("FormerBlock", "account_authentication", targets=("Former",))),
        control("Timeout", rule("StaleBlock", "stale_session")),
        control("Revocation", rule("TokenBlock", "stolen_session")),
        control("IndividualAccounts", rule("SharedAccountBlock", "shared_account")),
        control("Reauthentication", rule("PrivilegedCap", "privileged_operation", "cap", 2)),
        control("AdminRestriction", rule("AdminBlock", "admin_privilege")),
        control("DeviceSeparation", rule("SharedDeviceBlock", "shared_device_session")),
    )


def test_SITAS_T15_mfa_blocks_password_caps_bypass_and_preserves_session(graph, controls):
    result = apply_controls(graph, controls, ["MFA"])
    assert "Password" not in result.graph.edges
    assert result.graph.edges["Bypass"].likelihood == 2
    assert result.graph.edges["Token"] == graph.edges["Token"]
    assert {effect.edge_id for effect in result.effects} == {"Password", "Bypass"}


def test_SITAS_T16_rbac_blocks_inappropriate_privilege_only(graph, controls):
    result = apply_controls(graph, controls, ["RBAC"])
    assert "Privilege" not in result.graph.edges
    assert set(graph.edges) - set(result.graph.edges) == {"Privilege"}
    assert result.effects[0].control_id == "RBAC"


def test_SITAS_T17_disablement_targets_selected_identity(graph, controls):
    result = apply_controls(graph, controls, ["Disablement"])
    assert "FormerAuthentication" not in result.graph.edges
    assert result.graph.edges["ActiveAuthentication"] == graph.edges["ActiveAuthentication"]
    assert set(graph.edges) - set(result.graph.edges) == {"FormerAuthentication"}


def test_SITAS_T18_timeout_blocks_stale_session_but_preserves_fresh_and_token(graph, controls):
    result = apply_controls(graph, controls, ["Timeout"])
    assert "Stale" not in result.graph.edges
    assert result.graph.edges["Fresh"] == graph.edges["Fresh"]
    assert result.graph.edges["Token"] == graph.edges["Token"]
    assert set(graph.edges) - set(result.graph.edges) == {"Stale"}


def test_SITAS_T19_administrative_restriction_blocks_tagged_privilege(graph, controls):
    result = apply_controls(graph, controls, ["AdminRestriction"])
    assert "AdminAccess" not in result.graph.edges
    assert result.graph.edges["Reauth"] == graph.edges["Reauth"]


def test_revocation_blocks_stolen_session_without_expiring_other_sessions(graph, controls):
    result = apply_controls(graph, controls, ["Revocation"])
    assert "Token" not in result.graph.edges
    assert {"Stale", "Fresh"} <= result.graph.edges.keys()


def test_individual_accounts_remove_explicit_shared_account_transition(graph, controls):
    result = apply_controls(graph, controls, ["IndividualAccounts"])
    assert "SharedAccount" not in result.graph.edges
    assert result.graph.edges["ActiveAuthentication"] == graph.edges["ActiveAuthentication"]


def test_privileged_reauthentication_caps_transition_without_removing_it(graph, controls):
    result = apply_controls(graph, controls, ["Reauthentication"])
    assert result.graph.edges["Reauth"].likelihood == 2
    assert set(result.graph.edges) == set(graph.edges)
    assert result.effects[0].action == "cap"


def test_device_separation_blocks_shared_device_transition_only(graph, controls):
    result = apply_controls(graph, controls, ["DeviceSeparation"])
    assert set(graph.edges) - set(result.graph.edges) == {"SharedDevice"}
    assert result.graph.edges["Fresh"] == graph.edges["Fresh"]


def test_all_nine_controls_produce_expected_survivors_and_effects(graph, controls):
    result = apply_controls(graph, controls, [item.id for item in controls])
    assert set(result.graph.edges) == {"ActiveAuthentication", "Bypass", "Fresh", "Reauth"}
    assert result.graph.edges["Bypass"].likelihood == result.graph.edges["Reauth"].likelihood == 2
    assert {effect.control_id for effect in result.effects} == {item.id for item in controls}
    assert len(result.effects) == 10
    assert tuple(result.selected_ids) == tuple(sorted(item.id for item in controls))


def test_baseline_graph_and_edge_values_remain_unchanged(graph, controls):
    original_edges = dict(graph.edges)
    original_adjacency = dict(graph.adjacency)
    apply_controls(graph, controls, [item.id for item in controls])
    assert dict(graph.edges) == original_edges
    assert dict(graph.adjacency) == original_adjacency
    assert graph.edges["Bypass"].likelihood == 4


def test_target_selector_matches_edge_destination_and_requires_matching_tag(graph):
    scoped = control("Scoped", rule("ScopedPassword", "password_only", targets=("S",)), rule("ScopedFormer", "account_authentication", targets=("Former",)))
    result = apply_controls(graph, [scoped], ["Scoped"])
    assert set(graph.edges) - set(result.graph.edges) == {"FormerAuthentication"}
    assert "Password" in result.graph.edges
    assert [effect.rule_id for effect in result.effects] == ["ScopedFormer"]


def test_multiple_caps_use_minimum_and_keep_each_rules_own_effect(graph):
    cap_three = control("CapThree", rule("Three", "mfa_bypass", "cap", 3))
    cap_two = control("CapTwo", rule("Two", "mfa_bypass", "cap", 2))
    result = apply_controls(graph, [cap_three, cap_two], ["CapThree", "CapTwo"])
    assert result.graph.edges["Bypass"].likelihood == 2
    assert {(effect.rule_id, effect.before_likelihood, effect.after_likelihood) for effect in result.effects} == {("Three", 4, 3), ("Two", 4, 2)}


def test_cap_cannot_increase_original_likelihood(graph):
    weak_cap = control("WeakCap", rule("Five", "mfa_bypass", "cap", 5))
    result = apply_controls(graph, [weak_cap], ["WeakCap"])
    assert result.graph.edges["Bypass"].likelihood == 4
    assert result.effects[0].before_likelihood == result.effects[0].after_likelihood == 4


def test_block_dominates_cap_and_both_explanations_are_retained(graph):
    capped = control("Cap", rule("CapRule", "mfa_bypass", "cap", 2))
    blocked = control("Block", rule("BlockRule", "mfa_bypass"))
    result = apply_controls(graph, [capped, blocked], ["Cap", "Block"])
    assert "Bypass" not in result.graph.edges
    assert {(effect.action, effect.after_likelihood) for effect in result.effects} == {("cap", 2), ("block", None)}


def test_control_selection_order_and_duplicates_do_not_change_results(graph, controls):
    selected = [item.id for item in controls]
    forward = apply_controls(graph, controls, selected)
    reordered = apply_controls(graph, reversed(controls), [*reversed(selected), "MFA", "Timeout"])
    assert dict(forward.graph.nodes) == dict(reordered.graph.nodes)
    assert dict(forward.graph.edges) == dict(reordered.graph.edges)
    assert forward.effects == reordered.effects
    assert forward.selected_ids == reordered.selected_ids


def test_reapplying_same_controls_is_graph_idempotent(graph, controls):
    selected = [item.id for item in controls]
    first = apply_controls(graph, controls, selected)
    second = apply_controls(first.graph, controls, selected)
    assert dict(first.graph.nodes) == dict(second.graph.nodes)
    assert dict(first.graph.edges) == dict(second.graph.edges)
    assert dict(first.graph.adjacency) == dict(second.graph.adjacency)


def test_empty_selection_preserves_graph_and_has_no_effects(graph, controls):
    result = apply_controls(graph, controls, [])
    assert dict(result.graph.edges) == dict(graph.edges)
    assert result.effects == ()
    assert result.selected_ids == ()


def test_unknown_control_id_fails_clearly(graph, controls):
    with pytest.raises(ModelError):
        apply_controls(graph, controls, ["UnknownControl"])


def test_effect_order_and_serialized_fields_are_deterministic(graph, controls):
    result = apply_controls(graph, controls, ["MFA"])
    assert [(effect.edge_id, effect.control_id, effect.rule_id) for effect in result.effects] == [("Bypass", "MFA", "BypassCap"), ("Password", "MFA", "PasswordBlock")]
    assert result.effects[0].to_dict() == {
        "edgeId": "Bypass", "controlId": "MFA", "ruleId": "BypassCap", "action": "cap",
        "reason": "Synthetic reason for BypassCap.", "beforeLikelihood": 4, "afterLikelihood": 2,
    }
    assert result.effects[1].to_dict()["afterLikelihood"] is None


def test_effect_records_are_immutable(graph, controls):
    effect = apply_controls(graph, controls, ["MFA"]).effects[0]
    with pytest.raises(FrozenInstanceError):
        effect.after_likelihood = 99
