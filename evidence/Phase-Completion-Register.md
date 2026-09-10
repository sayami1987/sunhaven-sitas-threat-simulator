# Phase Completion Register

Entries distinguish completed artefacts from outstanding work. Actual command
output is kept separately in `logs/`; machine-readable phase records are in
their phase evidence folders. Git hashes are recorded after each commit exists.

## Phase 01 Source review and final design

UTC: 2026-09-10T14:33:51.848807+00:00

Status: Completed. Reviewed supplied materials; defined 24 FRs, 12 NFRs, threat model and architecture; created standalone repository and two editable diagrams with PNG exports.

Notes: Approved group proposal not supplied. Diagram exports are not screenshots. GitHub repository created; first publication follows review. Student critical review and demonstration remain to be completed separately.

Evidence: `evidence/logs/phase01-toolchain.txt`, `evidence/logs/phase01-diagram-exports.txt`, `evidence/logs/phase01-folder-tree.txt`, `evidence/logs/phase01-publication-scan.txt`.

Exact file/command details: `phases/phase-01.json`. Commit recorded after creation.

Phase 01 commit: `b219b3447817f37503cf225a9c2a127c105dcf07`. Publication is verified separately in push logs.

## Phase 02 Synthetic environment and strict input validation

UTC: 2026-09-10T14:44:10.364260+00:00

Status: Completed. Created 47 synthetic nodes, 56 edges, nine controls, risk model and strict loader. 121 loader tests passed; final configuration validates.

Notes: Review found mutable node attributes; recursively froze nested data and verified mutation failures. One initial development test expected a list after the representation became a tuple; corrected the expectation. Initial environment expanded to include explicit agency-device and multistage workstation routes. Two genuine Phase1 screenshots are saved; further native capture halted on URL-verification safety failure, so remaining screenshots require manual capture.

Evidence: `evidence/logs/phase02-loader-tests.txt`, `evidence/logs/phase02-final-model-validation.txt`.

Exact file/command details: `phases/phase-02.json`. Commit recorded after creation.

Phase 02 commit: `31a36543e282cf56e5d2b09f9ee609fdf838a498`. Publication is verified separately in push logs.

## Phase 03 Directed graph construction

UTC: 2026-09-10T14:46:43.397236+00:00

Status: Completed. Implemented deterministic directed multigraph indexes, scenario edge selection, iterative cycle detection and graph inspection. 27 graph tests passed; current model has 47 nodes, 56 edges and no cycle.

Notes: Parallel edges and cycles are supported and tested using handcrafted graphs even though the supplied synthetic environment has no cycle or parallel pair.

Evidence: `evidence/logs/phase03-graph-tests.txt`, `evidence/logs/phase03-graph-output.txt`.

Exact file/command details: `phases/phase-03.json`. Commit recorded after creation.

Phase 03 commit: `ff1fe11e3e1d1ecc7fe0328fb1ba6251f6078020`. Publication is verified separately in push logs.

## Phase 04 Bounded iterative attack path discovery

UTC: 2026-09-10T14:50:21.929805+00:00

Status: Completed. Implemented iterative DFS, stable path IDs, cycle-safe backtracking, explicit depth bounds and resource-exhaustion errors. 29 tests passed including an independent BFS oracle. Actual synthetic query found two paths; depth3 found zero with14 pruned branches.

Notes: Depth pruning is a declared scope limit, not a security pass. Resource exhaustion raises an error without returning partial analysis. Native screenshots remain unavailable after the prior URL-verification stop; actual path output is saved.

Evidence: `evidence/logs/phase04-pathfinder-tests.txt`, `evidence/logs/phase04-path-output.txt`, `evidence/logs/phase04-depth-bound.txt`.

Exact file/command details: `phases/phase-04.json`. Commit recorded after creation.

Phase 04 commit: `23b784f071d7250cdc3e0898220cba8bbe200498`. Publication is verified separately in push logs.

## Phase 05 Deterministic ordinal risk scoring

UTC: 2026-09-10T14:52:47.701716+00:00

Status: Completed. Implemented minimum-edge likelihood, target impact, product, severity and stable ranking. 37 risk tests passed. Both current care-record paths score4 x5 =20 Critical in the synthetic baseline.

Notes: Scoring validates the ordered path and target impact. The ordinal model is an educational convention rather than a calibrated probability. Actual arithmetic output is saved.

Evidence: `evidence/logs/phase05-risk-tests.txt`, `evidence/logs/phase05-risk-output.txt`.

Exact file/command details: `phases/phase-05.json`. Commit recorded after creation.

Phase 05 commit: `458a67d7ea7835fad100233249fd4d3c5c44529b`. Publication is verified separately in push logs.

## Phase 06 Control simulation and exposure comparison

UTC: 2026-09-10T14:59:47.223575+00:00

Status: Completed. Implemented all nine controls and before/after comparison with exact edge/control reasons and null residuals for blocked routes. Final combined control/comparison suite passed33 tests. MFA example blocked one path and reduced the remaining path from20 to10; illustrative exposure40 to10.

Notes: An initial root test command ran before test_comparison.py existed: pytest exited4 and no tests ran; the failed collection log is retained. The final completed suite passed. Reviewed added example PDFs and NIST/SANS/ISM guidance; recorded conceptual applicability without compliance claims.

Evidence: `evidence/logs/phase06-control-comparison-tests.txt`, `evidence/logs/phase06-final-tests.txt`, `evidence/logs/phase06-control-output.txt`.

Exact file/command details: `phases/phase-06.json`. Commit recorded after creation.

Phase 06 commit: `da4a4908531d4343e88ff863fedb21642e759d1e`. Publication is verified separately in push logs.

## Phase 07 Ten synthetic attack scenarios

UTC: 2026-09-10T15:06:40.584142+00:00

Status: Completed. All ten standalone scenarios executed. Independent literal-path tests passed19. All controls:15 baseline paths,12 blocked,3 remaining;2 reduced and1 unchanged. Ordinal exposure228 to27.

Notes: Residual exposure is deliberate: MFA social approval score8, agency operator score9, and controlled export score10. These are model results, not observed incident probabilities. No new UI screenshots; real output retained.

Evidence: `evidence/logs/phase07-scenario-tests.txt`, `evidence/logs/phase07-all-scenarios.txt`, `evidence/logs/phase07-baseline-scenarios.txt`.

Exact file/command details: `phases/phase-07.json`. Commit recorded after creation.

Phase 07 commit: `c080687f87bf8b9621837a02af59b4f283c549e1`. Publication is verified separately in push logs.

## Phase 08 Command-line analysis and technical reports

UTC: 2026-09-10T15:14:02.795751+00:00

Status: Completed. Created coordinator and JSON/CSV/HTML exports with input/source fingerprints and edge-level scoring evidence.48 report/CLI tests and31 comparison/scenario regression tests passed. Actual all-control reports generated:15 baseline,12 blocked,3 remaining.

Notes: Added explicit methodology section during review; final48 report/CLI tests rerun and passed. Tests include malicious display text, formula-like CSV, fixed-time byte equality, invalid input and interrupted output replacement. New UI screenshots unavailable; actual exports and execution logs retained.

Evidence: `evidence/logs/phase08-comparison-regression.txt`, `evidence/logs/phase08-report-cli-tests.txt`, `evidence/logs/phase08-final-report-tests.txt`, `evidence/logs/phase08-report-generation.txt`, `evidence/logs/phase08-publication-scan.txt`.

Exact file/command details: `phases/phase-08.json`. Commit recorded after creation.
