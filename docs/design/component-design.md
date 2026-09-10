# SITAS component design

SITAS separates model validation, graph traversal, risk calculation, control effects and report formatting so each rule can be understood and tested directly. This design specifies responsibilities and invariants; function names and execution evidence should be recorded against the final source in the traceability documents.

## Component responsibilities

| Component | Source module | Inputs | Outputs and responsibilities |
| --- | --- | --- | --- |
| Application coordinator | `src/sitas.py` | Local paths and run options | Validates options, orchestrates scenarios, reports errors and chooses output locations |
| Model loader | `src/model_loader.py` | JSON environment, controls, risk configuration and scenarios | Validated dataclasses; actionable input errors; no executable input expressions |
| Graph engine | `src/graph_engine.py` | Validated nodes, edges and scenario edge selection | Directed multigraph with stable edge ordering and preserved parallel transitions |
| Pathfinder | `src/pathfinder.py` | Graph, source, target and bounds | Ordered simple paths; stable identity; explicit resource-exhaustion errors |
| Risk engine | `src/risk_engine.py` | Path edges, target impact and risk configuration | Ordinal likelihood, impact, product and severity |
| Control engine | `src/control_engine.py` | Baseline graph and selected rules | Controlled graph and effect records identifying rules, edges and reasons |
| Comparison engine | `src/comparison_engine.py` | Baseline and controlled paths and scores; effect records | Blocked/reduced/unchanged findings and reconciled summary metrics |
| Report generator | `src/report_generator.py` | One completed analysis result | Equivalent JSON, CSV and HTML representations with escaped display data |

## Data objects

Nodes contain a stable ID, name, type and security attributes. Protected assets carry impact. Edges contain their own stable ID, source, target, relationship, likelihood, explicit security tags and an explanation. Scenarios contain a stable ID and title, source and protected target references, and the allowed edge IDs. Controls contain a stable ID, description and transparent match/action rules.

A path contains ordered node and edge IDs. A finding adds scenario identity, title, baseline risk, remaining risk or blocked state, relevant and applied controls, affected edges, explanation and recommendation. A report result adds the environment, selected scenarios, run settings, generation metadata and summary metrics. Internal Python names may differ from exported JSON field names; serializers should preserve a documented external schema.

## Invariants

- Node, edge, scenario and control IDs are stable and unique within their collections.
- Every graph edge resolves to two known nodes and each scenario references only known edges.
- Multiple edges between the same pair of nodes remain individually addressable.
- Simple paths never revisit a node, and their length equals their edge count.
- Canonical path identity uses ordered edge IDs, not a set of nodes or a traversal counter.
- Likelihood and impact are integer ordinal values in the range 1 to 5; booleans are not valid scores.
- A control cap cannot increase likelihood. Blocking removes a transition from controlled traversal.
- The baseline representation survives control application unchanged.
- Baseline path count equals blocked plus remaining; remaining equals reduced plus unchanged.
- Report summaries and individual findings derive from the same analysis object.

## Traversal contract

The iterative DFS explores adjacency in stable edge-ID order and carries a separate visited-node set for each candidate path. On reaching the target it records that path and stops extending it. At maximum depth it stops expansion because longer paths are outside the declared bound. A separate resource limit aborts analysis when the search would exceed supported work or output volume. Callers must propagate that error rather than write a successful complete report.

The algorithm enumerates paths, so worst-case work can grow exponentially with the model's connectivity. The intended datasets are small teaching models. Iteration avoids dependence on the Python recursion limit but does not remove the need for bounded search.

## Control composition contract

Rules identify edge tags and, where configured, the edge destination or target selector. Matching is explicit; display names do not trigger controls. The original edge and all matching rules provide the audit explanation. For a surviving edge, the effective likelihood is the minimum of its original value and all matching caps. Any matching block rule makes it unavailable for traversal. Sorting effect records provides repeatable output independently of control input order.

A path disappears if any of its transitions is blocked. Its retained finding must identify the affected edge and the matching control reason. A control may match an edge without lowering the path's minimum likelihood; the comparison engine must distinguish a recorded control effect from an actual lower risk score.

## Error and output contract

The loader owns file and schema errors; the pathfinder owns search-limit errors; the coordinator translates these into clear unsuccessful command results. Output writers should fail visibly if a destination cannot be written. Exported text is data: HTML must escape markup and CSV must neutralise text that spreadsheet applications could interpret as formulas. Generated reports include the bounds and modelling limitations so a user can interpret zero-path or blocked-path results correctly.

## Verification focus

Tests should use small handcrafted graphs whose expected paths can be enumerated independently. Include parallel edges, cycles, disconnected targets, depth boundaries, resource exhaustion, invalid references, ordinal score boundaries, duplicate controls, reversed control order and fresh versus stale session tags. Integration checks should compare the three report representations and verify that repeating a run preserves semantic results. Record outcomes only after executing those checks.
