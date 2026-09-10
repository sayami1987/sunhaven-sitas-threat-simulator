# SITAS component design

Implemented modules separate validation, graph traversal, ordinal risk, control effects, comparison and formatting. Internal Python names use snake_case; serializers preserve documented camelCase result fields.

## Components and public contracts

| Module | Callable or record | Implemented contract |
| --- | --- | --- |
| `src/models.py` | `Node`, `Edge`, `Environment`, `Scenario`, `Rule`, `Control`, `SeverityBand`, `RiskModel` | Frozen dataclasses. Node attributes are copied and recursively frozen. `ModelError` identifies invalid/ambiguous model operations. |
| `src/model_loader.py` | `load_environment(path)`, `load_controls(path, env)`, `load_risk_model(path)`, `load_scenarios(directory, env)` | Return Environment, control tuple, RiskModel or scenario tuple. `validate_environment`, `validate_controls`, `validate_risk_model` and `validate_scenario` accept parsed data. |
| `src/graph_engine.py` | `Graph(nodes, edges)`, `build_graph(env, scenario=None)` | Sorted read-only maps and adjacency tuples; scenario graphs keep every environment node but only selected edges. Duplicate IDs, unknown endpoints and invalid likelihoods raise ModelError. |
| `src/pathfinder.py` | `find_paths(graph, source, target, *, max_depth=12, max_paths=10000, max_expansions=100000)` | Returns frozen `SearchResult(paths, expansions, depth_pruned)` or raises `SearchLimitError`, a ModelError subclass. Each AttackPath contains id, node_ids and edge_ids. |
| `src/risk_engine.py` | `calculate_likelihood(values)`, `classify_severity(score, model)`, `score_path(graph, path, model)`, `rank_paths(graph, paths, model)` | Minimum ordinal, severity, validated RiskScore, and tuple of `(path, score)` pairs ordered by descending risk then path ID. RiskScore serializes likelihood, impact, riskScore and severity. |
| `src/control_engine.py` | `apply_controls(graph, controls, selected_ids)` | Frozen ControlResult containing new graph, effect tuple and sorted selected_ids. Baseline remains unchanged. |
| `src/comparison_engine.py` | `compare_scenario(env, scenario, risk_model, controls, selected_ids, *, max_depth=12, max_paths=10000, max_expansions=100000)` | Runs both searches, scores/matches paths and returns metadata, summary, findings and search counters. `summarize(findings)` aggregates supplied records. |
| `src/report_generator.py` | `render_json(result)`, `render_csv(result)`, `render_html(result)` | Pure string formatting. `write_reports(result, output_dir)` stages/replaces outputs and returns a format-to-Path dictionary after success. |
| `src/sitas.py` | `analyse(...)`, `main(argv=None)` | Validates inputs/options, runs scenarios and adds provenance. Analyse writes no reports. Main runs the CLI and returns 0 on success or 2 for model/search/filesystem errors. |

## Coordinator options

`analyse` accepts keyword-only `environment_path`, `controls_path`, `risk_path`, `scenario_dir`, `controls`, `scenario_ids`, `max_depth`, `max_paths`, `max_expansions` and `timestamp`. Default paths resolve from the repository. Controls are `all`, `none` or comma-separated IDs, deduplicated and sorted. `scenario_ids` is None or a nonempty list/tuple of strings; selected scenarios retain stable ID order. Every directory scenario is validated before filtering.

The result contains schemaVersion, title, generatedAt, simulationId, input/engine fingerprints, environment, settings, scenario results, flat findings, summary, node names, selected control descriptions, assumptions, limitations and references. Settings include selected controls, scenario IDs and all three bounds.

The CLI defaults to `reports` as output root and exposes matching input, selection, bound and timestamp options. `--list-scenarios` validates environment/scenario inputs and lists them without creating reports.

## Loader limits and canonical values

| Constraint | Enforced limit or meaning |
| --- | --- |
| Input file | At most 2 MiB per JSON file, with a one-byte oversize check; UTF-8, including optional BOM. |
| Schema | Integer schema_version 1, exact required/optional fields, no unsupported fields or duplicate JSON object keys; non-finite constants rejected. |
| IDs | `^[A-Za-z][A-Za-z0-9_-]{0,79}$`; collection IDs and all rule IDs unique. |
| Environment | synthetic is exactly true; 1-500 nodes, 0-5,000 edges; known endpoints. |
| Node types | attacker, actor, identity, credential, session, workstation, application, privilege, asset, authentication_factor. |
| Scores | Edge likelihood and asset impact: integer 1-5, excluding booleans and floating-point alternatives. |
| Attributes | JSON-compatible data, nonempty string keys/text, finite numbers, maximum depth 32 and 10,000 visited values per node-attribute tree. |
| Tags | At most 100 distinct valid tags per edge. |
| Scenarios | 1-1,000 JSON files; at most 5,000 distinct known edges each; known distinct source/target; target is an asset. Empty-edge or disconnected scenarios are valid. |
| Controls | 0-100 controls; at least one rule per control and at most 1,000 total rules. Tags exist in the full environment; target selectors hold at most 500 distinct known node IDs. |
| Actions | block has no cap field; cap requires an integer 1-5. |
| Risk model | minimum likelihood and exactly Low 1-4, Medium 5-9, High 10-16, Critical 17-25. |

The loader sorts records by ID and tag/target/selected-edge tuples by identifier. Fingerprinting normalises dictionary order; ordered attribute arrays retain their meaning. These limits bound inputs, not the total cost of every allowed multi-scenario run.

## Graph and traversal details

`Graph.outgoing(node_id)` returns its adjacency tuple or raises ModelError for an unknown node. `Graph.has_cycle()` uses iterative Kahn elimination. `Graph.summary()` reports nodes, edges, isolated nodes, endpoint pairs with parallel edges, and cycle presence. Parallel mechanisms keep distinct edge IDs.

DFS uses adjacency iterators and a visited set maintained by current-path backtracking. It is iterative and does not apply a global visited set that would remove independent alternatives. Returned paths sort by ordered edge-ID tuples; `path_id(edge_ids)` hashes that tuple, while finding identity also includes scenario ID.

Defaults are **12 edges, 10,000 paths and 100,000 expansions per scenario per graph search**. Accepted bounds are 1-500 edges, 1-100,000 paths and 1-1,000,000 expansions. Each examined outgoing edge counts as an expansion, including one then rejected for a cycle or depth. A depth-rejected extension increments depth_pruned. Exceeding path/expansion budgets raises an error rather than returning partial results.

## Risk, control and finding contracts

`score_path` checks ordered node/edge correspondence, simple-path uniqueness, graph membership, a nonempty edge sequence and an asset target with valid impact. Likelihood is minimum edge ordinal and risk is likelihood times impact: a bottleneck ranking convention, not a probability or conservative mathematical bound.

The control engine validates supplied action/cap values even for unselected or unmatched rules. It rejects unknown selected IDs. Matching uses a tag and, if nonempty, the edge's **target-node** selector. A globally valid tag absent from a scenario is simply unmatched. All effects remain sorted by edge/control/rule ID, including caps hidden by a block or caps that leave the original value unchanged.

`ControlEffect.to_dict()` exports edgeId, controlId, ruleId, action, reason, beforeLikelihood and afterLikelihood. The last value is the rule's own `min(original, cap)` or null for a block. Finding `edgeDetails`, in path order, contains source, target, relationship, explanation, baselineLikelihood and **combined** controlledLikelihood. Any block gives null; otherwise combination uses the minimum original value and caps.

Comparison asserts that controls introduce no new path tuple or risk increase and that every disappeared path has a recorded blocking transition. Findings sort by descending baseline risk then path ID. Top-level likelihood/impact/riskScore/severity always describe the baseline; residual is null for blocked findings. controlsRelevant includes matching catalogue controls; controlsApplied contains selected matching controls. Counts and exposure derive from those findings.

## Exports and provenance

Names beneath the output root are `json/sitas-findings.json`, `csv/sitas-findings.csv` and `html/sitas-threat-assessment.html`. UTF-8 JSON preserves structured data. CSV retains compact JSON fields, flattened risk and formula-neutralised scalar text. HTML escapes text/attributes and contains no scripts or remote assets; finding articles expose escaped data-finding-id attributes.

All rendering precedes directory/file operations, and all staging precedes replacements. `os.replace` is atomic for each file, not the set. Failure can preserve older reports or leave complete files from different runs. CSV repeats simulationId/generatedAt per finding; zero findings yield only its header. JSON and HTML retain metadata even when empty.

The input hash covers validated environment, all configured controls, risk and selected scenarios. The engine hash covers direct `src/*.py` source texts with normalised line endings. The simulation ID combines those hashes with settings, excluding timestamp. These are provenance aids, not signatures or verification of interpreter/dependencies. See [Report contract](report-contract.md).

## Verification boundary

Captured results are recorded separately. The [Phase 8 generation record](../../evidence/logs/phase08-report-generation.execution.json) identifies Python 3.12.14. Python 3.11+ remains the compatibility target; other-version execution and exhaustive model coverage are not established. No test outcome is inferred from this design. Native Draw.io authoring/export remains pending separately from the implemented runtime.
