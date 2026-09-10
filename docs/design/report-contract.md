# Report contract

`src.sitas.analyse` validates local inputs and produces one result dictionary before any output is written. `src.report_generator` formats that result as JSON, CSV and HTML. `python -m src.sitas` is the command-line entry point; `scripts/generate_reports.py` provides the same interface from any working directory.

The default output files are `reports/json/sitas-findings.json`, `reports/csv/sitas-findings.csv` and `reports/html/sitas-threat-assessment.html`. `--output` selects a different output root. `--controls all`, `--controls none`, or comma-separated IDs select rules. Repeat `--scenario scenario_01` to select scenarios. `--list-scenarios` displays their IDs without writing a report.

## Provenance and repeatability

JSON schema version 1 records the simulation ID, generation timestamp, input fingerprint, source fingerprint, environment, selected scenarios and controls, bounds, summary, findings, names, assumptions, limitations and references. SHA-256 fingerprints identify the validated input snapshot and the UTF-8 source modules with normalised line endings. The simulation ID incorporates those fingerprints and settings. It excludes the generation timestamp. Input JSON whitespace does not affect identity; list ordering remains part of the snapshot.

The default timestamp is actual UTC time. `--timestamp` accepts an explicitly supplied timezone-aware ISO timestamp and normalises it to UTC for a reproducibility experiment. A supplied timestamp is metadata chosen by the caller; it is not independent evidence of execution time. Execution logs contain actual start and finish times. Repeat runs with identical source, validated input, options and fixed timestamp should produce byte-identical exports.

## Findings and risk interpretation

Each finding retains its scenario and path IDs, source and target, ordered node and edge IDs, edge descriptions, original/effective edge likelihoods, path length, baseline likelihood, impact, score and severity. It includes relevant and applied controls, blocked edges, rule effects, outcome, explanation and recommendation. The top-level likelihood, impact, riskScore and severity fields always describe the baseline. `residual` is null for a blocked path, rather than a fictitious zero-risk surviving path.

Each `controlEffects.afterLikelihood` describes that individual rule's effect against the original edge. Each `edgeDetails.controlledLikelihood` is the aggregate result after all selected rules: null for any matching block, otherwise the minimum original likelihood and matching caps. This distinction exposes both the reason and the effective operand.

Scenario and aggregate counts reconcile as baseline = blocked + remaining, and remaining = reduced + unchanged. Severity counts are separate for baseline and remaining paths. Summed ordinal exposure is an illustrative comparison index; shared scenario transitions can be counted repeatedly. Neither an index nor its percentage reduction estimates real incident probability.

## Failure and display behaviour

The CLI returns exit code 2 with an ERROR message for input, search or file-system errors. A validation or search failure happens before report writing. An existing output directory can therefore still contain an older successful report after a failed run; its simulation ID and timestamp must be checked. A zero-path analysis within the declared depth bound is a valid result, with depth-pruning counters retained.

HTML escapes input-derived text and is self-contained without scripts, external styles or network-loaded assets. References are optional links a reader may choose to open. CSV quotes structured fields and neutralises formula-like text before spreadsheet use. JSON preserves the original text data. These are intentional representation differences, not different analyses.

All formats are rendered before writing and staged in destination directories. Each replacement is atomic at the file level. Replacing three files is not a single file-system transaction: interruption or a later replacement failure may leave files from different runs. Compare simulation metadata and rerun successfully before relying on an interrupted export.
