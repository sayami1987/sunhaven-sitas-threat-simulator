# Input contract

SITAS inputs are local UTF-8 JSON documents with `schema_version: 1`. Identifiers
start with a letter and contain at most 80 ASCII letters, digits, underscores or
hyphens. Human-readable labels and explanations are data, not executable code.

An environment has `id`, `name`, `synthetic: true`, `nodes` and `edges`. Nodes have
`id`, `name`, `type`, `attributes`; asset nodes require an integer `impact` from
1 to 5 in their attributes. Edges have `id`, `source`, `target`, `relationship`,
integer `likelihood` from 1 to 5, a `tags` list and `explanation`.

A scenario has `id`, `title`, `description`, `source`, `target`, `edge_ids` and
`recommendation`. Its selected edges define the subgraph to analyse. The target
must be a known asset and differ from the source. A disconnected target is valid
and produces zero discovered paths within the selected depth bound.

Controls are stored in a `controls` array. Each has `id`, `name`, `description`
and `rules`. Rules have `id`, `tag`, `action`, `reason`, optional `targets`, and a
`cap` when the action is `cap`. Targets select edge destinations. An omitted or
empty targets list matches any destination with the given tag. An action is
`block` or `cap`; a cap is an integer from 1 to 5. A cap can only lower or retain
the original edge likelihood. Selection of a control does not imply every rule
matches every scenario.

The risk model declares `likelihood_method: "minimum"` and severity `bands` with
`name`, `minimum`, `maximum`. Version 1 fixes Low 1-4, Medium 5-9, High 10-16 and
Critical 17-25. Changing these conventions requires an explicit schema/design
revision, not a silent interpretation of a malformed file.

Validation rejects duplicate JSON keys, unsupported fields, duplicate IDs,
invalid references, nonfinite numbers, boolean scores and oversized inputs.
There are no environment variables, external account lookups or network calls
in the input contract. Synthetic-data declarations express the user's modelling
intent; they cannot automatically prove that arbitrary custom text is fictional.
