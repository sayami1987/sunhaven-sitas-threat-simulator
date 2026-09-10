# Risk methodology

SITAS uses a deterministic educational ranking convention. An edge has an
ordinal likelihood of 1 Rare, 2 Unlikely, 3 Possible, 4 Likely or 5 Almost Certain.
The likelihood of a path is the minimum of its edge likelihoods: the hardest
modelled transition limits that route. These labels express assumptions, not
observed frequencies or calibrated probabilities.

Impact comes from the protected target asset: 1 Insignificant, 2 Minor,
3 Moderate, 4 Major or 5 Severe. The path score is likelihood multiplied by impact.
For example, edge values [4, 3, 5] and target impact 5 yield minimum likelihood 3,
score 15 and High severity. This arithmetic example is not execution evidence.

| Score | Severity |
| --- | --- |
| 1-4 | Low |
| 5-9 | Medium |
| 10-16 | High |
| 17-25 | Critical |

These ranges and the minimum-likelihood convention are stored in
`config/risk-model.json`. The loader rejects other mappings for schema version 1.
`src/risk_engine.py` implements the convention and checks that path edges match
the ordered nodes and terminate at an asset with valid impact.

The minimum convention is simple to explain but does not accumulate the
difficulty of several steps and can give equal scores to paths of different
lengths. Ordinal scales do not justify probability arithmetic. Dependencies,
attacker capability, data volume and unknown relationships are not calibrated.
More sophisticated scoring would require different data and explicit validation.

Control caps lower individual edge likelihoods; a cap above the existing
minimum may leave the overall path score unchanged. Blocking makes residual
path risk inapplicable (reported as null), rather than turning a blocked path
into a surviving Low-severity path. Summed scores, when reported, are only an
illustrative exposure index. Shared edges and overlapping scenarios can
double-count exposure and do not represent independent events or expected loss.
