"""Self-contained JSON, spreadsheet-safe CSV and escaped HTML report exports."""
import csv
from html import escape
import io
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit


FINDING_FIELDS = (
    "findingId", "pathId", "scenarioId", "title", "sourceNode", "targetNode",
    "orderedPath", "orderedEdges", "pathLength", "likelihood", "impact",
    "riskScore", "severity", "baseline", "residual", "controlsRelevant",
    "controlsApplied", "blocked", "blockedAt", "outcome", "controlEffects",
    "explanation", "recommendation", "edgeDetails",
)
STRUCTURED_FIELDS = {
    "orderedPath", "orderedEdges", "baseline", "residual", "controlsRelevant",
    "controlsApplied", "blockedAt", "controlEffects", "controlReasons", "edgeDetails",
}
RISK_FIELDS = ("likelihood", "impact", "riskScore", "severity")
CSV_FIELDS = ("simulationId", "generatedAt") + FINDING_FIELDS + tuple(
    prefix + key[0].upper() + key[1:]
    for prefix in ("baseline", "residual") for key in RISK_FIELDS
) + ("controlReasons",)


def render_json(result: dict) -> str:
    """Preserve the complete analysis, with stable key ordering and a newline."""
    return json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True,
                      allow_nan=False) + "\n"


def _csv_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value)
    # Preserve the original text after the apostrophe, including leading space.
    # A BOM is included in the ignorable prefix because some importers drop it.
    probe = text.lstrip().lstrip("\ufeff").lstrip()
    return "'" + text if probe.startswith(("=", "+", "-", "@")) else text


def render_csv(result: dict) -> str:
    """One row per finding; structured fields retain compact JSON representations."""
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for finding in result["findings"]:
        row = {"simulationId": result.get("simulationId"),
               "generatedAt": result.get("generatedAt"),
               **{key: finding.get(key) for key in FINDING_FIELDS}}
        for prefix in ("baseline", "residual"):
            risk = finding.get(prefix) or {}
            for key in RISK_FIELDS:
                row[prefix + key[0].upper() + key[1:]] = risk.get(key)
        row["controlReasons"] = [effect.get("reason", "")
                                 for effect in finding.get("controlEffects", [])]
        writer.writerow({key: json.dumps(value, ensure_ascii=False,
                                         separators=(",", ":"), sort_keys=True,
                                         allow_nan=False)
                         if key in STRUCTURED_FIELDS else _csv_value(value)
                         for key, value in row.items()})
    return stream.getvalue()


def _text(value) -> str:
    return escape("—" if value is None else str(value), quote=True)


def _table(headers, rows, *, caption=None) -> str:
    title = f"<caption>{_text(caption)}</caption>" if caption else ""
    head = "".join(f'<th scope="col">{_text(value)}</th>' for value in headers)
    body = "".join("<tr>" + "".join(f"<td>{value}</td>" for value in row) + "</tr>"
                   for row in rows)
    if not body:
        body = f'<tr><td colspan="{len(headers)}">No items in this run.</td></tr>'
    return f'<div class="table-wrap"><table>{title}<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def _list(items) -> str:
    return "<ul>" + "".join(f"<li>{_text(item)}</li>" for item in items) + "</ul>"


def _badge(label) -> str:
    category = str(label).lower()
    css = category if category in {"low", "medium", "high", "critical", "blocked", "reduced", "unchanged"} else "neutral"
    return f'<span class="badge {css}">{_text(label)}</span>'


def _risk(risk) -> str:
    if risk is None:
        return '<span class="muted">Blocked — no residual path</span>'
    return (f'<strong>{_text(risk["riskScore"])}</strong> '
            f'{_badge(risk["severity"])}<small>'
            f'Likelihood {_text(risk["likelihood"])} × impact {_text(risk["impact"])}</small>')


def _node(node_id, names) -> str:
    name = names.get(node_id, node_id)
    return f'{_text(name)}<small><code>{_text(node_id)}</code></small>'


def _reference(reference) -> str:
    title = _text(reference.get("title", "Reference"))
    raw_url = str(reference.get("url", ""))
    try:
        parsed = urlsplit(raw_url)
        safe = (parsed.scheme.lower() in {"http", "https"} and parsed.hostname
                and not any(character.isspace() or ord(character) < 32
                            or ord(character) == 127 for character in raw_url))
    except ValueError:
        safe = False
    if safe:
        return f'<li><a href="{_text(raw_url)}" rel="noreferrer">{title}</a><small>{_text(raw_url)}</small></li>'
    return f'<li>{title}<small>{_text(raw_url)}</small></li>'


STYLE = """
:root{color-scheme:light;--ink:#17283d;--muted:#53657a;--line:#dbe3eb;--navy:#17314f;--teal:#146c67}
*{box-sizing:border-box}body{margin:0;background:#f3f6fa;color:var(--ink);font:15px/1.55 system-ui,-apple-system,'Segoe UI',sans-serif}
main{max-width:1280px;margin:0 auto;padding:34px 28px 70px}header{background:var(--navy);color:white;border-radius:16px;padding:35px 38px;margin-bottom:25px}
header p{max-width:860px;color:#dae6f3}h1{font-size:34px;line-height:1.2;margin:7px 0 13px}h2{font-size:24px;margin:0 0 16px}h3{font-size:19px;margin:0 0 10px}
p{margin:9px 0 16px}.eyebrow{text-transform:uppercase;letter-spacing:.13em;font-size:12px;font-weight:700}.meta-line{overflow-wrap:anywhere;font-size:13px}
section{background:white;border:1px solid var(--line);border-radius:13px;padding:26px;margin:22px 0}.muted,small{color:var(--muted)}small{display:block;font-size:12px;margin-top:4px}
.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px}.metric{background:#f5f8fc;border:1px solid var(--line);border-radius:10px;padding:17px}.metric strong{display:block;font-size:29px;line-height:1.2;margin:6px 0}.metric span{font-size:13px;color:var(--muted)}
.notice{border-left:4px solid var(--teal);background:#edf7f5;padding:13px 16px;margin:16px 0}.notice.warning{border-color:#b07114;background:#fff7e8}
.table-wrap{overflow-x:auto;margin:14px 0 20px}table{border-collapse:collapse;width:100%;font-size:13px;text-align:left}caption{text-align:left;font-weight:650;font-size:15px;margin:0 0 9px}th{background:#edf2f8;font-weight:650;white-space:nowrap}th,td{padding:11px 12px;border-bottom:1px solid var(--line);vertical-align:top}td{overflow-wrap:anywhere}tbody tr:last-child td{border-bottom:0}
.badge{display:inline-block;border-radius:20px;font-size:11px;font-weight:700;padding:3px 9px;white-space:nowrap}.critical{background:#f8dde1;color:#922c40}.high{background:#ffe7cf;color:#8e4a0b}.medium{background:#fff0bd;color:#795c00}.low,.blocked{background:#dbf0e7;color:#176044}.reduced{background:#def1f1;color:#176362}.unchanged,.neutral{background:#e8edf4;color:#435773}
.finding{border-top:1px solid var(--line);padding:25px 0 12px}.finding:first-of-type{border-top:0;padding-top:0}.finding-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:20px}.finding-heading h3{margin-bottom:4px}.risk-pair{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:16px 0}.risk-box{padding:14px 17px;border:1px solid var(--line);border-radius:9px}.risk-box>span{font-size:12px;color:var(--muted);display:block;margin-bottom:7px}
code{font:12px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace;overflow-wrap:anywhere}a{color:#135da6}ul{padding-left:23px}li{margin:8px 0}dl{display:grid;grid-template-columns:190px 1fr;gap:8px 20px}dt{font-weight:650}dd{margin:0;overflow-wrap:anywhere}.control-note{font-size:13px}.footer{color:var(--muted);font-size:12px;margin-top:26px}
@media(max-width:760px){main{padding:16px 12px 35px}header,section{padding:20px}h1{font-size:28px}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.risk-pair{grid-template-columns:1fr}dl{grid-template-columns:1fr;gap:2px}dd{margin-bottom:10px}.finding-heading{display:block}}
@media print{body{background:white;font-size:11px}main{padding:0;max-width:none}header{background:white;color:var(--ink);border-bottom:2px solid var(--navy);padding:12px 0;border-radius:0}header p{color:var(--muted)}section{border:0;border-radius:0;padding:12px 0;break-inside:auto}.table-wrap{overflow:visible}thead{display:table-header-group}tr,.risk-pair,.metric{break-inside:avoid}h2,h3{break-after:avoid}a{color:inherit}.metrics{gap:8px}}
"""


def render_html(result: dict) -> str:
    """Render all findings with escaped text, no JavaScript or remote resources."""
    findings = result["findings"]
    scenarios = result["scenarios"]
    summary = result["summary"]
    settings = result.get("settings", {})
    names = result.get("nodeNames", {})
    title = _text(result.get("title", "SITAS Threat Assessment Report"))
    parts = [f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
             '<meta name="viewport" content="width=device-width,initial-scale=1">'
             '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; style-src &#39;unsafe-inline&#39;; base-uri &#39;none&#39;; form-action &#39;none&#39;">'
             f'<title>{title}</title><style>{STYLE}</style></head><body><main>',
             '<header><div class="eyebrow">Sunhaven / SITAS / Synthetic model</div>',
             f'<h1>{title}</h1><p>Attack-path and control-effect comparison for a fictional environment. '
             'Scores describe ordinal modelled exposure; they are not probabilities or evidence of a real incident.</p>',
             f'<div class="meta-line">Generated {_text(result.get("generatedAt"))} · '
             f'Simulation <code>{_text(result.get("simulationId"))}</code></div></header>',
             '<section id="summary"><h2>Summary</h2><div class="metrics">']
    metrics = (("Baseline paths", "baselinePaths"), ("Blocked paths", "blockedPaths"),
               ("Remaining paths", "remainingPaths"), ("Reduced paths", "reducedPaths"),
               ("Unchanged paths", "unchangedPaths"), ("Baseline exposure", "baselineExposure"),
               ("Residual exposure", "residualExposure"), ("Exposure reduction (%)", "exposureReductionPercent"))
    parts.extend(f'<div class="metric"><span>{_text(label)}</span><strong>{_text(summary.get(key))}</strong></div>'
                 for label, key in metrics)
    parts.append('</div><p class="notice">Exposure is the sum of ordinal path scores. Paths may share '
                 'assets and transitions, so this total is not expected financial loss or a probability of compromise.</p>')
    parts.append(_table(("Severity", "Baseline paths", "Remaining paths"),
                        [(_badge(severity), _text(summary.get("baselineSeverity", {}).get(severity, 0)),
                          _text(summary.get("remainingSeverity", {}).get(severity, 0)))
                         for severity in ("Critical", "High", "Medium", "Low")]))
    parts.append('</section><section id="scenarios"><h2>Scenario comparison</h2>')
    parts.append(_table(("Scenario", "Baseline paths", "Blocked", "Reduced", "Unchanged", "Baseline exposure", "Residual exposure"),
                        [(f'<strong>{_text(s["title"])}</strong><small>{_text(s["scenarioId"])}</small>',
                          *(_text(s["summary"].get(key)) for key in
                            ("baselinePaths", "blockedPaths", "reducedPaths", "unchangedPaths", "baselineExposure", "residualExposure")))
                         for s in scenarios]))
    for scenario in scenarios:
        parts.append(f'<p><strong>{_text(scenario["scenarioId"])}:</strong> {_text(scenario.get("description", ""))}</p>')
    parts.append('</section><section id="residual"><h2>Highest residual risks</h2>')
    remaining = sorted((finding for finding in findings if finding.get("residual") is not None),
                       key=lambda finding: (-finding["residual"]["riskScore"], finding["findingId"]))
    parts.append('<p>Up to ten remaining paths, ranked by residual ordinal risk. All findings follow below.</p>')
    parts.append(_table(("Finding / scenario", "Residual risk", "Outcome", "Recommendation"),
                        [(f'<code>{_text(f["findingId"])}</code><small>{_text(f["title"])}</small>',
                          _risk(f["residual"]), _badge(f["outcome"]), _text(f.get("recommendation", "")))
                         for f in remaining[:10]]))
    parts.append('</section><section id="findings"><h2>All findings</h2>')
    if not findings:
        parts.append('<p>No source-to-target paths were found within the configured depth bound. '
                     'This is not a claim that the environment has no other possible attack paths.</p>')
    for index, finding in enumerate(findings, 1):
        parts.extend([f'<article class="finding" id="finding-{index}" data-finding-id="{_text(finding["findingId"])}"><div class="finding-heading"><div>',
                      f'<h3>{index}. {_text(finding["title"])}</h3><code>{_text(finding["findingId"])}</code>',
                      f'<small>Scenario {_text(finding["scenarioId"])} · Path {_text(finding["pathId"])} · '
                      f'{_text(finding["pathLength"])} edges</small></div>{_badge(finding["outcome"])}</div>',
                      '<div class="risk-pair"><div class="risk-box"><span>Baseline risk</span>',
                      _risk(finding["baseline"]), '</div><div class="risk-box"><span>Residual risk</span>',
                      _risk(finding.get("residual")), '</div></div>'])
        nodes = finding["orderedPath"]
        details = {edge["edgeId"]: edge for edge in finding.get("edgeDetails", [])}
        edge_rows = []
        for step, edge_id in enumerate(finding["orderedEdges"]):
            detail = details.get(edge_id, {})
            controlled = detail.get("controlledLikelihood")
            controlled_text = ("blocked" if controlled is None and "controlledLikelihood" in detail
                               else controlled)
            edge_rows.append((_text(step + 1), _node(nodes[step], names),
                              f'<code>{_text(edge_id)}</code><small>{_text(detail.get("relationship", ""))}</small>',
                              _node(nodes[step + 1], names), _text(detail.get("baselineLikelihood")),
                              _text(controlled_text), _text(detail.get("explanation", ""))))
        parts.append(_table(("Step", "From node", "Ordered edge", "To node", "Baseline likelihood", "Controlled likelihood", "Transition rationale"), edge_rows,
                            caption="Ordered attack path"))
        parts.append(f'<p>{_text(finding.get("explanation", ""))}</p>')
        parts.append(f'<p class="control-note"><strong>Relevant controls:</strong> '
                     f'{_text(", ".join(finding.get("controlsRelevant", [])) or "None")}<br>'
                     f'<strong>Applied controls:</strong> '
                     f'{_text(", ".join(finding.get("controlsApplied", [])) or "None")}<br>'
                     f'<strong>Blocked at:</strong> '
                     f'{_text(", ".join(finding.get("blockedAt", [])) or "No blocking edge")}</p>')
        effects = finding.get("controlEffects", [])
        if effects:
            parts.append(_table(("Control / rule", "Edge", "Action", "Original → rule result", "Reason"),
                                [(f'<code>{_text(e["controlId"])} / {_text(e["ruleId"])}</code>',
                                  f'<code>{_text(e["edgeId"])}</code>', _text(e["action"]),
                                  f'{_text(e["beforeLikelihood"])} → {_text(e["afterLikelihood"] if e["afterLikelihood"] is not None else "blocked")}',
                                  _text(e["reason"])) for e in effects], caption="Matched control rules"))
            parts.append('<p class="muted">Each rule result is relative to the original edge. '
                         'Combined caps use the minimum; any matching block removes the edge.</p>')
        parts.append(f'<p><strong>Recommendation:</strong> {_text(finding.get("recommendation", ""))}</p></article>')
    parts.append('</section><section id="bounds"><h2>Search bounds and pruning</h2>')
    parts.append(f'<p>Maximum path depth: {_text(settings.get("maxDepth"))} edges. '
                 f'Path budget: {_text(settings.get("maxPaths"))}. '
                 f'Expansion budget: {_text(settings.get("maxExpansions"))}.</p>')
    search_rows = []
    pruned = False
    for scenario in scenarios:
        search = scenario.get("search", {})
        for phase in ("baseline", "controlled"):
            data = search.get(phase, {})
            pruned = pruned or bool(data.get("depthPruned", 0))
            search_rows.append((_text(scenario["scenarioId"]), _text(phase),
                                _text(data.get("expansions", 0)), _text(data.get("depthPruned", 0))))
    parts.append(_table(("Scenario", "Graph", "Edge expansions", "Depth-pruned transitions"), search_rows))
    parts.append('<p class="notice warning">Depth pruning occurred: these findings cover paths within the configured depth, '
                 'and do not establish global reachability or complete exposure.</p>' if pruned else
                 '<p>No depth-pruned transitions were recorded. Results still depend on the supplied synthetic graph and scenario selection.</p>')
    parts.append('<p>Depth-pruned transitions count excluded extensions, not distinct omitted attack paths. '
                 'The analysis fails when a path or expansion budget is exceeded; it does not publish a partial result as complete.</p>')
    parts.append('</section><section id="metadata"><h2>Run metadata</h2><dl>')
    environment = result.get("environment", {})
    metadata = (("Schema version", result.get("schemaVersion")), ("Generated at", result.get("generatedAt")),
                ("Simulation ID", result.get("simulationId")), ("Environment", environment.get("name")),
                ("Environment ID", environment.get("id")), ("Synthetic environment", environment.get("synthetic")),
                ("Input fingerprint", result.get("inputFingerprint")), ("Engine fingerprint", result.get("engineFingerprint")),
                ("Selected controls", ", ".join(settings.get("selectedControls", [])) or "None"))
    parts.extend(f'<dt>{_text(label)}</dt><dd>{_text(value)}</dd>' for label, value in metadata)
    parts.append('</dl><h3>Control catalogue</h3>')
    parts.append(_table(("ID", "Control", "Modelled purpose"),
                        [(f'<code>{_text(c["id"])}</code>', _text(c.get("name", "")),
                          _text(c.get("description", ""))) for c in result.get("controls", [])]))
    parts.append('</section><section id="methodology"><h2>Methodology</h2>'
                 '<p>Validate the synthetic input, construct each scenario directed graph, and enumerate '
                 'simple paths using iterative depth-first search. Each path uses the minimum edge likelihood '
                 'and the protected target impact. Multiply these ordinal values to obtain its risk score.</p>'
                 '<p>Apply selected control rules to a separate graph: block matching transitions or cap their '
                 'likelihood. Enumerate and score the controlled graph again. Match paths by their full ordered '
                 'edge sequence, then classify each baseline path as blocked, reduced or unchanged.</p>'
                 '<p>The cited guidance informs assessment structure and control context. The numerical '
                 'formula and severity thresholds are SITAS modelling conventions.</p>')
    parts.append('</section><section id="assumptions"><h2>Assumptions</h2>')
    parts.append(_list(result.get("assumptions", [])))
    parts.append('</section><section id="limitations"><h2>Limitations</h2>')
    parts.append(_list(result.get("limitations", [])))
    parts.append('</section><section id="references"><h2>References</h2><ul>')
    parts.extend(_reference(reference) for reference in result.get("references", []))
    parts.append('</ul></section><p class="footer">Generated by SITAS from synthetic inputs. '
                 'This self-contained report uses no scripts, remote styles, tracking or external resources.</p></main></body></html>\n')
    return "".join(parts)


def write_reports(result: dict, output_dir: str | Path) -> dict[str, Path]:
    """Render all formats, then stage and replace each complete output file.

    Replacement is atomic per file, not a transaction across all three files.
    If replacement fails partway through, earlier complete replacements can
    remain alongside older files. Temporary staging files are cleaned up.
    """
    rendered = {"json": render_json(result), "csv": render_csv(result),
                "html": render_html(result)}
    base = Path(output_dir)
    names = {"json": "sitas-findings.json", "csv": "sitas-findings.csv",
             "html": "sitas-threat-assessment.html"}
    destinations = {kind: base / kind / names[kind] for kind in rendered}
    staged = []
    try:
        for kind, content in rendered.items():
            destination = destinations[kind]
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                             prefix=".sitas-", suffix=".tmp",
                                             dir=destination.parent, delete=False) as stream:
                temporary = Path(stream.name)
                staged.append((temporary, destination))
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        for temporary, destination in staged:
            os.replace(temporary, destination)
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)
    return destinations
