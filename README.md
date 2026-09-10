# SITAS

**Sunhaven Identity Threat and Attack-Path Simulator**

SITAS models how compromised identities, credentials, shared devices, sessions and privileges can expose protected assets in fictional Sunhaven Care. It discovers directed attack paths, explains their ordinal risk and compares the model after selected controls.

This is an educational cybersecurity prototype using fictional/synthetic data. It is Loojaw Manandhar's standalone COIT13236 individual project. Its Python application and local JSON files provide the complete simulation runtime. Live accounts, resident records and external application integrations are unnecessary.

## Current status

Phases 1–8 have been implemented, tested in their phase suites, committed and pushed. The ten scenarios produce 15 baseline paths; all nine controls block 12, reduce two and leave one unchanged. Three paths remain, with ordinal scores 8, 9 and 10.

Phase 9 documentation is in progress. The five editable Draw.io files are **drafts awaiting authoring/review and PNG export in Draw.io itself**. Custom-rendered PNG drafts are no longer part of the current delivery. Native application access was interrupted by a browser URL-verification failure. Final full-suite testing, demonstration and repository release review are subsequent phases and are not recorded as completed.

## Features and design

- Strict JSON validation with duplicate-key, type, reference and size checks.
- Directed multigraph with stable edge identities and cycle inspection.
- Iterative depth-first enumeration of bounded simple paths, including alternative and parallel-edge routes.
- Risk: minimum edge likelihood × target impact; Low 1–4, Medium 5–9, High 10–16, Critical 17–25.
- Nine explicit controls that block transitions or cap their likelihood.
- Independent controlled-graph traversal and blocked/reduced/unchanged comparison.
- JSON, CSV and self-contained HTML with input/source fingerprints, ordered paths and control reasons.

[System design](docs/design/system-design.md) · [Component design](docs/design/component-design.md) · [Draw.io status](docs/diagrams/README.md) · [Report contract](docs/design/report-contract.md)

## Installation

Python 3.11 or later is the language target. Execution used Python 3.12.14 on Windows; other platforms and versions have not been independently validated. Analysis uses the standard library. Development packages provide pytest:

```powershell
git clone https://github.com/sayami1987/sunhaven-sitas-threat-simulator.git
cd sunhaven-sitas-threat-simulator
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS/Linux use `.venv/bin/python` instead. Package installation requires access to a package source; subsequent analysis requires no network connection.

## Run the analysis

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m src.sitas --controls all
.\.venv\Scripts\python.exe -m src.sitas --controls none --output reports/baseline
.\.venv\Scripts\python.exe -m src.sitas --scenario scenario_01 --controls mfa --output reports/mfa
.\.venv\Scripts\python.exe -m src.sitas --scenario scenario_07 --controls session_timeout,session_revocation --output reports/sessions
.\.venv\Scripts\python.exe -m src.sitas --list-scenarios
```

Default outputs: [JSON](reports/json/sitas-findings.json), [CSV](reports/csv/sitas-findings.csv), [SITAS Threat Assessment Report](reports/html/sitas-threat-assessment.html). Download/open the HTML locally; GitHub displays its source. No server is required.

Use `--help` for local input paths and options. Defaults are 12 edges per path, 10,000 paths and 100,000 expansions per scenario graph. Depth pruning is disclosed. Exceeding a path or expansion budget returns an error. Failed runs can leave older outputs intact; verify their timestamp and simulation ID.

Control IDs: `mfa`, `rbac`, `account_disablement`, `session_timeout`, `session_revocation`, `individual_accounts`, `privileged_reauthentication`, `admin_restriction`, `device_session_separation`.

For exact export comparison, supply the same timezone-aware timestamp, for example `--timestamp 2026-09-10T15:00:00+00:00`. This is caller-selected reproducibility metadata, not execution-time evidence. Logs retain actual execution timestamps.

## Testing and evidence

```powershell
.\.venv\Scripts\python.exe scripts/run_tests.py -q
.\.venv\Scripts\python.exe scripts/run_scenarios.py --controls all
```

There are 314 collected automated cases. Phase-specific executions appear in [test results](docs/testing/test-results.md); the final full-suite run remains Phase 10 work. Tests cover independent path oracles, literal scenario expectations, invalid input, cycles, parallel edges, bounds, scoring, controls, report consistency, display escaping and output failures.

[Requirements traceability](docs/requirements/requirements-traceability.md) · [Development Journal](evidence/Development-Journal.md) · [Phase Completion Register](evidence/Phase-Completion-Register.md) · [Screenshot Evidence Register](evidence/Screenshot-Evidence-Register.md)

## Repository structure

```text
src/         Validation, graph, traversal, risk, control, comparison, reports and CLI
config/      Synthetic environment, controls and risk conventions
scenarios/   Ten independent scenario definitions
tests/       Unit, scenario and integration checks
scripts/     Repeatable inspection, tests, reporting and evidence commands
reports/     Actual JSON, CSV and HTML reports
docs/        Design, requirements, threat model, methods, tests and diagram drafts
evidence/    Phase records, command logs, test XML and genuine screenshots
```

## Interpretation

Scores are educational ordinal conventions, not probabilities or measured control effectiveness. The illustrative exposure index changes from 228 to 27 with all controls; overlapping paths are not independent incidents. Controls affect explicitly matched conditions. MFA does not automatically prevent social approval or existing-session reuse.

The model excludes temporal state, AND/OR prerequisites, repeated-node attacks and mechanisms absent from the input. Zero paths does not establish real-world security. See [limitations](docs/limitations/assumptions-and-limitations.md) and [reference alignment](docs/methodology/reference-alignment.md). Student review, understanding and the university demonstration remain separate from tool execution.
