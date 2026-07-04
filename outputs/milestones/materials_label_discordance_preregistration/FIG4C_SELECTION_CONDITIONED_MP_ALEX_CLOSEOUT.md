# Fig. 4c Selection-Conditioned MP-vs-Alex Diagnostic

## Question

Does the high WBM-vs-Alex discordance case persist when the same release-style
conditioning is applied inside the MP-vs-Alex exact-match denominator?

## Definition

The primary panel-c bar uses a portable source-native release rule:

```text
denominator: MP-vs-Alex strict-structure matches
score/source label: MP energy_above_hull
selection rule: MP energy_above_hull <= 0 eV/atom
evaluation: binary exact-stability disagreement with Alex labels
```

This is a diagnostic reconciliation bar. It is not a new PARC guarantee and not
a three-source validation.

A strict SCS/PARC portability check was also run on this small denominator at
`alpha=0.10`, `rho=0.10` and `K in {50,100,124,200,287}`. It produced
`0` non-empty seed rows out of `100`. Thus the panel-c bar
uses source-native release conditioning rather than a certified PARC release.

## Result

```text
full MP-vs-Alex denominator discordance: 0.108 (n=287)
MP-native exact-stable selected discordance: 0.169 (n=124)
MP-selected but Alex-unstable count: 21
```

Interpretation: selection conditioning within the MP-vs-Alex denominator raises
discordance modestly relative to the full denominator, but it remains far below
the earlier WBM-vs-Alex/PARC-style case. The reconciliation is therefore mostly
a source-pair / denominator effect, with a smaller MP-native selection effect.
