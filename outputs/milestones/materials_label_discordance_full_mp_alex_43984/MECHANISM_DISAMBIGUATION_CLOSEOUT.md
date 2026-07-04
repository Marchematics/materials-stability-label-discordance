# Mechanism Disambiguation: (a) DFT Disagreement vs (b) Hull-Reference-Only

## Question

When MP and Alexandria give different stable/unstable labels for the same strict-matched structure, does the discordance arise from:
- (a) Genuinely different DFT total/formation energies between workflows, OR
- (b) The same formation energy evaluated against different hull reference sets?

## Method

1. Re-queried MP API for `formation_energy_per_atom` for all 5,060 discordant pairs (100% available).
2. Tested within-formula polymorph consistency: under mechanism (b) where Alex.e_form == MP.e_form (inherited), the difference in MP formation energies between two polymorphs must equal the difference in Alexandria e_hull values: Δ(MP.e_form) == Δ(Alex.e_hull).
3. MP internal consistency check: Δ(MP.e_form) should equal Δ(MP.e_hull) — confirmed (247/254 pairs sub-meV).

## Results

### Near-Hull Concentration

| Condition | Count | Fraction |
|-----------|-------|----------|
| Both sources \|e_hull\| < 5 meV | 1,683 | 33.3% |
| Either source \|e_hull\| < 5 meV | 5,060 | 100.0% |
| Both sources \|e_hull\| < 100 meV | 4,949 | 97.8% |
| Neither source \|e_hull\| < 100 meV | 0 | 0.0% |

ALL discordant pairs are near-hull in at least one source. Zero pairs have both sources > 100 meV from hull.

### Polymorph Cross-Validation (254 same-formula pairs)

| Metric | Value |
|--------|-------|
| MP internal consistency (sub-meV) | 247/254 (97.2%) |
| Alex agreement (sub-meV) | 19/254 (7.5%) |
| Alex inconsistent (>10 meV) while MP consistent (<1 meV) | 129/254 (50.8%) |
| Median \|Δ(MP.e_form) - Δ(Alex.e_hull)\| | 11.2 meV |

## Conclusion: MIXED Mechanism

The discordance is **primarily near-hull** — all 5,060 discordant pairs have at least one source within 5 meV of the convex hull. This is the signature of hull-reference-driven label flips.

However, the polymorph cross-validation reveals that Alexandria did NOT simply inherit MP's formation energies for ~51% of testable polymorph pairs. The median formation-energy mismatch of 11.2 meV indicates **genuine cross-workflow energy differences** at the level of individual structures.

The correct interpretation: **the 11.7% label discordance reflects combined hull-reference-set differences (causing near-hull concentration) and workflow-dependent formation-energy differences (evident in polymorph cross-validation).** Both effects contribute; neither alone fully explains the discordance.

## Impact on Paper Framing

- The headline "labels are not interchangeable" is PARTLY supported by genuine energy differences (mechanism a).
- The near-hull concentration (mechanism b) must be disclosed as the dominant spatial pattern.
- The title/abstract should reflect the combined mechanism: hull-reference conventions AND formation-energy workflows both contribute to source-native label uncertainty.
- This finding STRENGTHENS the benchmark-reliability argument: if even the target structure's own energy differs between public DFT databases, the label source matters for benchmark construction.
