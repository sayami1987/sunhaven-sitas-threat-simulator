# SITAS attack scenarios

The scenario catalogue defines ten synthetic teaching cases. Each scenario file selects a source, protected target and allowed edge IDs from the common environment. The sequences below describe intended mechanisms; the JSON model supplies the authoritative IDs and scores. Expected control effects are design hypotheses to verify, not measured results.

| Scenario | File | Hypothetical path and security question | Control hypothesis to verify |
| --- | --- | --- | --- |
| 01 Stolen employee credentials | `scenario-01-stolen-credential.json` | Attacker → stolen staff password → workforce identity → care application → resident information. Can a password-only path reach the target? | MFA blocks the tagged password-only authentication edge. |
| 02 Shared workstation session misuse | `scenario-02-shared-session.json` | Unauthorised actor → shared workstation → abandoned authenticated session → care application → resident information. Can another user inherit access? | Timeout blocks stale-session transitions; account/session separation addresses explicitly tagged shared-use transitions. |
| 03 Stale former-worker identity | `scenario-03-stale-identity.json` | Former worker → accepted credential or identity → authentication → application → protected resource. What exposure follows an assumed residual identity? | Account disablement blocks the targeted identity's authentication transition. |
| 04 Excessive privilege | `scenario-04-excessive-privilege.json` | Standard identity → overbroad privilege → protected function → sensitive asset. Does excessive access create a reachable target? | RBAC or least privilege blocks the tagged overprivileged relationship. |
| 05 Privileged administrator compromise | `scenario-05-admin-compromise.json` | Attacker → administrator credential → privileged identity → administrative capability → identity-administration asset. What is the impact of a privileged route? | Administrative restriction and privileged reauthentication affect their explicitly matched transitions. |
| 06 MFA social engineering | `scenario-06-mfa-social-engineering.json` | Attacker → password compromise → social-engineering or MFA bypass transition → identity → application → protected asset. Does an alternative route remain after MFA? | A password-only edge can be blocked while an explicitly modeled bypass route has a capped likelihood and remains visible. |
| 07 Session token reuse | `scenario-07-session-reuse.json` | Attacker → acquired active session → application → protected information. Can access bypass a new password step? | Session revocation blocks the compromised-session edge; MFA alone must not remove unrelated session edges. |
| 08 Agency credential compromise | `scenario-08-agency-compromise.json` | Attacker → agency credential → agency identity → shared device → application → incorrectly exposed data. How do authentication and access relationships combine? | MFA, individual accounts and least privilege act on their respective tagged edges. |
| 09 Incorrect privilege relationship | `scenario-09-privilege-path.json` | Standard worker → inappropriate privilege → restricted operation → protected asset. Can a single incorrect relationship expose a restricted target? | Least privilege removes the explicit inappropriate relationship while unrelated paths remain available. |
| 10 Multistage attack | `scenario-10-multistage.json` | Attacker → credential → identity → workstation → application → privilege → protected asset. Which distinct controls affect a chain of weaknesses? | Combined controls compose deterministically; effect records identify each relevant transition without double-counting blocked paths. |

## Scenario authoring rules

Source and target IDs must resolve, the target must be an asset with impact, and allowed edge IDs must be unique known references. A scenario can contain branches, cycles and parallel edges so the engine can demonstrate more than a single hard-coded route. Only the allowed edges participate in its graph.

A scenario should explain why each transition is possible, tag the condition a control can match, and include a recommendation appropriate to the modeled weakness. Edge likelihood and target impact are synthetic assumptions. Using a shared environment avoids repeating object definitions while retaining explicit scenario scope.

## Outcome checks

For each scenario, inspect baseline ordered paths, applied rule effects, remaining paths and count reconciliation. A zero-path baseline may be a deliberate negative case in tests; it must not silently replace an intended attack demonstration. Include separate tests of malformed input, unreachable assets, cycles, maximum depth and resource exhaustion. Do not infer a result from the scenario's title or insert an expected count into a report.

The same edge sequence may appear in more than one scenario. Aggregate figures count scenario-path findings, so they should not be interpreted as mutually independent attacks or probabilities.
