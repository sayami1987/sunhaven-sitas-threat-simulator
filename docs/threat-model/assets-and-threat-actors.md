# SITAS assets and threat actors

The [synthetic environment](../../config/environment.json) contains 47 nodes and 56 directed transitions. Its entities describe fictional security states, capabilities and resources. Seven protected assets and three workstations provide targets and device context for the ten [attack scenarios](attack-scenarios.md).

## Protected assets

| Stable ID | Fictional asset | Impact | Targeted scenarios |
| --- | --- | --- | --- |
| `asset_care_records` | Care-record dataset | 5 | 01 |
| `asset_medication_records` | Medication-record dataset | 4 | 02, 03, 09 |
| `asset_payroll_records` | Payroll-record dataset | 5 | 04 |
| `asset_identity_store` | Identity-configuration dataset | 5 | 05 |
| `asset_staff_roster` | Staff roster dataset | 4 | 06, 07 |
| `asset_agency_roster` | Permitted agency roster dataset | 3 | 08 |
| `asset_care_archive` | Exported care-record archive | 5 | 10 |

Impact is an authored integer from 1 to 5 attached to each target. These scores express teaching assumptions about consequences within the model. They are not measurements of actual harm. The agency target represents limited permitted business data; it is distinct from the care-record dataset and carries a different impact.

## Scenario sources and actor assumptions

| Stable ID | Role in the model | Scenario use and assumed capability |
| --- | --- | --- |
| `attacker_external` | External threat actor and scenario source | Starts scenarios 01, 03, 05, 06, 07, 08 and 10. Each scenario explicitly selects the credential, identity, session or already-compromised operator route available to this actor. |
| `actor_local` | Local workstation user and scenario source | Starts scenario 02 with access to a shared care workstation. Stale and fresh sessions are separate alternatives. |
| `actor_internal` | Internal user and scenario source | Starts scenarios 04 and 09 with the assumed ability to use a valid workforce or agency identity before encountering an excessive or incorrect privilege. |
| `actor_agency` | Authorised agency operator reached along a path | Scenario 08 assumes this operator is already attacker-controlled, has completed authentication and holds necessary delegated access to the limited agency dataset. |
| `actor_support` | Authorised support operator reached along a path | Scenario 10 assumes a compromised or malicious operator misuses a required export role. The path retains its final privileged operation. |

The three scenario-source IDs are `attacker_external`, `actor_local` and `actor_internal`. Former-worker, workforce, agency and administrator identities are intermediate nodes. Scenario 03 starts at the external attacker and assumes reuse of `identity_former`; it does not start at a separate former-worker actor.

The agency and support operator assumptions explain the remaining exposure in scenarios 08 and 10. They represent alternatives to stealing a password, rather than an automatic bypass inferred by the program. Being represented as compromised in a fictional scenario makes no statement about a real person or role.

## Devices and applications

| Device ID | Fictional device | Relevant scenario |
| --- | --- | --- |
| `workstation_shared` | Shared care workstation | 02, with stale and fresh sessions |
| `workstation_agency_shared` | Shared agency workstation | 08, after the password-authenticated agency context |
| `workstation_service` | Service-support workstation | 10, before the internal support application and excessive privilege |

The seven application nodes are `app_care`, `app_medication`, `app_admin`, `app_roster`, `app_agency`, `app_export` and `app_internal_support`. They represent the care portal, medication application, administration console, staff roster portal, agency scheduling console, export application and internal support application respectively. The graph contains these application states; it does not launch corresponding services.

## Credentials sessions and privilege

Credential nodes hold synthetic references without usable secrets. Session nodes distinguish stale, fresh, administrator, copied, cross-device and same-device contexts. The MFA-factor node represents an assumed approval event. Privilege nodes distinguish excessive staff/service authority, an incorrectly assigned clinical role, unrestricted administration and a required support-export role.

Scenario 08 uses a separate `identity_agency_password_context` for its primary credential route and `identity_agency` for the delegated-operator route. This preserves their different authentication assumptions in the common graph.

Edges state why a transition is available and identify its ordinal likelihood and explicit control tags. Stable edge IDs preserve distinct mechanisms even when endpoints coincide. These attributes, together with scenario edge selection, determine what the analysis can discover.
