# SITAS nonfunctional requirements

These requirements define the qualities needed for an explainable, repeatable educational simulator. Acceptance criteria are verification obligations rather than claims of achieved results.

| ID | Requirement | Acceptance criteria |
| --- | --- | --- |
| NFR-01 | All simulation data shall be fictional or synthetic. | Fixtures, reports and examples identify their fictional context and contain no resident records, employee personal details or real credentials. |
| NFR-02 | The simulator shall run offline. | Running the analysis and opening its report requires only local files and the Python runtime; no network service or authentication step is needed. |
| NFR-03 | Analysis results shall be deterministic. | Identical validated models, scenarios, controls and limits yield identical path identities, scores, classifications and semantic ordering. |
| NFR-04 | Risk scoring shall be explainable. | Each finding exposes the ordered path, edge likelihood basis, target impact, multiplication and severity mapping; documentation identifies the ordinal convention. |
| NFR-05 | Code shall be modular. | Validation, graph construction, traversal, risk, controls, comparison and formatting have separate responsibilities and documented interfaces. |
| NFR-06 | Functions shall be testable. | Core computation accepts explicit inputs without hidden service state; automated tests cover expected outcomes and meaningful failure cases. |
| NFR-07 | Input errors shall fail safely. | Invalid input or exhausted search resources produce clear errors and no claim of a complete successful analysis; baseline data is not silently repaired or mutated. |
| NFR-08 | Secrets shall not be committed. | Repository review includes source, configuration, generated output and history; credential files, tokens and private keys are excluded. |
| NFR-09 | Outputs shall be reproducible. | Retain input/configuration identity and run options; semantic outputs agree on repeat execution. Generation timestamps are explicit metadata and may be fixed for exact export comparison. |
| NFR-10 | The implementation shall remain understandable for an undergraduate demonstration. | A presenter can trace JSON to graph, explain iterative DFS and one cycle example, calculate a score manually, and show why a rule blocks or reduces a path. |
| NFR-11 | SITAS shall execute using only its packaged Python application and local synthetic inputs. | Setup and the full demonstration run from the repository using Python 3.11 or later; no external application state or service output is required. |
| NFR-12 | Documentation shall reflect the actual implementation. | Designs are distinguished from executed results; commands, schemas, diagrams and traceability are checked against source and genuine logs before release. |

Search depth and resource bounds are part of a run's declared scope. Successful execution means the supported bounded analysis completed; it does not establish safety of a real environment. Reporting must retain that distinction.
