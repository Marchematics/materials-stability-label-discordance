# Project Truth

Last updated: 2026-05-26.

## Source of Truth

- Active manuscript: `manuscript/main.tex`.
- Current compiled PDF: `manuscript/main.pdf`.
- Bibliography: `manuscript/references.bib` plus generated `manuscript/main.bbl`.
- Main figure builder: `scripts/build_manuscript_figures.py`.
- Zenodo-ready data/code release package:
  `releases/zenodo/discordance-npjcompmat-data-code-2026-05-26.zip`.
- Archived DOI used in manuscript and release notes:
  `10.5281/zenodo.20392665`.
- This is the Zenodo concept DOI for the data/code archive and resolves to the
  latest version.
- Current checked Zenodo version record:
  `10.5281/zenodo.20392666`.
- Zenodo concept DOI:
  `10.5281/zenodo.20392665`.
- Public GitHub repository:
  `https://github.com/Marchematics/materials-stability-label-discordance`.

## Venue And Article Type

- Primary venue: `npj Computational Materials`.
- Article type: Article / research article.
- Style: Nature Portfolio / Springer Nature journal article, using
  `sn-jnl.cls` with `sn-nature`.
- Dominant contribution type: benchmark-reliability audit and reporting
  framework for computational materials stability labels.

## Current One-Sentence Story

Public source-native DFT-derived binary stability labels are useful but not
fully source-invariant: in the full Materials Project--Alexandria MP-identifier
exact-match denominator, 11.7% of binary labels disagree, and that disagreement
creates measurable benchmark-readout uncertainty that should be disclosed
alongside binary stability endpoints.

## Stable Framing

The manuscript separates three empirical questions and one reporting
implication:

1. What is the source-pair baseline for MP--Alexandria public stability-label
   discordance on a strict shared-structure denominator?
2. How do cross-source hull-energy differences and chemistry stratify that
   discordance?
3. Does changing only the evaluation label source alter benchmark readouts under
   fixed predictions?
4. How should benchmark reports disclose source-sensitive and near-threshold
   labels without overclaiming from clipped public tables?

## Durable Claim Boundaries

Do claim:

- This is a source-native public-label reproducibility audit on a stringent
  MP-identifier exact-match denominator.
- The full denominator has 43,139 strict MP--Alexandria structure matches and
  5,060 discordant binary stability labels (11.7%).
- Chemical-system cluster bootstrap supports the same rate scale (11.3--12.1%).
- Discordance is chemically nonuniform and enriched when cross-source hull
  energies differ enough to create threshold crossings.
- In the clipped public-label representation, near-hull flags quantify reporting
  burden rather than independent physical localization.
- Label-source choice changes benchmark readouts under a perfect source-label
  oracle and under a fixed CHGNet 5,000-structure ranking diagnostic.

Do not claim:

- DFT labels are invalid or either database is wrong.
- The MP--Alexandria denominator is a random sample of all possible public DFT
  database overlap.
- The analysis is mechanism-resolved into formation-energy, correction, magnetic
  or hull-reference effects.
- OQMD triangulates the result; exact-structure coverage was too small.
- CHGNet is evaluated as a stability leaderboard model here.
- Near-hull flags are a general three-state annotation rule under unclipped
  physics; in this dataset they are public-table burden diagnostics.
- Secondary WBM--Alexandria and 287-structure scored-subset diagnostics are
  source-wide estimates.

## Current Main Display Items

- Fig. 1: full MP--Alexandria exact-match denominator and binary label outcomes.
- Fig. 2: cross-source hull-energy differences and near-hull reporting burden.
- Fig. 3: benchmark-readout consequences under oracle and CHGNet diagnostics.
- Fig. 4: chemistry-stratified source-native discordance.
- Table 1: denominator construction audit.
- Table 2: chemistry-stratified discordance.
