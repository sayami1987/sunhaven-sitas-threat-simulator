# Development plan

Each phase creates real artefacts before a commit. Commands and outcomes are
recorded as executed; later evidence does not imply earlier completion.

| Phase | Work | Exit evidence |
| --- | --- | --- |
| 01 | Source review, requirements, architecture, threat model, initial diagrams | Documents, diagram validation, repository structure |
| 02 | Synthetic environment, controls and risk configuration, validated loader | Valid/invalid input tests |
| 03 | Directed graph and adjacency relationships | Node, edge and reference tests |
| 04 | Iterative DFS, deterministic path IDs and traversal bounds | Single/multiple/no path, cycles, depth and resource tests |
| 05 | Likelihood, target impact, product and severity | Calculation and boundary tests |
| 06 | Control rules and exposure comparison | Rule-specific block/reduction and comparison tests |
| 07 | Ten complete scenario definitions | Executed per-scenario assertions |
| 08 | JSON, CSV and HTML reports | Export integrity, escaping, cross-format consistency |
| 09 | Remaining diagrams and technical documentation | Five editable diagrams and PNG exports, traceability |
| 10 | Full automated validation | Actual pytest log and machine-readable results |
| 11 | Repeatable demonstration | Baseline/controlled output, report and screenshot evidence |
| 12 | Repository review and delivery | Privacy scan, clean Git state and verified publication status |

Source review is evidence of planning, not lecturer approval or student attendance.
Student demonstration and critical review remain separate from tool execution.
The student must review, modify as needed, rerun and understand each module.
