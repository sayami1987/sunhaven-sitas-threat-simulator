"""Coordinator and real command execution verify reproducibility and failures."""

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

import pytest

from src.models import ModelError
from src.sitas import analyse


ROOT = Path(__file__).resolve().parents[1]
FIXED_TIME = "2026-09-10T14:00:00+00:00"


def cli(*arguments):
    return subprocess.run(
        [sys.executable, "-m", "src.sitas", *map(str, arguments)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30,
    )


def test_analyse_returns_consistent_aggregate_and_flat_findings():
    result = analyse(timestamp=FIXED_TIME)
    assert result["summary"]["baselinePaths"] == 15
    assert result["summary"]["blockedPaths"] == 12
    assert len(result["scenarios"]) == 10
    assert len(result["findings"]) == 15
    assert {finding["findingId"] for finding in result["findings"]} == {
        finding["findingId"] for scenario in result["scenarios"] for finding in scenario["findings"]
    }
    for key in ("simulationId", "inputFingerprint", "engineFingerprint", "settings"):
        assert result[key]


def test_identical_inputs_and_fixed_time_produce_identical_result_objects():
    first = analyse(timestamp=FIXED_TIME)
    second = analyse(timestamp=FIXED_TIME)
    assert first == second


def test_generation_time_does_not_change_simulation_identity():
    first = analyse(timestamp=FIXED_TIME)
    later = analyse(timestamp="2026-09-11T00:00:00+00:00")
    assert first["simulationId"] == later["simulationId"]
    assert first["inputFingerprint"] == later["inputFingerprint"]
    assert first["engineFingerprint"] == later["engineFingerprint"]
    assert first["summary"] == later["summary"]
    assert first["generatedAt"] != later["generatedAt"]


def test_aware_timestamp_is_normalised_to_utc():
    result = analyse(timestamp="2026-09-11T00:00:00+10:00")
    generated = datetime.fromisoformat(result["generatedAt"].replace("Z", "+00:00"))
    assert generated.utcoffset().total_seconds() == 0
    assert generated == datetime(2026, 9, 10, 14, tzinfo=timezone.utc)


@pytest.mark.parametrize("timestamp", ["2026-09-10T14:00:00", "not-a-date"])
def test_timestamp_requires_valid_timezone_aware_iso_text(timestamp):
    with pytest.raises(ModelError):
        analyse(timestamp=timestamp)


def test_default_inputs_resolve_independently_of_current_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = analyse(timestamp=FIXED_TIME)
    assert result["summary"]["baselinePaths"] == 15
    assert not (tmp_path / "reports").exists()


def test_changed_valid_environment_changes_input_fingerprint(tmp_path):
    original = analyse(timestamp=FIXED_TIME)
    environment = json.loads((ROOT / "config" / "environment.json").read_text(encoding="utf-8"))
    environment["name"] = "Synthetic renamed environment for fingerprint verification"
    changed_path = tmp_path / "environment.json"
    changed_path.write_text(json.dumps(environment), encoding="utf-8")
    changed = analyse(environment_path=changed_path, timestamp=FIXED_TIME)
    assert changed["inputFingerprint"] != original["inputFingerprint"]
    assert changed["simulationId"] != original["simulationId"]
    assert changed["engineFingerprint"] == original["engineFingerprint"]
    assert changed["summary"] == original["summary"]


def test_selected_scenarios_and_controls_are_applied():
    result = analyse(scenario_ids=["scenario_01", "scenario_06"], controls="mfa", timestamp=FIXED_TIME)
    assert {scenario["scenarioId"] for scenario in result["scenarios"]} == {"scenario_01", "scenario_06"}
    assert result["summary"]["baselinePaths"] == 2
    assert result["summary"]["blockedPaths"] == 1
    assert result["summary"]["reducedPaths"] == 1
    assert result["summary"]["residualExposure"] == 8


def test_none_control_selection_preserves_baseline_exposure():
    result = analyse(controls="none", timestamp=FIXED_TIME)
    assert result["summary"]["remainingPaths"] == 15
    assert result["summary"]["unchangedPaths"] == 15
    assert result["summary"]["residualExposure"] == result["summary"]["baselineExposure"] == 228


def test_duplicate_control_selection_has_same_identity_and_findings():
    single = analyse(controls="mfa,rbac", timestamp=FIXED_TIME)
    duplicate = analyse(controls="rbac,mfa,mfa", timestamp=FIXED_TIME)
    assert single == duplicate


@pytest.mark.parametrize("controls", ["unknown_control", "", " , "])
def test_invalid_control_selection_rejected(controls):
    with pytest.raises(ModelError):
        analyse(controls=controls, timestamp=FIXED_TIME)


def test_unknown_scenario_id_is_rejected():
    with pytest.raises(ModelError):
        analyse(scenario_ids=["scenario_missing"], timestamp=FIXED_TIME)


def test_invalid_bounds_fail_even_when_scenario_has_no_selected_edges(tmp_path):
    scenario = json.loads((ROOT / "scenarios" / "scenario-01-stolen-credential.json").read_text(encoding="utf-8"))
    scenario["edge_ids"] = []
    (tmp_path / "empty-graph.json").write_text(json.dumps(scenario), encoding="utf-8")
    with pytest.raises(ModelError):
        analyse(scenario_dir=tmp_path, max_depth=0, timestamp=FIXED_TIME)


def test_cli_writes_all_reports_and_fixed_time_runs_are_byte_equal(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    for destination in (first, second):
        completed = cli("--timestamp", FIXED_TIME, "--output", destination)
        assert completed.returncode == 0, completed.stderr
    for relative in ("json/sitas-findings.json", "csv/sitas-findings.csv", "html/sitas-threat-assessment.html"):
        first_file, second_file = first / relative, second / relative
        assert first_file.is_file() and first_file.stat().st_size > 0
        assert first_file.read_bytes() == second_file.read_bytes()


def test_cli_repeated_scenario_flags_select_requested_cases(tmp_path):
    destination = tmp_path / "selected"
    completed = cli("--scenario", "scenario_01", "--scenario", "scenario_06", "--controls", "mfa", "--timestamp", FIXED_TIME, "--output", destination)
    assert completed.returncode == 0, completed.stderr
    result = json.loads((destination / "json" / "sitas-findings.json").read_text(encoding="utf-8"))
    assert {scenario["scenarioId"] for scenario in result["scenarios"]} == {"scenario_01", "scenario_06"}
    assert result["summary"]["baselinePaths"] == 2


def test_cli_lists_scenarios_without_creating_reports(tmp_path):
    destination = tmp_path / "listing"
    completed = cli("--list-scenarios", "--output", destination)
    assert completed.returncode == 0, completed.stderr
    assert all(f"scenario_{index:02}" in completed.stdout for index in range(1, 11))
    assert not destination.exists()


def test_cli_malformed_input_fails_without_creating_report_directory(tmp_path):
    malformed = tmp_path / "malformed.json"
    malformed.write_text('{"id":', encoding="utf-8")
    destination = tmp_path / "invalid-output"
    completed = cli("--environment", malformed, "--output", destination)
    assert completed.returncode == 2
    assert "ERROR" in completed.stderr
    assert "Traceback" not in completed.stderr
    assert not destination.exists()


def test_cli_search_resource_failure_does_not_publish_partial_reports(tmp_path):
    destination = tmp_path / "limited-output"
    completed = cli("--max-paths", "1", "--output", destination)
    assert completed.returncode == 2
    assert "ERROR" in completed.stderr
    assert not destination.exists()


def test_cli_unwritable_output_target_fails_clearly_and_preserves_existing_file(tmp_path):
    destination = tmp_path / "existing-file"
    destination.write_text("existing content", encoding="utf-8")
    completed = cli("--output", destination)
    assert completed.returncode == 2
    assert "ERROR" in completed.stderr
    assert "Traceback" not in completed.stderr
    assert destination.read_text(encoding="utf-8") == "existing content"
