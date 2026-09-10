"""Cross-format checks and hostile display data verify report integrity."""

import copy
import csv
from html.parser import HTMLParser
import io
import json
from pathlib import Path

import pytest

from src import report_generator
from src.models import ModelError
from src.report_generator import render_csv, render_html, render_json, write_reports
from src.sitas import analyse


ROOT = Path(__file__).resolve().parents[1]
FIXED_TIMESTAMP = "2026-09-11T00:00:00+00:00"
OUTPUT_NAMES = {
    "json": Path("json/sitas-findings.json"),
    "csv": Path("csv/sitas-findings.csv"),
    "html": Path("html/sitas-threat-assessment.html"),
}
RENDERERS = {"json": render_json, "csv": render_csv, "html": render_html}
FINDING_FIELDS = {
    "findingId", "pathId", "scenarioId", "title", "sourceNode", "targetNode",
    "orderedPath", "orderedEdges", "pathLength", "likelihood", "impact", "riskScore",
    "severity", "baseline", "residual", "controlsRelevant", "controlsApplied",
    "blocked", "blockedAt", "outcome", "controlEffects", "edgeDetails", "explanation", "recommendation",
}
STRUCTURED_FIELDS = {
    "orderedPath", "orderedEdges", "baseline", "residual", "controlsRelevant",
    "controlsApplied", "blockedAt", "controlEffects", "edgeDetails",
}


class ParsedHTML(HTMLParser):
    """Read rendered text and real attributes, distinguishing escaped markup."""

    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.text_parts = []
        self.script_parts = []
        self.in_script = False
        self.finding_text = {}
        self.active_finding = None
        self.metrics = []
        self.active_metric = None
        self.feed(source)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if tag == "script":
            self.in_script = True
        if tag == "article" and "data-finding-id" in attrs:
            self.active_finding = attrs["data-finding-id"]
            self.finding_text[self.active_finding] = []
        if tag == "div" and "metric" in attrs.get("class", "").split():
            self.active_metric = []

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        self.text_parts.append(data)
        if self.in_script:
            self.script_parts.append(data)
        if self.active_finding is not None:
            self.finding_text[self.active_finding].append(data)
        if self.active_metric is not None and data.strip():
            self.active_metric.append(data.strip())

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False
        if tag == "article":
            self.active_finding = None
        if tag == "div" and self.active_metric is not None:
            self.metrics.append(self.active_metric)
            self.active_metric = None

    @property
    def text(self):
        return " ".join(self.text_parts)


@pytest.fixture(scope="module")
def report():
    return analyse(environment_path=ROOT / "config/environment.json",
                   controls_path=ROOT / "config/controls.json",
                   risk_path=ROOT / "config/risk-model.json",
                   scenario_dir=ROOT / "scenarios", controls="all", timestamp=FIXED_TIMESTAMP)


def csv_rows(source):
    return list(csv.DictReader(io.StringIO(source, newline="")))


def test_SITAS_T21_json_retains_complete_analysis_and_required_finding_fields(report):
    decoded = json.loads(render_json(report))
    assert decoded == report
    assert decoded["schemaVersion"] == 1
    assert decoded["environment"]["synthetic"] is True
    assert decoded["generatedAt"] == FIXED_TIMESTAMP
    assert len(decoded["findings"]) == decoded["summary"]["baselinePaths"] == 15
    assert len(decoded["scenarios"]) == 10
    assert len({item["findingId"] for item in decoded["findings"]}) == 15
    assert decoded["summary"]["baselineExposure"] == 228
    assert decoded["summary"]["residualExposure"] == 27
    for finding in decoded["findings"]:
        assert FINDING_FIELDS <= finding.keys()
        assert finding["pathLength"] == len(finding["orderedEdges"]) == len(finding["orderedPath"]) - 1
        assert finding["blocked"] == (finding["residual"] is None)
        assert finding["riskScore"] == finding["baseline"]["riskScore"]
        details = finding["edgeDetails"]
        assert [item["edgeId"] for item in details] == finding["orderedEdges"]
        assert [(item["source"], item["target"]) for item in details] == list(zip(finding["orderedPath"], finding["orderedPath"][1:]))
        assert all(item["relationship"] and item["explanation"] for item in details)
        assert min(item["baselineLikelihood"] for item in details) == finding["baseline"]["likelihood"]
        if finding["residual"] is not None:
            assert min(item["controlledLikelihood"] for item in details) == finding["residual"]["likelihood"]
        else:
            assert {item["edgeId"] for item in details if item["controlledLikelihood"] is None} == set(finding["blockedAt"])


def test_SITAS_T22_csv_reconciles_every_finding_and_nested_control_effect(report):
    rows = csv_rows(render_csv(report))
    assert len(rows) == len(report["findings"])
    by_id = {row["findingId"]: row for row in rows}
    assert len(by_id) == len(rows)
    for finding in report["findings"]:
        row = by_id[finding["findingId"]]
        assert FINDING_FIELDS <= row.keys()
        assert row["simulationId"] == report["simulationId"]
        assert row["generatedAt"] == report["generatedAt"]
        assert json.loads(row["controlReasons"]) == [item["reason"] for item in finding["controlEffects"]]
        for key in STRUCTURED_FIELDS:
            assert json.loads(row[key]) == finding[key]
        for key in ("pathId", "scenarioId", "title", "sourceNode", "targetNode",
                    "severity", "outcome", "explanation", "recommendation"):
            assert row[key] == finding[key]
        for key in ("pathLength", "likelihood", "impact", "riskScore"):
            assert int(row[key]) == finding[key]
        assert row["blocked"] == str(finding["blocked"]).lower()
        for prefix, score in (("baseline", finding["baseline"]), ("residual", finding["residual"])):
            for name in ("likelihood", "impact", "riskScore", "severity"):
                column = prefix + name[0].upper() + name[1:]
                assert row[column] == (str(score[name]) if score is not None else "")
    assert sum(int(row["riskScore"]) for row in rows) == report["summary"]["baselineExposure"]
    assert sum(int(row["residualRiskScore"]) for row in rows if row["residualRiskScore"]) == report["summary"]["residualExposure"]
    assert sum(row["blocked"] == "true" for row in rows) == report["summary"]["blockedPaths"]


def test_SITAS_T23_html_contains_run_metadata_and_all_finding_evidence(report):
    parsed = ParsedHTML(render_html(report))
    assert set(parsed.finding_text) == {item["findingId"] for item in report["findings"]}
    assert sum(tag == "article" and "data-finding-id" in attrs for tag, attrs in parsed.elements) == len(report["findings"])
    for label, key in (("Baseline paths", "baselinePaths"), ("Blocked paths", "blockedPaths"),
                       ("Remaining paths", "remainingPaths"), ("Reduced paths", "reducedPaths"),
                       ("Unchanged paths", "unchangedPaths"), ("Baseline exposure", "baselineExposure"),
                       ("Residual exposure", "residualExposure"), ("Exposure reduction (%)", "exposureReductionPercent")):
        assert [label, str(report["summary"][key])] in parsed.metrics
    for value in (report["title"], report["generatedAt"], report["simulationId"],
                  report["inputFingerprint"], report["engineFingerprint"], report["environment"]["name"]):
        assert value in parsed.text
    for finding in report["findings"]:
        section = " ".join(" ".join(parsed.finding_text[finding["findingId"]]).split())
        for key in ("findingId", "pathId", "scenarioId", "explanation", "recommendation"):
            assert finding[key] in section
        for label, risk in (("Baseline risk", finding["baseline"]), ("Residual risk", finding["residual"])):
            if risk is None:
                assert label + " Blocked — no residual path" in section
            else:
                assert f"{label} {risk['riskScore']} {risk['severity']}" in section
                assert f"Likelihood {risk['likelihood']} × impact {risk['impact']}" in section
        for item in finding["edgeDetails"]:
            assert item["explanation"] in section
    assert all(limitation in parsed.text for limitation in report["limitations"])
    assert all(assumption in parsed.text for assumption in report["assumptions"])


@pytest.mark.parametrize("format_name", tuple(RENDERERS))
def test_fixed_timestamp_produces_identical_report_bytes(report, format_name):
    again = analyse(controls="all", timestamp=FIXED_TIMESTAMP)
    assert RENDERERS[format_name](report).encode("utf-8") == RENDERERS[format_name](again).encode("utf-8")


def test_rendering_does_not_mutate_the_completed_analysis(report):
    before = copy.deepcopy(report)
    for renderer in RENDERERS.values():
        renderer(report)
    assert report == before


@pytest.mark.parametrize("payload", [
    '=HYPERLINK("https://example.invalid","synthetic")',
    "+SUM(1,2)", "-1+2", "@SUM(1,2)", "\t=1+1", " \r\n@SUM(1,2)",
])
def test_csv_neutralises_formula_prefixes_without_dropping_original_text(report, payload):
    hostile = copy.deepcopy(report)
    hostile["findings"][0]["title"] = payload
    hostile["findings"][0]["explanation"] = payload
    hostile["findings"][0]["recommendation"] = payload
    row = next(item for item in csv_rows(render_csv(hostile))
               if item["findingId"] == hostile["findings"][0]["findingId"])
    for field in ("title", "explanation", "recommendation"):
        assert row[field] == "'" + payload


def test_csv_preserves_unicode_quotes_commas_and_line_breaks_as_one_cell(report):
    modified = copy.deepcopy(report)
    label = 'Synthetic Ω care, "quoted"\nSecond line'
    modified["findings"][0]["title"] = label
    rows = csv_rows(render_csv(modified))
    assert len(rows) == len(report["findings"])
    assert rows[0]["title"] == label


def test_html_escapes_hostile_labels_and_attribute_delimiters(report):
    hostile = copy.deepcopy(report)
    payload = '<img src="synthetic-marker" onerror="alert(1)"><script>synthetic_marker()</script> & "quoted"'
    hostile["title"] = payload
    hostile["environment"]["name"] = payload
    hostile["findings"][0]["title"] = payload
    hostile["findings"][0]["explanation"] = payload
    hostile["findings"][0]["recommendation"] = payload
    hostile["findings"][0]["findingId"] = 'Synthetic" autofocus onfocus="alert(1)'
    hostile["assumptions"].append(payload)
    hostile["limitations"].append(payload)
    hostile["references"] = [{"title": payload, "url": 'https://example.invalid/" onmouseover="alert(1)'}]
    parsed = ParsedHTML(render_html(hostile))
    assert payload in parsed.text
    assert "synthetic_marker()" not in "".join(parsed.script_parts)
    assert not any(attrs.get("src") == "synthetic-marker" for _, attrs in parsed.elements)
    assert not any(name.startswith("on") or name == "autofocus"
                   for _, attrs in parsed.elements for name in attrs)
    assert not any('onmouseover=' in name for _, attrs in parsed.elements for name in attrs)


@pytest.mark.parametrize("unsafe_url", [
    "javascript:alert(1)", " \tJaVaScRiPt:alert(1)", "java\nscript:alert(1)",
    "data:text/html,<script>alert(1)</script>", "file:///synthetic-local-file", "//example.invalid/untrusted",
])
def test_html_keeps_non_http_reference_urls_inert(report, unsafe_url):
    hostile = copy.deepcopy(report)
    hostile["references"] = [{"title": "Synthetic hostile URL test", "url": unsafe_url}]
    parsed = ParsedHTML(render_html(hostile))
    for _, attrs in parsed.elements:
        for name in ("href", "src", "action", "formaction"):
            value = attrs.get(name, "")
            normalised = "".join(character for character in value if not character.isspace()).lower()
            assert not normalised.startswith(("javascript:", "data:", "file:", "//"))


def test_valid_reference_url_and_title_preserve_ampersands_without_creating_attributes(report):
    changed = copy.deepcopy(report)
    url = "https://example.invalid/reference?a=1&b=2"
    title = "Synthetic reference & explanation"
    changed["references"] = [{"title": title, "url": url}]
    parsed = ParsedHTML(render_html(changed))
    assert any(tag == "a" and attrs.get("href") == url for tag, attrs in parsed.elements)
    assert title in parsed.text


def test_write_reports_creates_exact_complete_files_matching_rendered_content(report, tmp_path):
    output = tmp_path / "assessment-output"
    paths = write_reports(report, output)
    assert set(paths) == set(OUTPUT_NAMES)
    for format_name, relative_path in OUTPUT_NAMES.items():
        assert isinstance(paths[format_name], Path)
        assert paths[format_name] == output / relative_path
        assert paths[format_name].read_bytes() == RENDERERS[format_name](report).encode("utf-8")
    assert {path.relative_to(output) for path in output.rglob("*") if path.is_file()} == set(OUTPUT_NAMES.values())
    assert write_reports(report, output) == paths


def test_output_path_conflict_is_reported_without_overwriting_the_existing_file(report, tmp_path):
    output = tmp_path / "existing-file"
    output.write_text("Synthetic existing file must survive.", encoding="utf-8")
    with pytest.raises((OSError, ModelError)):
        write_reports(report, output)
    assert output.read_text(encoding="utf-8") == "Synthetic existing file must survive."


def test_replacement_failure_leaves_only_complete_old_or_new_reports(report, tmp_path, monkeypatch):
    output = tmp_path / "reports"
    original_paths = write_reports(report, output)
    original_bytes = {key: path.read_bytes() for key, path in original_paths.items()}
    changed = copy.deepcopy(report)
    changed["title"] = "Synthetic replacement report"
    replacement_bytes = {key: renderer(changed).encode("utf-8") for key, renderer in RENDERERS.items()}
    original_replace = report_generator.os.replace
    calls = 0

    def fail_second_replace(source, destination, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("Synthetic injected replacement failure")
        return original_replace(source, destination, *args, **kwargs)

    monkeypatch.setattr(report_generator.os, "replace", fail_second_replace)
    with pytest.raises((OSError, ModelError)):
        write_reports(changed, output)
    assert calls == 2
    for format_name, path in original_paths.items():
        assert path.read_bytes() in (original_bytes[format_name], replacement_bytes[format_name])
    assert {path.relative_to(output) for path in output.rglob("*") if path.is_file()} == set(OUTPUT_NAMES.values())


def test_late_render_failure_preserves_all_existing_report_files(report, tmp_path, monkeypatch):
    output = tmp_path / "reports"
    paths = write_reports(report, output)
    before = {key: path.read_bytes() for key, path in paths.items()}

    def fail_html(_):
        raise ValueError("Synthetic formatter failure")

    monkeypatch.setattr(report_generator, "render_html", fail_html)
    with pytest.raises((ValueError, ModelError)):
        write_reports(report, output)
    assert {key: path.read_bytes() for key, path in paths.items()} == before
    assert {path.relative_to(output) for path in output.rglob("*") if path.is_file()} == set(OUTPUT_NAMES.values())
