# Test results

This is the Phase 09 evidence snapshot. Targeted suites have executed successfully through Phase 08. **The final full-suite regression is pending Phase 10.** A Phase 09 collection check returned 314 cases; collection alone is not a test execution result.

**Phase 09 is partial.** The required native Draw.io creation and export workflow remains pending. Public diagram files are editable XML drafts; earlier custom PNG exports and their exporter have been removed from the public working tree. Those earlier exports are not evidence of native Draw.io creation/export.

Results below come from retained command output and [phase records](../../evidence/phases). UTC times are taken from the execution metadata, not from fixed timestamps used as report-test inputs. Phase commit hashes identify the commits containing the relevant implementation and recorded evidence; tests were run while preparing those commits.

## Executed targeted suites

| Phase | Scope | Actual result | Finished UTC | Log and machine-readable evidence |
| --- | --- | --- | --- | --- |
| 02 | Loader contracts | **121 passed**, exit 0 | 2026-09-10 14:42:16 | [Log](../../evidence/logs/phase02-loader-tests.txt), [execution](../../evidence/logs/phase02-loader-tests.execution.json), [JUnit](../../evidence/08-testing/phase02-loader.junit.xml) |
| 03 | Directed graph | **27 passed**, exit 0 | 2026-09-10 14:46:25 | [Log](../../evidence/logs/phase03-graph-tests.txt), [execution](../../evidence/logs/phase03-graph-tests.execution.json), [JUnit](../../evidence/08-testing/phase03-graph.junit.xml) |
| 04 | Iterative DFS | **29 passed**, exit 0 | 2026-09-10 14:50:08 | [Log](../../evidence/logs/phase04-pathfinder-tests.txt), [execution](../../evidence/logs/phase04-pathfinder-tests.execution.json), [JUnit](../../evidence/08-testing/phase04-pathfinder.junit.xml) |
| 05 | Risk scoring | **37 passed**, exit 0 | 2026-09-10 14:52:25 | [Log](../../evidence/logs/phase05-risk-tests.txt), [execution](../../evidence/logs/phase05-risk-tests.execution.json), [JUnit](../../evidence/08-testing/phase05-risk.junit.xml) |
| 06, initial attempt | Requested controls/comparison suite before comparison test file existed | **No tests ran**, exit 4; collection failed | 2026-09-10 14:57:02 | [Retained failure log](../../evidence/logs/phase06-control-comparison-tests.txt), [execution](../../evidence/logs/phase06-control-comparison-tests.execution.json), [JUnit](../../evidence/08-testing/phase06-control-comparison.junit.xml) |
| 06, completed suite | Controls and comparison | **33 passed**, exit 0 | 2026-09-10 14:58:10 | [Successful log](../../evidence/logs/phase06-final-tests.txt), [execution](../../evidence/logs/phase06-final-tests.execution.json), [JUnit](../../evidence/08-testing/phase06-final.junit.xml) |
| 07 | Ten scenarios and counterexamples | **19 passed**, exit 0 | 2026-09-10 15:06:22 | [Log](../../evidence/logs/phase07-scenario-tests.txt), [execution](../../evidence/logs/phase07-scenario-tests.execution.json), [JUnit](../../evidence/08-testing/phase07-scenarios.junit.xml) |
| 08 | Comparison/scenario regression after adding edge-level reporting data | **31 passed**, exit 0 | 2026-09-10 15:10:59 | [Log](../../evidence/logs/phase08-comparison-regression.txt), [execution](../../evidence/logs/phase08-comparison-regression.execution.json), [JUnit](../../evidence/08-testing/phase08-comparison.junit.xml) |
| 08, initial report suite | Reports and CLI | **48 passed**, exit 0 | 2026-09-10 15:12:56 | [Log](../../evidence/logs/phase08-report-cli-tests.txt), [execution](../../evidence/logs/phase08-report-cli-tests.execution.json), [JUnit](../../evidence/08-testing/phase08-report-cli.junit.xml) |
| 08, final report suite | Reports and CLI after methodology-section review | **48 passed**, exit 0 | 2026-09-10 15:13:39 | [Final log](../../evidence/logs/phase08-final-report-tests.txt), [execution](../../evidence/logs/phase08-final-report-tests.execution.json), [JUnit](../../evidence/08-testing/phase08-final-report.junit.xml) |

These runs overlap. Their counts must not be added together as a single unique-test total or described as one final regression run. The Phase 06 initial failure was a missing test-file collection error, not a failed simulation assertion; its subsequent successful 33-case run is recorded separately. Phase 02 notes also document correcting an early expectation from list to tuple after attributes were made immutable; the retained formal loader run above passed.

## Commit associations

| Phase | Recorded commit | Record |
| --- | --- | --- |
| 01 | `b219b3447817f37503cf225a9c2a127c105dcf07` | [Phase 01](../../evidence/phases/phase-01.json) |
| 02 | `31a36543e282cf56e5d2b09f9ee609fdf838a498` | [Phase 02](../../evidence/phases/phase-02.json) |
| 03 | `ff1fe11e3e1d1ecc7fe0328fb1ba6251f6078020` | [Phase 03](../../evidence/phases/phase-03.json) |
| 04 | `23b784f071d7250cdc3e0898220cba8bbe200498` | [Phase 04](../../evidence/phases/phase-04.json) |
| 05 | `458a67d7ea7835fad100233249fd4d3c5c44529b` | [Phase 05](../../evidence/phases/phase-05.json) |
| 06 | `da4a4908531d4343e88ff863fedb21642e759d1e` | [Phase 06](../../evidence/phases/phase-06.json) |
| 07 | `c080687f87bf8b9621837a02af59b4f283c549e1` | [Phase 07](../../evidence/phases/phase-07.json) |
| 08 | `eb96fecbf82cd4304b765eca73750c24039e82f6` | [Phase 08](../../evidence/phases/phase-08.json) |

## Current collection inventory

`python -m pytest --collect-only -q` reported **314 tests collected in 0.33 seconds**, exit 0, in the captured Phase 09 check. See the [collection log](../../evidence/logs/phase09-test-collection.txt) and [execution metadata](../../evidence/logs/phase09-test-collection.execution.json). The inventory is:

| Module | Collected cases |
| --- | ---: |
| `tests/test_loader.py` | 121 |
| `tests/test_graph.py` | 27 |
| `tests/test_pathfinder.py` | 29 |
| `tests/test_risk.py` | 37 |
| `tests/test_controls.py` | 21 |
| `tests/test_comparison.py` | 12 |
| `tests/test_scenarios.py` | 19 |
| `tests/test_reports.py` | 26 |
| `tests/test_cli.py` | 22 |
| **Total** | **314** |

The Phase 01 toolchain evidence records Python **3.12.14**, pytest **8.4.2** and Pillow **12.3.0**. Only the first two are needed to run the automated test suite. Pillow was present in the historical toolchain; it does not establish native Draw.io creation or export. The available runtime used for testing was the repository's `.venv`.

## Observed simulation and report checks

- The supplied environment validates with **47 nodes, 56 edges and nine controls**. Cycle and parallel-edge behaviours are tested with handcrafted graphs; the supplied main environment itself has no cycle or parallel pair.
- The ten-scenario acceptance run yields **15 baseline paths, 12 blocked, three remaining, two reduced and one unchanged**. Baseline ordinal exposure is **228** and residual exposure is **27**. These totals are based on scenario-path records, which can share relationships and assets. See [actual scenario output](../../evidence/logs/phase07-all-scenarios.txt) and [scenario results](../../evidence/07-control-simulation/scenario-results.json).
- The residual routes are deliberate model outcomes: social approval score **8**, agency operator score **9** and controlled export score **10**. A blocked route has a `null` residual, not a Low classification or a fabricated zero-likelihood path.
- Phase 08 generated the actual [JSON](../../reports/json/sitas-findings.json), [CSV](../../reports/csv/sitas-findings.csv) and [HTML](../../reports/html/sitas-threat-assessment.html) reports; see [generation log](../../evidence/logs/phase08-report-generation.txt). The report suite checked cross-format values, actual edge operands, escaped markup/URLs, spreadsheet formula handling, fixed-time equality and output-write failures.
- The Phase 08 [publication pattern scan](../../evidence/logs/phase08-publication-scan.txt) reported **196 files and zero flagged file/pattern matches**. Its scope is Git-visible current files. It does not establish that every secret or private detail is absent and does not substitute for history review.

## Phase 10 full regression — pending

| Field | Status |
| --- | --- |
| Full-suite execution | Pending; no final suite pass claimed in this snapshot. |
| Expected collection before further changes | 314 cases; re-collect if tests change. |
| Actual passed/failed/skipped/error totals | Pending actual run. |
| Tested revision and execution time | Pending actual run. |
| Retained full-suite log, execution metadata and JUnit | Pending actual files. |
| Failure/retest details | Record original failures and successful reruns if any occur. |

## Manual and release checks — pending

Native Draw.io creation/export, final HTML visual review, the final clean-setup/offline demonstration, student explanation of the implementation and complete publication privacy/secret-history review remain outstanding. Two genuine Phase 01 screenshots are in the [screenshot register](../../evidence/Screenshot-Evidence-Register.md); diagram exports and report files do not count as additional screenshots. Update these statuses only after the corresponding action and evidence exist. The final history/privacy review is planned for Phase 12.
