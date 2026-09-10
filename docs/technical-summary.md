# SITAS technical summary

SITAS is an offline Python application that models identity attack paths in the fictional Sunhaven Care environment. It validates synthetic JSON, constructs each scenario's graph, enumerates attack paths, calculates ordinal risk, applies explicit security-control rules and compares the result. JSON, CSV and HTML exports preserve the explanation behind each finding.

The current dataset contains 47 nodes, 56 directed transitions, seven protected assets, three workstations, ten scenarios and nine controls. The [recorded scenario execution](../evidence/07-control-simulation/scenario-results.json) found 15 baseline paths. All controls together blocked 12 and left three, with two reduced and one unchanged. The sum of ordinal scores changed from 228 to 27. These numbers describe the supplied model and its assumptions.

## Data and graph implementation

[model_loader.py](../src/model_loader.py) reads local JSON using strict schemas and converts it to dataclass records. It rejects duplicate JSON keys, unsupported fields, unknown references, invalid IDs, non-finite numbers, boolean scores and unsupported control actions. Files are limited to 2 MiB; node, edge and other collection sizes are bounded. Protected assets have an integer impact from 1 to 5. Nested node attributes are copied into immutable mappings and tuples.

[graph_engine.py](../src/graph_engine.py) stores immutable ID indexes and adjacency tuples sorted by edge ID. Its directed multigraph retains distinct edges with the same source and destination. Each scenario selects allowed edge IDs from the shared synthetic environment and supplies a known source and protected target. Iterative topological elimination provides cycle inspection, while scenario traversal handles cycles directly.

## Path discovery

[pathfinder.py](../src/pathfinder.py) uses iterative depth-first search. A stack of adjacency iterators stores the current route. A visited-node set belongs to that route: backtracking removes the departing node so another route can legitimately pass through it. This prevents cycles without suppressing alternatives that converge on the same node. The target ends a path, and paths never revisit a node.

Default bounds are 12 edges per path, 10,000 paths and 100,000 examined outgoing edges. Maximum depth limits the declared analysis scope and records excluded extensions. Exceeding the path or expansion budget raises `SearchLimitError`, so an incomplete resource-limited search cannot be reported as a complete result. The work counter includes attempted cycle and depth-pruned transitions.

Canonical identity is the complete ordered edge-ID sequence. A display path ID uses the prefix `SITAS-AP-` and the first 16 hexadecimal characters of its SHA-256 digest. Comparisons use the complete sequence, not the shortened digest. Parallel transitions therefore remain distinct even if their node sequences are equal.

## Risk calculation

[risk_engine.py](../src/risk_engine.py) assigns path likelihood as the minimum ordinal likelihood among its edges and takes impact from the protected target. The product is classified using the configured ranges.

| Severity | Score range |
| --- | --- |
| Low | 1–4 |
| Medium | 5–9 |
| High | 10–16 |
| Critical | 17–25 |

For scenario 06, all baseline edges have likelihood 4 and target impact is 4: the score is 16 High. The MFA approval rule caps one edge at 2, so the path becomes 2 × 4 = 8 Medium. This bottleneck convention is explainable and deterministic. It is not a multiplication of probabilities and is not statistically calibrated.

## Security controls

[control_engine.py](../src/control_engine.py) matches each rule's tag against an edge and, when provided, matches its target selector against the edge destination. A block removes that transition from the controlled graph. A cap sets its likelihood to the minimum of the original value and all applicable caps. Blocking takes precedence. Selection order and duplicate selections do not compound reductions, and the baseline graph remains unchanged.

| Configured control | ID | Implemented graph rule |
| --- | --- | --- |
| Multi-factor authentication | `mfa` | Block `password_only`; cap `mfa_social_engineering` at 2 |
| Role-based access control | `rbac` | Block `excessive_privilege` |
| Account disablement | `account_disablement` | Block `stale_identity` |
| Idle session timeout | `session_timeout` | Block `stale_session` |
| Session revocation | `session_revocation` | Block `session_token` |
| Individual staff accounts | `individual_accounts` | Block `shared_account` |
| Privileged reauthentication | `privileged_reauthentication` | Cap `privileged_operation` at 2 |
| Administrator restriction | `admin_restriction` | Block `unrestricted_admin` |
| Device-session separation | `device_session_separation` | Block `cross_device_session` |

These are the rules in [controls.json](../config/controls.json). Current configured rules apply by tag; the engine also supports target selectors. Each matched rule records its original likelihood, individual effect and reason. The combined graph applies the strongest cap or a block, so per-rule explanations remain distinguishable from the final combined value.

## Comparison and remaining exposure

[comparison_engine.py](../src/comparison_engine.py) enumerates baseline and controlled graphs separately, matches complete ordered edge sequences and classifies every baseline finding as blocked, reduced or unchanged. Blocked findings retain their original score, route, affected edges and control reasons; their residual score is absent. Surviving paths are rescored, and a matched rule can leave path risk unchanged if it does not lower the path minimum.

The three remaining paths illustrate specific assumptions. Scenario 06 retains the capped MFA approval route at 8. Scenario 08 assumes an already-controlled authorised agency operator whose necessary delegated access remains at 9. Scenario 10 assumes misuse of a required support-export role, with final reauthentication reducing its score from 15 to 10. Full explanations and per-scenario figures are in the [scenario catalogue](threat-model/attack-scenarios.md).

Counts reconcile as baseline = blocked + remaining and remaining = reduced + unchanged. Summed scores and their percentage change are educational indices. Paths can share transitions and assets, so these totals are not additive real-world incident probabilities or financial loss estimates.

## Reports and reproducibility

[sitas.py](../src/sitas.py) exposes the `analyse` API and command line. Inputs, selected controls/scenarios and search bounds determine the semantic result. Reports record an input fingerprint, an engine fingerprint, a simulation ID and a timezone-aware generation timestamp. The timestamp is excluded from simulation identity. Fixing it allows byte comparisons of exports for identical source, input and settings.

[report_generator.py](../src/report_generator.py) writes these files under the selected output directory, which defaults to `reports`:

- `json/sitas-findings.json`, containing structured findings and run metadata.
- `csv/sitas-findings.csv`, containing one finding per row with structured fields serialised as JSON and formula-like spreadsheet values neutralised.
- `html/sitas-threat-assessment.html`, containing comparison, ordered transitions, per-rule reasons, remaining-risk ranking, bounds, assumptions and limitations.

The HTML report escapes input text and contains no scripts or required remote resources. Output content is rendered before writing; temporary files are staged and each destination is replaced atomically. Replacement is per file rather than one transaction across all three formats, so a replacement failure can leave complete files from different runs. Such a failure returns an error.

## Execution evidence

The [Phase 7 execution log](../evidence/logs/phase07-all-scenarios.txt) and [scenario test log](../evidence/logs/phase07-scenario-tests.txt) support the scenario figures and 19 passing scenario acceptance tests at commit [c080687](https://github.com/sayami1987/sunhaven-sitas-threat-simulator/commit/c080687f87bf8b9621837a02af59b4f283c549e1). The [Phase 8 report and CLI test log](../evidence/logs/phase08-final-report-tests.txt) records 48 passing tests covering exports, report safety, command execution and reproducibility. These are recorded phase results, not a claim about an unexecuted later revision.

The simulator runs using Python 3.11 or later and the standard library. Pytest is used for development verification. Its principal limitations are the authored graph assumptions, simple-path abstraction, ordinal scoring convention and declared search bounds; [assumptions and limitations](limitations/assumptions-and-limitations.md) explains those constraints.
