# v1.1-jarvis-extension

Title: Source-aware MP--alex-mp-20 stability benchmark with JARVIS-DFT extension

This release is the public data/code and figure package for:

```text
Source-aware reporting for Materials Project and MatterGen alex-mp-20
stability labels in crystal-discovery benchmarks
```

Commit: see the `v1.1-jarvis-extension` tag target.

Zenodo DOI: https://doi.org/10.5281/zenodo.20392665

## Changes since v1.0-resubmission

- Adds a JARVIS-DFT third-source extension using records queried on
  2026-07-04 through the JARVIS OPTIMADE `jarvisdft` structures endpoint.
- Adds a 23,300-row single-match MP--alex-mp-20--JARVIS denominator for
  pairwise source-conflict rates.
- Reports exact-zero source-conflict burdens of 20.3% for MP--JARVIS, 24.5%
  for alex-mp-20--JARVIS and 13.0% for MP--alex-mp-20 on the triple
  denominator.
- Adds deterministic multiple-match sensitivity for the 4,973 rows with
  multiple JARVIS exact matches.
- Adds public Fig. 5 source data and `manuscript/figures/fig5_jarvis_multisource.pdf`.

## Included public-safe artifacts

- `manuscript/figures/`: public manuscript figure PDFs only.
- `DATA_PROVENANCE.md`: data-source provenance for Materials Project,
  MatterGen alex-mp-20 and the JARVIS-DFT extension.
- `outputs/milestones/jarvis_multisource_extension/`: JARVIS denominator
  flow, exact-match tables, pairwise conflict rates, three-source composition,
  multiple-match sensitivity and Fig. 5 source data.
- `outputs/milestones/materials_label_discordance_full_mp_alex_43984/`:
  strict MP--alex-mp-20 denominator summaries.
- `outputs/milestones/benchmark_reliability_enhancement/`: benchmark-card,
  chemistry, threshold and excluded-record audit outputs.
- `outputs/milestones/benchmark_impact_label_source_choice/`: source-label
  transfer and conflict-excluded sensitivity outputs.
- `scripts/`: public-safe analysis and figure-building scripts.
- `tests/`: integrity checks for key derived artifacts.

## Validation status

Validation commands run for this release:

```bash
python scripts/build_jarvis_multisource_extension.py --match
pytest -q
sha256sum -c MANIFEST_SHA256.txt
```

Observed test status: `34 passed`.

## Scope

This release reports source-native label dependence on strict exact-structure
denominators. It is **not** a common-hull reconstruction, prospective
discovery study or independent DFT validation.

The JARVIS extension is a third-source public-label extension, not an
adjudication of which source is physically correct. Formula candidates are used
only as a prefilter; reported JARVIS denominators require exact
`StructureMatcher` matches. Raw Materials Project structure caches, restricted
local reconstruction inputs and article-writing files are intentionally not
included in this public repository.
