# SITAS assumptions and limitations

SITAS analyses a fictional synthetic attack graph. Results describe selected inputs, preconditions, control rules and bounds. They do not establish exploitability, security or compliance of a real organisation.

## Authored model and coverage

Nodes, edges, tags, impact and likelihood values are authored assumptions. The loader checks structure and references, not their truth in a real environment. Missing mechanisms cannot be discovered; incorrect tags or preconditions can misrepresent control effects. Scenarios deliberately select an edge subset. The ten supplied cases do not exhaust identity risks or every possible model/control combination.

Paths are simple directed paths: no node repeats. This excludes attacks requiring repeated visits, changing state, temporal behaviour, concurrency, AND/OR prerequisites or adversarial adaptation. Prose states assumed prerequisites, but the graph does not execute an identity protocol or independently establish those prerequisites.

## Bounds and scalability

Defaults are **12 edges of depth, 10,000 paths and 100,000 examined edge expansions**, independently for each scenario's baseline and controlled graph. They are not one combined budget across the run.

Successful results cover paths within the depth bound. depthPruned counts excluded extensions, not omitted complete paths. Zero paths can mean disconnected selected edges or no qualifying bounded route. Zero remaining paths is not proof that a real environment is secure.

Exceeding path or expansion budgets raises SearchLimitError and aborts before report writing; partial searches are not labelled complete. Iterative traversal avoids recursion, but simple-path enumeration grows combinatorially. Input/per-search limits do not guarantee speed or fixed total memory for every allowed combination. Multiple scenarios accumulate findings and rendered reports in memory.

## Ordinal risk

Minimum edge likelihood is a **bottleneck ordinal convention**, not a conservative bound, calibrated probability, attack-success estimate or product of event probabilities. It ignores event dependencies and does not penalise every additional step.

Impact is an authored target integer 1-5. Its product with likelihood maps to Low 1-4, Medium 5-9, High 10-16 or Critical 17-25. Some integers within those bands are not products of two 1-5 integers. Differences and percentage reductions are model summaries, not measured changes in incident probability or expected financial loss.

Counts depend on model granularity: parallel edges can increase path records without a proportional change in real exposure. Paths and scenarios can share assets and prerequisites. Summed exposure is therefore not independent, additive real-world risk.

## Controls and explanation

Controls remove tagged transitions or cap ordinal likelihood. Multiple caps take the minimum rather than repeated percentage reductions; any matching block removes the edge. Lowering a non-minimum edge can leave path risk unchanged while retaining an effect record.

Matching uses explicit tags and, when configured, the edge's target node. Names and node types do not imply a match. MFA does not match session-token reuse; idle timeout does not match fresh sessions; device separation does not match original-device reuse; account disablement matches stale_identity rather than every account-associated route.

The supplied shared-workstation routes lack session_token tags. They respond to timeout/shared-account rules, while revocation matches explicit administrator/staff-token routes. This models different conditions; it does not claim real shared-workstation sessions cannot be revoked. The administrator-session alternative assumes authority already carried in that session. Applying the password-only MFA rule to a service identity is a simplification, not a deployment prescription.

controlEffects.afterLikelihood describes each rule against the original edge. edgeDetails.controlledLikelihood is the combined result. Overlapping rules can give different values in these two views. A blocked edge has null effective likelihood and a blocked finding has residual null; neither becomes a surviving zero-score or Low-severity path.

## Three residual paths in the recorded run

The [saved Phase 8 report](../../reports/json/sitas-findings.json), supported by the [generation execution record](../../evidence/logs/phase08-report-generation.execution.json), records 15 baseline paths, 12 blocked and three remaining with all nine controls. These are supplied-model results, not universal behaviour.

| Remaining assumption | Recorded baseline -> residual | Meaning |
| --- | --- | --- |
| scenario_06: fictional user approves the assumed MFA event. | 16 High -> 8 Medium | The MFA cap lowers likelihood to 2 but preserves the human-mediated route. |
| scenario_08: already attacker-controlled agency operator uses required delegated access after normal authentication. | 9 Medium -> 9 Medium | MFA removes the separate password/shared-device branch; no selected rule removes this authorised-operator route. |
| scenario_10: already compromised or malicious support operator misuses an approved export role. | 15 High -> 10 High | Reauthentication caps the final operation, but the permitted-role alternative remains. |

The recorded exposure index changes from 228 to 27 (88.16%): two remaining paths are reduced and one unchanged. That percentage is only the summed ordinal index. These routes are explicit assumptions, not newly discovered real bypasses or universal control-effectiveness claims.

## Operational and report boundary

SITAS reads local synthetic JSON and writes reports. It does not contact identity services, scan networks, execute attacks, authenticate users, suspend accounts or revoke live sessions. Credential/session nodes hold labels and references, not usable secrets. The analysis uses the Python standard library.

UTF-8 HTML escapes text/attributes, with no scripts or remote assets. HTTP/HTTPS reference links are optional for the reader and do not imply network execution by SITAS. JSON preserves strings; CSV neutralises formula-leading scalar text. These intentional representation differences do not change findings.

Defaults are `reports/json/sitas-findings.json`, `reports/csv/sitas-findings.csv` and `reports/html/sitas-threat-assessment.html`. Rendering completes before writing; staging completes before replacement. Replacement is atomic per file, **not across all three**. A later failure can leave complete files from different runs. Failed analysis leaves older reports intact, so existing files do not prove the latest command succeeded. Check identifiers/timestamps and rerun successfully after interruption. Empty CSV has only its header; JSON/HTML still contain metadata.

Native Draw.io authoring and export is required for final diagrams and remains pending. Earlier custom-rendered PNGs were archived privately outside the repository and are not represented as native exports or final evidence. The public diagram folder retains editable drafts and a pending-status note. This documentation update does not complete that Phase 9 requirement.

## Reproducibility and evidence limits

inputFingerprint identifies canonical validated environment, all configured controls, risk and selected scenarios. engineFingerprint identifies normalised direct `src/*.py` source texts. simulationId also includes settings but excludes generation time. These hashes are not signatures, a Git commit ID, or verification of interpreter, dependencies, scripts or every repository file.

Default timestamps use actual UTC; caller-supplied timezone-aware timestamps support fixed-metadata comparison. A chosen timestamp is not independent execution evidence. Logs record actual start/finish times. Preserving input files, selections, bounds and source is necessary for repeatability.

Recorded execution used **Python 3.12.14**. **Python 3.11+** is the compatibility target; other versions/platforms are not claimed tested from that record. Finite tests validate cases and invariants, not every model or real-world assumption. Screenshots, logs and outputs prove only the work actually captured; a design target is not an executed result.
