# Result Summary

Last updated: 2026-05-24.

## Full MP--Alexandria Denominator

- Alexandria v20 local train+val rows: 675,204.
- Unique Alexandria rows carrying Materials Project identifiers: 43,984.
- Materials Project records successfully queried: 43,169.
- MP-ID query gap: 815 records not returned by the MP query used for this run.
- Strict StructureMatcher matches: 43,139.
- Strict mismatches among queried records: 30.
- Primary denominator interpretation: full queryable MP-identifier exact-match
  public-label overlap, not a random all-database intersection.
- OQMD exact-structure coverage in the diagnostic workflow: n=4, used only as a
  coverage boundary.

## Primary Source-Native Discordance

- Discordant labels: 5,060/43,139.
- Discordance rate: 11.7%.
- Exact binomial 95% interval: 11.4--12.0%.
- Chemical-system cluster bootstrap 95% interval: 11.3--12.1%.
- Reduced-formula cluster bootstrap 95% interval: 11.4--12.1%.
- Confusion matrix:
  - both unstable: 24,835;
  - MP-unstable / Alexandria-stable: 1,432;
  - MP-stable / Alexandria-unstable: 3,628;
  - both stable: 13,244.
- Directionality: MP-stable/Alexandria-unstable is larger than the reverse, but
  the manuscript does not mechanistically attribute this asymmetry.

## Chemistry Stratification

- Unary: 53/349 = 15.2%.
- Binary: 1,093/8,707 = 12.6%.
- Ternary: 3,147/24,781 = 12.7%.
- Quaternary or higher: 767/9,302 = 8.2%.
- Transition metal present: 3,545/32,055 = 11.1%.
- Lanthanide present: 2,066/15,063 = 13.7%.
- Oxygen present: 848/11,549 = 7.3%.
- Halogen present: 1,030/6,458 = 15.9%.
- Interpretation: descriptive atlas of source-native label disagreement, not
  mechanism-resolved attribution.

## Cross-Source Hull-Energy Difference

Definition: `Delta e = e_hull^MP - e_hull^Alex`.

- `|Delta e| < 10 meV/atom`: 2,559/34,442 discordant = 7.4%.
- `10 <= |Delta e| < 100 meV/atom`: 2,390/8,287 discordant = 28.8%.
- `|Delta e| >= 100 meV/atom`: 111/410 discordant = 27.1%.
- Interpretation: cross-source energy separation is associated with threshold
  crossing, but is not sufficient by itself because same-side outliers can remain
  concordant.

## Near-Hull Reporting Burden

Stable public entries are clipped/reported at `e_hull = 0` in the matched tables:

- MP stable: 16,872/16,872 entries at zero.
- Alexandria stable: 14,676/14,676 entries at zero.

Therefore any discordant pair triggers an either-source positive-threshold
near-hull flag. The threshold sweep is a reporting-burden analysis, not
independent localization evidence.

- 5 meV either-source flag: captures 5,060/5,060 discordant pairs and flags
  21,354/43,139 structures.
- 25 meV either-source flag: captures 5,060/5,060 discordant pairs and flags
  28,985/43,139 structures.
- Outside-flag discordance is zero under the clipped public representation.

## Benchmark-Readout Impact

Oracle/source-label transfer:

- Perfect MP-source labeler against MP labels: F1 = 1.000 by definition.
- Same MP labels evaluated against Alexandria labels: F1 = 0.8396.
- Source-agreement-only denominator retains 38,079/43,139 structures = 88.27%.

CHGNet 5,000-structure fixed-ranking diagnostic:

- Deterministic sample n = 5,000 from full denominator, seed 20260523.
- Sample representativeness:
  - MP-stable rate: 39.3% versus full 39.1%;
  - Alexandria-stable rate: 34.6% versus full 34.0%;
  - discordance: 11.2% versus full 11.7%.
- CHGNet formation-energy proxy is deliberately not a composition-aware
  stability leaderboard.
- Raw proxy AUROC: 0.546 against MP labels, 0.534 against Alexandria labels.
- Negative proxy AUROC: 0.454 against MP labels, 0.466 against Alexandria
  labels.
- Precision@300: MP 0.333 versus Alexandria 0.290, shift +4.3 percentage
  points; bootstrap 95% interval 0.7--8.0 percentage points.
- Precision@500: MP 0.304 versus Alexandria 0.268, shift +3.6 percentage
  points; bootstrap 95% interval 1.2--6.2 percentage points.
- K=300 top-set decomposition: 77 both stable, 23 MP-only stable, 10
  Alexandria-only stable, 190 both unstable.

## Secondary Diagnostics

These are supplementary only.

- Earlier 287-structure scored subset:
  - ALIGNN-FF top decile: 5/29 discordant;
  - CHGNet top decile: 3/29 discordant;
  - MACE-MP top decile: 3/29 discordant;
  - rank-permutation p values: 0.633, 0.367 and 0.327.
- WBM--Alexandria archived probe:
  - 141/270 = 52.2% on its release-conditioned denominator;
  - MP-native exact-stable selected full-denominator set: 3,628/16,872 = 21.5%;
  - MP-native `e_hull^MP <= 25 meV/atom` sensitivity set:
    4,677/27,280 = 17.1%.
- Interpretation: source pair, denominator and selection condition must be
  reported together.
