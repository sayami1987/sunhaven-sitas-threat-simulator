# SITAS attack scenarios

The ten scenario files select a source, protected target and allowed edge IDs from the common fictional environment. The recorded Phase 7 execution found 15 baseline paths. Applying all nine configured controls blocked 12 and left three: two with lower ordinal risk and one unchanged. These are results of the supplied model, not observations of a real system.

The values below come from [scenario-results.json](../../evidence/07-control-simulation/scenario-results.json) and the [actual execution log](../../evidence/logs/phase07-all-scenarios.txt), recorded in commit [c080687](https://github.com/sayami1987/sunhaven-sitas-threat-simulator/commit/c080687f87bf8b9621837a02af59b4f283c549e1). The [scenario test log](../../evidence/logs/phase07-scenario-tests.txt) records 19 passing acceptance tests, including literal expected edge sequences and independently calculated scores.

## Catalogue

| ID | Scenario file | Source | Protected target |
| --- | --- | --- | --- |
| `scenario_01` | [scenario-01-stolen-credential.json](../../scenarios/scenario-01-stolen-credential.json) | `attacker_external` | `asset_care_records` |
| `scenario_02` | [scenario-02-shared-session.json](../../scenarios/scenario-02-shared-session.json) | `actor_local` | `asset_medication_records` |
| `scenario_03` | [scenario-03-stale-identity.json](../../scenarios/scenario-03-stale-identity.json) | `attacker_external` | `asset_medication_records` |
| `scenario_04` | [scenario-04-excessive-privilege.json](../../scenarios/scenario-04-excessive-privilege.json) | `actor_internal` | `asset_payroll_records` |
| `scenario_05` | [scenario-05-admin-compromise.json](../../scenarios/scenario-05-admin-compromise.json) | `attacker_external` | `asset_identity_store` |
| `scenario_06` | [scenario-06-mfa-social-engineering.json](../../scenarios/scenario-06-mfa-social-engineering.json) | `attacker_external` | `asset_staff_roster` |
| `scenario_07` | [scenario-07-session-reuse.json](../../scenarios/scenario-07-session-reuse.json) | `attacker_external` | `asset_staff_roster` |
| `scenario_08` | [scenario-08-agency-compromise.json](../../scenarios/scenario-08-agency-compromise.json) | `attacker_external` | `asset_agency_roster` |
| `scenario_09` | [scenario-09-privilege-path.json](../../scenarios/scenario-09-privilege-path.json) | `actor_internal` | `asset_medication_records` |
| `scenario_10` | [scenario-10-multistage.json](../../scenarios/scenario-10-multistage.json) | `attacker_external` | `asset_care_archive` |

## Recorded comparison

All nine controls were selected for this execution. Before and after columns are sums of ordinal path scores within each scenario. A blocked path has no residual score; zero in an aggregate column means no surviving path contributed to that sum.

| Scenario | Baseline paths | Blocked | Remaining | Reduced | Unchanged | Before index | After index |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 01 | 1 | 1 | 0 | 0 | 0 | 20 | 0 |
| 02 | 2 | 2 | 0 | 0 | 0 | 28 | 0 |
| 03 | 1 | 1 | 0 | 0 | 0 | 16 | 0 |
| 04 | 1 | 1 | 0 | 0 | 0 | 20 | 0 |
| 05 | 2 | 2 | 0 | 0 | 0 | 35 | 0 |
| 06 | 1 | 0 | 1 | 1 | 0 | 16 | 8 |
| 07 | 2 | 2 | 0 | 0 | 0 | 28 | 0 |
| 08 | 2 | 1 | 1 | 0 | 1 | 18 | 9 |
| 09 | 1 | 1 | 0 | 0 | 0 | 12 | 0 |
| 10 | 2 | 1 | 1 | 1 | 0 | 35 | 10 |
| Total | 15 | 12 | 3 | 2 | 1 | 228 | 27 |

Baseline severity counts are four Critical, nine High and two Medium. The three remaining paths comprise one High and two Medium. The reported index reduction is 88.16%; it is a change in an educational ordinal sum, not a percentage reduction in real incident probability. Shared prerequisites and assets mean these paths are not independent events.

## Mechanisms and interpretation

1. **Stolen worker password.** The actor holds a synthetic worker-password reference, authenticates as the workforce identity and reaches the care portal and care records. All four edge likelihoods are 4 and target impact is 5, giving 20. MFA blocks the explicit password-only login transition.

2. **Shared workstation sessions.** A local actor reaches the shared care workstation and either a stale or fresh authenticated session. Both routes use the shared identity to reach medication records. Their baseline scores are 16 and 12. Timeout removes only the stale-session transition; individual accounts remove both shared-identity transitions. The isolated timeout acceptance test confirms that the fresh path remains with score 12.

3. **Former-worker identity.** The external attacker is assumed able to reuse the fictional identity that should be disabled. That identity reaches the medication application and records, giving score 16. Account disablement matches the `stale_identity` transition. The scenario describes this assumed state rather than querying actual account records.

4. **Excessive staff privilege.** An internal actor uses the workforce identity and an excessive role to reach the administration console and payroll data. The baseline score is 20. RBAC blocks the excessive-role edge; privileged reauthentication also caps a later operation, with its effect retained in the blocked finding.

5. **Administrator compromise.** The password route passes through an unrestricted administrator role and has score 20. A separate already-authenticated administrator session reaches the console with score 15. MFA alone blocks the password route and leaves the session alternative. In the full-control result, session revocation blocks that alternative as well.

6. **MFA social approval.** The scenario assumes an attacker-initiated MFA approval is accepted. It contains an explicit approval transition rather than a password-only login edge. MFA caps that transition from likelihood 4 to 2; target impact 4 gives a reduction from 16 High to 8 Medium. The route remains visible.

7. **Session reuse across device contexts.** A copied session can be used on a different device or its original device. Baseline scores are 16 and 12. Device-session separation alone blocks the cross-device edge and leaves the original-device route. Session revocation blocks both token routes; MFA alone changes neither.

8. **Agency credential and operator alternatives.** The primary route passes through a compromised agency-password reference, a distinct password-authenticated identity context, a shared agency workstation and the scheduling application. Its target is limited permitted agency data, with impact 3 and score 9. MFA blocks that password route. The alternative explicitly assumes an already-controlled authorised operator with completed authentication and necessary delegated permissions. No selected rule matches that route, which remains unchanged at 9 Medium. Its continued presence follows the stated precondition, not an automatically inferred control bypass.

9. **Incorrect agency privilege.** An internal actor uses an agency identity with an incorrectly assigned clinical role to reach medication records. Minimum likelihood 3 and impact 4 give score 12. RBAC removes the excessive assignment; privileged reauthentication also reduces the modeled operation's likelihood.

10. **Multistage export.** The primary route has seven transitions through credential, identity, workstation, internal support application, excessive privilege, export application and care archive. Its score is 20, and password, excessive-role and unrestricted-admin controls block it. A separate assumed compromised or malicious support operator uses a required export role. Privileged reauthentication caps its final operation, reducing the surviving path from 15 to 10; both scores are High under the configured bands.

## Scope of these results

The saved execution used the normal 12-edge maximum depth and recorded no depth-pruned transitions. The [baseline-only execution](../../evidence/07-control-simulation/scenario-baseline.json) retained all 15 paths with index 228. Invalid or ambiguous input raises an error; valid scenarios with no reachable target return a bounded zero-path result.

The scenario JSON defines which transitions participate. The engine enumerates those transitions rather than relying on scenario titles or inserting expected findings. Model changes require new execution evidence before updating recorded results. See [assumptions and limitations](../limitations/assumptions-and-limitations.md) for the interpretation of ordinal scores, graph coverage and resource limits.
