# Test plan

The test strategy checks whether the offline simulator implements its stated graph and control model, produces explainable ordinal calculations and fails visibly when it cannot complete a bounded analysis. It does not measure the effectiveness of controls in a live identity service or establish real-world incident probabilities.

## Scope and independent expectations

| Layer | Test source | Independent expected result |
| --- | --- | --- |
| JSON contracts | [test_loader.py](../../tests/test_loader.py) | Handwritten valid/invalid data, duplicate JSON keys, invalid ordinals/references, byte/depth limits and immutable attributes. |
| Directed graph | [test_graph.py](../../tests/test_graph.py) | Explicit node/edge sets, direction, parallel edges, disconnected nodes and known cycle structure. |
| Path enumeration | [test_pathfinder.py](../../tests/test_pathfinder.py) | Manually enumerated chains/diamonds/cycles plus a separate breadth-first oracle on seeded tiny graphs. The oracle is not a recording of DFS output. |
| Risk | [test_risk.py](../../tests/test_risk.py) | Manual minimum-edge calculations, target impact and inclusive severity boundaries. |
| Controls | [test_controls.py](../../tests/test_controls.py) | Explicit matching tags/targets for nine controls, block dominance, minimum caps, reasons and baseline preservation. |
| Comparison | [test_comparison.py](../../tests/test_comparison.py) | Three handwritten routes yield baseline exposure 50 and controlled exposure 20; one is blocked, one reduced and one unchanged. Parallel-edge identity and unchanged bottlenecks have separate cases. |
| Ten scenarios | [test_scenarios.py](../../tests/test_scenarios.py) | Literal expected ordered edge sequences and manually calculated scores for every scenario; selected-control counterexamples retain valid alternatives. |
| Reports | [test_reports.py](../../tests/test_reports.py) | JSON equivalence; CSV row/operand reconciliation; parsed HTML finding sections and metrics; hostile data remains inert; staged-file failures preserve complete files. |
| Coordinator/CLI | [test_cli.py](../../tests/test_cli.py) | Real subprocess exit codes, selected scenarios/controls, no report publication on validation/search failure, fingerprint changes and fixed-time byte equality. |

SITAS-T01 to SITAS-T24 are acceptance anchors, not the total number of pytest cases. Parameterised cases and additional boundary tests expand the suite to **314 collected cases** at Phase 09. Collection does not execute those tests. Historical targeted execution results are recorded separately in [test results](test-results.md).

## Reproduction commands

Run commands from the repository root with the project virtual environment activated. The recorded development toolchain is Python 3.12.14 with pytest 8.4.2. Application runtime code uses the Python standard library; pytest is a development dependency. The locked development packages are in [requirements-dev-lock.txt](../../requirements-dev-lock.txt).

```text
python -m pytest --collect-only -q
python -m pytest tests/test_loader.py -q
python -m pytest tests/test_pathfinder.py tests/test_risk.py -q
python -m pytest tests/test_controls.py tests/test_comparison.py -q
python -m pytest tests/test_scenarios.py tests/test_reports.py tests/test_cli.py -q
```

The planned Phase 10 full regression command is:

```text
python scripts/capture_command.py --log evidence/logs/phase10-full-suite.txt -- python -m pytest -q --junitxml=evidence/08-testing/phase10-full-suite.junit.xml
```

The capture helper retains stdout, stderr, start/end UTC times and exit code for the full-suite command. This plan does not assert that the Phase 10 log or JUnit file exists yet. A direct alternative for a local check is `python scripts/run_tests.py -q`.

## Invariants and failure cases

- Graph edges retain their direction and ID. Different parallel edges remain different paths even when their node sequence is identical.
- DFS paths are simple, target-terminal and bounded by edge depth. Depth pruning narrows the result's scope. Path/expansion exhaustion must raise an error rather than return a partial result as complete.
- Path likelihood is the minimum edge ordinal; risk is likelihood multiplied by target impact. Both inputs are integers from 1 to 5. The severity bands are fixed by schema version 1.
- Selected controls match explicit tags and optional destination selectors. Caps only lower or retain an edge value; any block makes that edge unavailable. Control order and repeated selection must not alter the result.
- A blocked finding retains its baseline and exact reasons but has no residual score. Baseline count equals blocked plus remaining; remaining equals reduced plus unchanged.
- Report formats describe the same completed analysis. JSON preserves structured values, CSV protects formula-like text and HTML escapes text/attributes and restricts reference links to ordinary HTTP(S) URLs.
- Report replacement is atomic per file. An interruption may leave a mix of complete old/new reports; it must raise an error, retain complete bytes and remove staging files. No test should imply a transaction across the three formats.

## Evidence and release gates

Phase-specific `.txt`, `.execution.json` and JUnit files are retained under [evidence](../../evidence). Actual phase records associate results with a commit. Failed attempts remain visible alongside successful reruns. Fixed timestamps in reproducibility tests are deliberate test inputs, not the execution times of those tests.

| Gate | Acceptance evidence | Status at Phase 09 |
| --- | --- | --- |
| Targeted module/integration tests | Named test nodes, actual exit codes and phase-specific logs | Recorded through Phase 08. |
| Native Draw.io diagrams | Diagrams created and exported in Draw.io itself, with genuine workflow evidence | Pending; Phase 09 remains partial. Existing diagram files alone do not establish native creation/export. |
| Full regression | One complete final run, JUnit totals, exit 0 and tested revision | Pending Phase 10. |
| Generated report visual review | Readable summary, all findings, long paths, edge table, print layout and limitations | Pending manual/visual check; structural HTML tests already recorded. |
| Clean local demonstration | Setup, all-scenario run and report opened using only local packaged inputs | Targeted CLI runs recorded; final demonstration pending. |
| Student understanding | Student explains a valid path, a cycle, a risk calculation, a blocked path and one surviving path | Pending student action; cannot be inferred from automated tests. |
| Publication review | Current files, generated artefacts, images and complete Git history checked for private data and secrets | Current pattern scans recorded; final privacy/history review pending Phase 12. |

A test failure is investigated using its original log, corrected within scope and rerun with a new or clearly identified evidence file. Counts from repeated or overlapping runs must not be added together as if they were unique tests. Update the [requirements matrix](../requirements/requirements-traceability.md) only to the level supported by the completed check.
