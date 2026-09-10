"""Scenario acceptance expectations derived by reading the synthetic model."""

from pathlib import Path

import pytest

from src.comparison_engine import compare_scenario, summarize
from src.model_loader import load_controls, load_environment, load_risk_model, load_scenarios


ROOT = Path(__file__).resolve().parents[1]

# Explicit edge routes and hand-calculated minimum-likelihood times target-impact.
# These literals are independent acceptance expectations, not captured engine output.
EXPECTED_PATHS = {
    "scenario_01": {
        ("edge_worker_password_acquired", "edge_worker_password_login", "edge_worker_care_portal", "edge_care_records_access"): 20,
    },
    "scenario_02": {
        ("edge_local_shared_workstation", "edge_workstation_stale_session", "edge_stale_shared_identity", "edge_shared_medication_access", "edge_medication_records_access"): 16,
        ("edge_local_shared_workstation", "edge_workstation_fresh_session", "edge_fresh_shared_identity", "edge_shared_medication_access", "edge_medication_records_access"): 12,
    },
    "scenario_03": {
        ("edge_former_identity_reuse", "edge_former_medication_access", "edge_medication_records_access"): 16,
    },
    "scenario_04": {
        ("edge_internal_worker_identity", "edge_worker_excessive_role", "edge_excessive_admin_console", "edge_admin_payroll_access"): 20,
    },
    "scenario_05": {
        ("edge_admin_password_acquired", "edge_admin_password_login", "edge_admin_unrestricted_role", "edge_unrestricted_admin_console", "edge_console_identity_store"): 20,
        ("edge_stolen_admin_session", "edge_admin_session_console", "edge_console_identity_store"): 15,
    },
    "scenario_06": {
        ("edge_social_password_acquired", "edge_social_mfa_approval", "edge_mfa_worker_identity", "edge_worker_roster_access", "edge_staff_roster_access"): 16,
    },
    "scenario_07": {
        ("edge_copied_staff_session", "edge_cross_device_reuse", "edge_cross_device_roster", "edge_staff_roster_access"): 16,
        ("edge_copied_staff_session", "edge_same_device_reuse", "edge_same_device_roster", "edge_staff_roster_access"): 12,
    },
    "scenario_08": {
        ("edge_agency_password_acquired", "edge_agency_password_login", "edge_agency_shared_workstation", "edge_agency_workstation_console", "edge_agency_roster_access"): 9,
        ("edge_agency_operator_compromise", "edge_agency_delegated_identity", "edge_agency_console_access", "edge_agency_roster_access"): 9,
    },
    "scenario_09": {
        ("edge_internal_agency_identity", "edge_agency_misassigned_role", "edge_wrong_role_medication", "edge_medication_records_access"): 12,
    },
    "scenario_10": {
        ("edge_service_password_acquired", "edge_service_password_login", "edge_service_workstation_access", "edge_workstation_internal_support", "edge_service_excessive_role", "edge_service_unrestricted_export", "edge_export_care_archive"): 20,
        ("edge_support_operator_influence", "edge_support_active_identity", "edge_support_approved_export_role", "edge_support_permitted_export", "edge_export_care_archive"): 15,
    },
}

# Surviving outcome, score: all other baseline routes should be blocked.
EXPECTED_REMAINING = {"scenario_06": ("reduced", 8), "scenario_08": ("unchanged", 9), "scenario_10": ("reduced", 10)}


@pytest.fixture(scope="module")
def project():
    environment = load_environment(ROOT / "config" / "environment.json")
    controls = load_controls(ROOT / "config" / "controls.json", environment)
    risk_model = load_risk_model(ROOT / "config" / "risk-model.json")
    scenarios = {scenario.id: scenario for scenario in load_scenarios(ROOT / "scenarios", environment)}
    return environment, controls, risk_model, scenarios


def analyse(project, scenario_id, selected=None):
    environment, controls, risk_model, scenarios = project
    if selected is None:
        selected = [control.id for control in controls]
    return compare_scenario(environment, scenarios[scenario_id], risk_model, controls, selected)


@pytest.mark.parametrize("scenario_id", tuple(EXPECTED_PATHS))
def test_SITAS_T24_each_scenario_matches_explicit_paths_scores_and_control_outcomes(project, scenario_id):
    result = analyse(project, scenario_id)
    expected = EXPECTED_PATHS[scenario_id]
    assert {tuple(finding["orderedEdges"]): finding["baseline"]["riskScore"] for finding in result["findings"]} == expected
    assert result["summary"]["baselinePaths"] == len(expected)
    survivors = [finding for finding in result["findings"] if not finding["blocked"]]
    if scenario_id in EXPECTED_REMAINING:
        outcome, residual_score = EXPECTED_REMAINING[scenario_id]
        assert len(survivors) == 1
        assert (survivors[0]["outcome"], survivors[0]["residual"]["riskScore"]) == (outcome, residual_score)
    else:
        assert survivors == []
    assert result["summary"]["blockedPaths"] == len(expected) - len(survivors)
    for finding in result["findings"]:
        assert finding["orderedPath"][0] == result["sourceNode"]
        assert finding["orderedPath"][-1] == result["targetNode"]
        assert finding["pathLength"] == len(finding["orderedEdges"])
        assert finding["explanation"] and finding["recommendation"]
        if finding["blocked"]:
            assert finding["blockedAt"] and finding["controlsApplied"]
            assert finding["residual"] is None
    assert result["search"]["baseline"]["depthPruned"] == 0


def test_all_scenarios_have_reconciled_hand_calculated_totals(project):
    assert set(project[3]) == set(EXPECTED_PATHS)
    findings = [finding for scenario_id in EXPECTED_PATHS for finding in analyse(project, scenario_id)["findings"]]
    totals = summarize(findings)
    assert {key: totals[key] for key in ("baselinePaths", "blockedPaths", "remainingPaths", "reducedPaths", "unchangedPaths")} == {
        "baselinePaths": 15, "blockedPaths": 12, "remainingPaths": 3, "reducedPaths": 2, "unchangedPaths": 1,
    }
    # Baseline: 20+28+16+20+35+16+28+18+12+35. Residual: 2*4 + 3*3 + 2*5.
    assert totals["baselineExposure"] == 228
    assert totals["residualExposure"] == 27
    assert totals["baselineSeverity"] == {"Low": 0, "Medium": 2, "High": 9, "Critical": 4}
    assert totals["remainingSeverity"] == {"Low": 0, "Medium": 2, "High": 1, "Critical": 0}
    assert len({finding["findingId"] for finding in findings}) == 15


def test_mfa_alone_preserves_administrator_session_alternative(project):
    result = analyse(project, "scenario_05", ["mfa"])
    assert result["summary"]["blockedPaths"] == 1
    survivors = [finding for finding in result["findings"] if not finding["blocked"]]
    assert len(survivors) == 1
    assert survivors[0]["orderedEdges"] == ["edge_stolen_admin_session", "edge_admin_session_console", "edge_console_identity_store"]
    assert survivors[0]["residual"]["riskScore"] == 15
    assert survivors[0]["controlsApplied"] == []


def test_mfa_alone_does_not_remove_session_only_scenario(project):
    result = analyse(project, "scenario_07", ["mfa"])
    assert result["summary"]["remainingPaths"] == 2
    assert result["summary"]["unchangedPaths"] == 2
    assert all(not finding["controlEffects"] for finding in result["findings"])


def test_timeout_alone_leaves_fresh_shared_session_path(project):
    result = analyse(project, "scenario_02", ["session_timeout"])
    assert result["summary"]["blockedPaths"] == 1
    survivor = next(finding for finding in result["findings"] if not finding["blocked"])
    assert "edge_workstation_fresh_session" in survivor["orderedEdges"]
    assert survivor["residual"]["riskScore"] == 12
    assert survivor["outcome"] == "unchanged"


def test_disablement_matches_stale_identity_but_preserves_active_worker(project):
    former = analyse(project, "scenario_03", ["account_disablement"])
    active = analyse(project, "scenario_01", ["account_disablement"])
    assert former["summary"]["blockedPaths"] == 1
    assert former["findings"][0]["blockedAt"] == ["edge_former_identity_reuse"]
    assert active["summary"]["unchangedPaths"] == 1
    assert active["findings"][0]["controlsApplied"] == []


def test_device_separation_preserves_original_device_while_revocation_blocks_both(project):
    separated = analyse(project, "scenario_07", ["device_session_separation"])
    revoked = analyse(project, "scenario_07", ["session_revocation"])
    survivor = next(finding for finding in separated["findings"] if not finding["blocked"])
    assert "edge_same_device_reuse" in survivor["orderedEdges"]
    assert separated["summary"]["remainingPaths"] == 1
    assert revoked["summary"]["remainingPaths"] == 0


def test_agency_primary_route_contains_credential_shared_device_and_application(project):
    result = analyse(project, "scenario_08")
    primary = next(finding for finding in result["findings"] if "edge_agency_password_login" in finding["orderedEdges"])
    assert primary["orderedPath"] == [
        "attacker_external", "credential_agency", "identity_agency_password_context",
        "workstation_agency_shared", "app_agency", "asset_agency_roster",
    ]
    assert primary["blockedAt"] == ["edge_agency_password_login"]
    survivor = next(finding for finding in result["findings"] if not finding["blocked"])
    assert "edge_agency_operator_compromise" in survivor["orderedEdges"]
    assert survivor["baseline"] == survivor["residual"]


def test_multistage_primary_places_workstation_and_application_before_privilege(project):
    result = analyse(project, "scenario_10")
    primary = next(finding for finding in result["findings"] if "edge_service_password_login" in finding["orderedEdges"])
    assert primary["orderedPath"] == [
        "attacker_external", "credential_service", "identity_service", "workstation_service",
        "app_internal_support", "privilege_service_excessive", "app_export", "asset_care_archive",
    ]
    survivor = next(finding for finding in result["findings"] if not finding["blocked"])
    # The assumed authorised-operator route has minimum 3, capped to 2 at an impact-5 target.
    assert survivor["baseline"]["riskScore"] == 15
    assert survivor["residual"]["riskScore"] == 10
    assert survivor["controlsApplied"] == ["privileged_reauthentication"]


def test_no_controls_preserves_all_baseline_routes_and_scores(project):
    findings = [finding for scenario_id in EXPECTED_PATHS for finding in analyse(project, scenario_id, [])["findings"]]
    assert len(findings) == 15
    assert all(finding["outcome"] == "unchanged" and finding["baseline"] == finding["residual"] for finding in findings)
    assert summarize(findings)["residualExposure"] == 228
