# Reference guidance and SITAS applicability

The following sources were checked on 11 September 2026 (Australia/Sydney).
They inform the explanation of the model and its report. The simulator makes no
certification, organisational compliance or real control-effectiveness claim.

## NIST risk assessment guidance

NIST SP 800-30 Revision 1 describes preparing, conducting, communicating and
maintaining risk assessments. Section 2.3 discusses uncertainty and qualitative
or semi-quantitative approaches. Appendix K illustrates reporting with an
executive summary, detailed results and supporting material. SITAS adopts these
reporting concepts by exposing scope, assumptions, threat paths, assessment
date, severity counts, control effects and evidence. Its minimum-edge rule,
1-5 scales, multiplication and four severity bands are explicit project design
choices; they are not a scoring algorithm prescribed by NIST.

Source: [NIST SP 800-30 Rev. 1](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-30r1.pdf),
sections 2.3 and 3, and Appendix K. Printed pages 13-14, 23-38 and K-1 to K-2.

## SANS policy reference

The SANS policy library and its Access Management and Privileged Account
Management summaries identify identity verification, RBAC, least privilege and
MFA as relevant policy subjects. SITAS uses those subjects to explain simulated
controls. It does not adopt a policy template as an implemented organisational
policy. The linked landing-page descriptions were reviewed; the separately
downloadable policy templates were not imported or reproduced.

Sources: [SANS policy library](https://www.sans.org/information-security-policy),
[Access Management Policy](https://www.sans.org/information-security-policy/access-management-policy),
[Privileged Account Management Policy](https://www.sans.org/information-security-policy/privileged-account-management-policy)
(policy pages published 11 February 2026).

## Australian ISM reference

The ISM landing page provided the September 2026 release. Its framework guidance
distinguishes defining a system, selecting controls, implementation, assessment,
authorisation and monitoring. SITAS supports hypothetical analysis; it does not
perform the operational assurance and authorisation steps.

The September 2026 system-access guidance supplies useful conceptual context:

| ISM reference | Topic | SITAS modelling relationship |
| --- | --- | --- |
| ISM-0414 and ISM-0415 | Individually identifiable users and controlled shared accounts | `individual_accounts` blocks explicitly modelled shared-account transitions. |
| ISM-1852 and ISM-1508 | Necessary unprivileged and privileged access | `rbac` and `admin_restriction` model selected inappropriate privilege transitions. |
| ISM-0430 | Remove or suspend access when no longer needed | `account_disablement` models blocking a stale-identity authentication transition. |
| ISM-1504 and ISM-1173 | MFA for sensitive online services and privileged human users | `mfa` blocks password-only transitions and retains an explicitly modelled social-engineering residual. |
| ISM-0428 | Lock inactive sessions and require reauthentication | `session_timeout` models stale-session exposure; it does not measure or enforce an actual ISM timeout. |

These are topic mappings. They do not implement the complete ISM control text,
timing requirements, applicability conditions or assessment evidence.

Sources: [ISM September 2026](https://www.cyber.gov.au/business-government/asds-cyber-security-frameworks/ism),
[Using the cyber security framework](https://www.cyber.gov.au/business-government/asds-cyber-security-frameworks/ism/using-the-cyber-security-framework),
[Guidelines for system access](https://www.cyber.gov.au/business-government/asds-cyber-security-frameworks/ism/cyber-security-guidelines/guidelines-for-system-access).

## Applying the references to reports

Each report should state the model identity and fingerprint, its generation time,
the selected scenarios and search limits, and the actual before/after results.
It should retain surviving routes, state the assumptions behind control rules,
link findings to input edges, and explain uncertainty. A changed scenario,
control definition or risk model should trigger a new run and input fingerprint.
