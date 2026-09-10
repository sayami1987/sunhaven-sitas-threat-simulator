# SITAS assumptions and limitations

SITAS provides reproducible analysis of a fictional attack graph. A result describes the selected model, scenario, control rules and search bounds. It does not establish exploitability, security or compliance of a real organisation.

## Model coverage

Nodes, transitions and their preconditions are authored assumptions. Missing or incorrectly tagged edges can hide or misrepresent exposure. The engine cannot find an attack mechanism absent from the model. Scenario edge selection deliberately narrows the analysis to a defined teaching case.

Paths are simple directed paths: they do not revisit a node. This prevents cyclic traversal but omits attacks that require repeated visits, state changes or temporal behaviour. The graph does not implement concurrent attacks, AND/OR prerequisite logic, time-dependent authentication, adversarial adaptation or a complete identity protocol.

## Search bounds

Maximum depth is measured in edges. A successful bounded run does not include paths longer than its declared limit. Separate resource limits protect the process from path explosion; exhausting them is an error rather than a complete result. Iterative DFS avoids recursion limits but path enumeration can still require exponential work on highly connected graphs.

Zero remaining paths means no modeled path was found within the reported scenario and limits. It must not be described as proof that the environment is secure.

## Risk interpretation

Likelihood is ordinal, from 1 to 5. The path uses its minimum edge likelihood as a conservative bottleneck convention. This is simple and explainable, but it ignores dependence between events, does not multiply probabilities, and does not penalise every additional attack step. The method is not statistically calibrated.

Impact is an authored target value from 1 to 5. Multiplying likelihood and impact provides a ranking indicator, with Low 1–4, Medium 5–9, High 10–16 and Critical 17–25. Numeric differences and percentages in these scores are modelling summaries, not measured changes in incident probability or expected financial loss. Some integer scores inside the severity bands cannot be produced by multiplying two integers from 1 to 5.

Path counts are also sensitive to model granularity: splitting a transition or adding parallel edges can change the count without representing an equivalent change in real exposure. Paths may share prerequisites and targets. Summed risk scores and cross-scenario totals must not be treated as independent, additive real-world risks.

## Control interpretation

Controls are explicit graph rules. A block removes a matched transition; a cap limits its ordinal likelihood. Multiple caps use the minimum, so duplicate controls do not compound a reduction. A rule that lowers a non-minimum edge may leave path risk unchanged, and its recorded effect must be distinguished from a lower path score.

Effectiveness is assumed according to tags and selectors. MFA does not inherently invalidate an existing session, timeout does not inherently block a fresh session, and an account-disablement rule applies only within its selected scope. A bypass exists only if the model includes it. A blocked path therefore means the rule's assumed prevention condition holds in this model; it does not mean the control is universally effective.

## Operational scope

SITAS consumes local synthetic JSON and emits analysis reports. It does not connect to a live identity service, authenticate workers, operate a production portal, scan a network or execute an attack. The Python runtime is sufficient for analysis; opening the local HTML report does not require hosting. Report text should consistently identify the synthetic environment.

## Evidence and reproducibility

For repeatable analysis, preserve the input files, selected scenarios and controls, software revision and search bounds. Analysis values are deterministic; generation timestamps describe when an export was created and can differ across runs. Exact file comparisons should fix metadata or compare semantic content separately.

Tests validate the implementation against defined cases and invariants. Passing tests do not validate real-world assumptions or establish exhaustive coverage of all possible input models. Screenshots, logs, reports and commit references must come from actual work; a design target or expected outcome must not be presented as an executed result.
