# Control simulation methodology

SITAS applies selected control rules to a copy of a synthetic directed graph.
The implementation is `src/control_engine.py`; the configured rules are in
`config/controls.json`. The function returns a new graph, a record of every
matching rule, and the selected control IDs in sorted order. It never configures
real accounts, sessions, devices or applications.

## Rule selection and matching

`apply_controls(graph, controls, selected_ids)` accepts validated `Control`
records. Repeated selected IDs are deduplicated. An unknown selected ID raises
`ModelError`. Duplicate configured control or rule IDs also raise `ModelError`.

A rule matches an edge only when:

1. Its `tag` is present in the edge's `tags`.
2. Its `targets` list is empty, or the edge's **target node ID** occurs in that
   list. A matching source node does not satisfy this selector.

An omitted target list becomes an empty tuple when the loader creates the rule.
The loader validates tags and target IDs against the full environment. A global
rule can legitimately have no matching tag in a selected scenario graph; this
produces no effect and is not an error.

The engine checks actions and caps for every supplied rule before matching,
including rules with no matching edge or belonging to an unselected control.
Only `block` and `cap` are supported. A cap must be an integer from 1 to 5;
Boolean values are rejected. A block rule must not provide a cap.

## Combining matched effects

A `block` removes the matching edge from the output graph. If any matching rule
blocks an edge, the edge is absent even when other rules cap it.

A `cap` keeps the edge and limits its ordinal likelihood. With original edge
likelihood `L` and matching caps `c1 ... cn`, the surviving likelihood is:

```text
L_after = min(L, c1, ..., cn)
```

Caps never increase a likelihood. Applying no controls preserves the graph's
nodes, edges and values in a new graph instance. The baseline graph and its
records are not edited. Nodes and endpoints remain unchanged; the operation
only removes edges or lowers their scores, so it cannot create a new route.

Every matched rule is retained as a `ControlEffect`, even if another rule blocks
the edge or the cap does not lower its original score. Effects are sorted by
edge ID, control ID and rule ID. Each effect contains the explanation from the
configured rule and uses the original edge likelihood as `beforeLikelihood`.

`afterLikelihood` is **rule-specific**, not the combined edge result:

- Block: `null`.
- Cap: `min(original_likelihood, that_rule_cap)`.

For example, an edge originally scored 5 with caps 3 and 2 produces effects
`5 -> 3` and `5 -> 2`, while the output edge is scored 2. Adding a matching block
retains both cap explanations and the block explanation, but removes the edge.

## Meaning of the nine configured controls

| Control ID | Matching tag and effect | Scope of the assumption |
| --- | --- | --- |
| `mfa` | Block `password_only`; cap `mfa_social_engineering` at 2. | Password-only access is interrupted. The assumed human-mediated MFA route remains possible at a lower ordinal score. Existing session-token routes are unaffected. |
| `rbac` | Block `excessive_privilege`. | Removes explicitly excessive or incorrectly assigned roles; required business permissions remain. |
| `account_disablement` | Block `stale_identity`. | Removes the modelled stale-identity route. It does not automatically revoke unrelated active sessions. |
| `session_timeout` | Block `stale_session`. | Applies to stale idle sessions; freshly active alternatives remain. |
| `session_revocation` | Block `session_token`. | Applies only to transitions explicitly tagged as session-token routes. It does not infer a match merely because a node has type `session`. |
| `individual_accounts` | Block `shared_account`. | Removes shared-identity routes. A shared device using an individual identity is a different condition. |
| `privileged_reauthentication` | Cap `privileged_operation` at 2. | Reduces the ordinal score for a privileged operation without claiming perfect prevention. |
| `admin_restriction` | Block `unrestricted_admin`. | Removes explicitly unrestricted authority; narrowly approved roles can remain. |
| `device_session_separation` | Block `cross_device_session`. | Removes reuse on another device; original-device reuse is an explicit alternative. |

In the supplied model, the shared-workstation routes use `shared_account` and
stale/active-session tags. They do not carry `session_token`, so session
revocation alone does not remove those routes. The administrator and staff-token
reuse routes explicitly carry `session_token`. This difference is a visible
modelling choice, not a statement that real workstation sessions cannot be
revoked.

The administrator-session alternative assumes authority was already carried in
an authenticated session. The password-only service route applies the same MFA
rule as other `password_only` transitions; this is a simplified model and does
not prescribe an authentication design for a real service identity.

## Interpretation and limitations

Likelihood values and caps are ordinal assumptions from a synthetic teaching
model, not measured probabilities or estimates of real control effectiveness.
Matching depends on the supplied tags and scenario preconditions. A missing tag
can leave a route unaffected, and an overbroad tag can remove more than intended.

Several scenarios deliberately retain routes through fresh sessions, an
original device, or an already compromised authorised operator. These routes
explain why one control can reduce exposure without eliminating all modelled
paths. A control with no matched rule changes nothing in that scenario.

SITAS must traverse and score the resulting graph separately to compare attack
paths and risk. A matched control effect alone does not establish that a target
became unreachable. The absence of a route in this finite synthetic graph is
also not evidence that a real organisation is secure.
