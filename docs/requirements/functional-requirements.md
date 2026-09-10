# SITAS functional requirements

These requirements define the observable behaviour of the offline Sunhaven Identity Threat and Attack-Path Simulator. IDs preserve the project brief's FR-01 to FR-24 numbering. Acceptance criteria describe checks to perform; they are not recorded test results.

| ID | Requirement | Acceptance criteria |
| --- | --- | --- |
| FR-01 | Load environment configuration. | A valid local JSON environment produces an identified synthetic model containing nodes and edges. Missing or unreadable files produce errors. |
| FR-02 | Validate environment structure. | Reject missing required fields, wrong types, duplicate IDs, unsupported values, invalid endpoints and scores outside 1 to 5 before traversal. |
| FR-03 | Load scenario definitions. | Read scenario ID, title, source, target and allowed edge IDs. Reject missing fields and unknown references. |
| FR-04 | Create a directed graph. | Construct directed adjacency from selected edges; traversal follows source-to-target direction only. |
| FR-05 | Add nodes and relationships. | Preserve all validated node and edge IDs, including distinct parallel edges; expose enough structure to inspect the resulting graph. |
| FR-06 | Select attack source. | Resolve the source specified by the selected scenario and reject an unknown source. |
| FR-07 | Select protected target. | Resolve the selected scenario's protected asset and its impact; reject an invalid target or source-equals-target scenario. |
| FR-08 | Discover valid attack paths. | Return ordered simple paths using iterative DFS, including alternatives and parallel-edge paths, without duplicate edge sequences; return zero for a valid unreachable target. |
| FR-09 | Prevent infinite graph traversal. | Avoid revisiting nodes within a path, apply an explicit maximum depth in edges, and fail clearly on resource exhaustion instead of reporting partial results as complete. |
| FR-10 | Calculate likelihood. | Assign each discovered path the minimum ordinal likelihood of its traversed edges. |
| FR-11 | Calculate impact. | Assign the impact configured for the protected target asset, validated as an integer from 1 to 5. |
| FR-12 | Calculate risk score. | Compute path likelihood multiplied by target impact; preserve the operands in the finding. |
| FR-13 | Classify severity. | Map scores to Low 1–4, Medium 5–9, High 10–16 and Critical 17–25; reject incompatible risk configuration. |
| FR-14 | Load security controls. | Validate control IDs and explicit tag/target match rules, supported block or cap actions, explanations and cap values. |
| FR-15 | Apply control rules. | Apply only matching selected rules; block transitions or cap likelihood using the minimum of applicable caps; repeated or reordered controls preserve the result. |
| FR-16 | Identify blocked paths. | Retain baseline paths removed by controls and explain their affected edge IDs, controls and blocking reasons. |
| FR-17 | Recalculate remaining exposure. | Enumerate the controlled graph independently and rescore surviving paths using effective edge likelihoods. |
| FR-18 | Compare before and after results. | Match paths by ordered edge IDs and scenario; classify blocked, reduced and unchanged outcomes with baseline and remaining values. |
| FR-19 | Export a JSON report. | Write structured run metadata, scenarios, summary metrics, ordered path findings, control explanations and modelling limitations. |
| FR-20 | Export a CSV report. | Write a consistent header and one row per finding, preserving IDs, scores and outcomes; quote fields correctly and protect formula-like text. |
| FR-21 | Generate an HTML report. | Produce a local SITAS Threat Assessment Report with readable summary/comparison tables, path explanations, recommendations and limitations; escape input-derived markup. |
| FR-22 | Produce clear errors for invalid inputs. | Distinguish validation or search failure from a valid zero-path run; return an unsuccessful result for malformed input and resource exhaustion. |
| FR-23 | Run multiple scenarios. | Execute a selected collection of valid scenario files with independent scenario context and produce aggregate and per-scenario results. |
| FR-24 | Generate summary metrics. | Report baseline, blocked, remaining, reduced and unchanged path counts, severity distributions and highest-risk paths; verify count reconciliation. |

The ten scenario topics are defined in [Attack scenarios](../threat-model/attack-scenarios.md). The [system design](../design/system-design.md) fixes graph, path identity, scoring and control semantics. Actual source functions, test outcomes and evidence should be mapped separately when those artefacts exist.
