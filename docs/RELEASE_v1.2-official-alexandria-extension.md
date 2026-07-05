# Release v1.2-official-alexandria-extension

Public-safe resubmission package for the multi-source source-native
stability-label audit.

## Scope

This release adds the official Alexandria-PBE extension to the existing
Materials Project--MatterGen alex-mp-20 audit. MatterGen alex-mp-20 and
official Alexandria-PBE are treated as distinct source-native label sources.

The official Alexandria-PBE analysis uses the complete PBE 3D database snapshot
`2025.07.02`, not the convex-hull-only download. The relevant stability field
is `entries[].data.e_above_hull`, interpreted as eV atom^-1.

## Key public-safe artifacts

- `outputs/milestones/official_alexandria_pbe_feasibility/`
  - schema and download audit;
  - formula-prefiltered exact-structure matching outputs;
  - denominator flow and multiple-match sensitivity inputs.
- `outputs/milestones/official_alexandria_pbe_extension/`
  - pairwise source-conflict burdens under 0, 1, 5, 10 and 25 meV atom^-1 cutoffs;
  - source-conflict directionality;
  - three-source label composition;
  - alex-mp-20--official Alexandria-PBE source-native hull-value differences;
  - chemistry-stratified chemical-system bootstrap intervals;
  - fixed source-native and CHGNet-ranking uncertainty bands;
  - figure-source inputs;
  - SHA256 manifest.
- `DATA_PROVENANCE.md`
- `REPRODUCIBILITY.md`
- `MANIFEST_SHA256.txt`

## Primary official Alexandria-PBE results

On the 36,802-row single-match MP--alex-mp-20--official Alexandria-PBE
denominator, exact-zero source-conflict burdens are:

- MP--official Alexandria-PBE: 5,666 / 36,802 = 15.4%;
- MatterGen alex-mp-20--official Alexandria-PBE: 3,862 / 36,802 = 10.5%;
- MP--MatterGen alex-mp-20: 4,244 / 36,802 = 11.5%.

Including multiple official Alexandria-PBE exact matches under deterministic
tie-breaking gives the same qualitative ordering and slightly higher
MP--official Alexandria-PBE burdens.

## Guardrails

This release reports source-native public-label dependence. It does not claim:

- common-hull reconstruction;
- independent DFT validation;
- formula-only official Alexandria-PBE validation;
- that MatterGen alex-mp-20 labels are unmodified Alexandria labels;
- that any source is the physically correct reference.
