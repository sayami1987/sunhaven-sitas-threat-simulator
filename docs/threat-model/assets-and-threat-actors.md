# SITAS assets and threat actors

All entities describe a fictional Sunhaven Care model. Names identify roles and security states rather than real people. The environment JSON is authoritative for stable IDs, exact relationships and impact values; this document explains the modelling purpose of each category.

## Protected assets

| Asset category | Security concern | Reason to model it |
| --- | --- | --- |
| Fictional resident records | Confidentiality of sensitive care information | Demonstrates the consequence of workforce or session access reaching a sensitive data target |
| Fictional workforce data | Confidentiality and integrity of workforce information | Provides an additional target with its own explicit impact assumption |
| Identity administration | Integrity of roles, privileges and administrative configuration | Represents a high-impact target reached through privileged compromise |

Each protected asset has an integer impact from 1 to 5. The score is a teaching assumption attached to the target and should be explained in the environment model. Real care records, employee lists, tenant identifiers and secrets are unnecessary for this analysis.

## Threat actors and starting states

| Actor or state | Assumed capability | Modelling purpose |
| --- | --- | --- |
| External attacker | Can use the credential or session-compromise transitions allowed by a scenario | Compares password, social-engineering and session routes |
| Former worker | Retains a fictional credential or identity whose acceptance is assumed | Explores a residual authentication path |
| Unauthorised shared-device user | Can interact with a shared workstation under the scenario's conditions | Explores abandoned-session access and separation controls |
| Compromised standard workforce identity | Possesses standard access plus the explicitly modeled inappropriate relationship | Explores excess privilege and restricted operations |
| Compromised agency identity | Can use a fictional agency credential and selected device/application relationships | Explores combined authentication and access exposure |
| Compromised administrator identity | Can attempt the selected privileged transitions | Explores administrative reachability and impact |

An identity being used as an attack source means compromise or misuse is assumed for the scenario. It does not imply that a real worker or role is malicious.

## Supporting entities

Credentials model possession of authentication material without storing passwords. Sessions model an already authenticated state, including relevant conditions such as stale, stolen or shared use. Devices include shared nurse workstations, agency laptops and management workstations. Applications include the care portal and identity-administration console. Privilege and role nodes expose the transitions between ordinary application access and a restricted capability.

Relationships express what can be reached and why. Distinct edge IDs allow two authentication mechanisms between the same entities to carry different likelihood values and control tags. Descriptions should make each precondition understandable without requiring hidden external information.
