# v1.0-resubmission

Title: Source-aware MP--alex-mp-20 stability benchmark

This release is the public data/code and figure package for:

```text
Source-aware reporting for Materials Project and MatterGen alex-mp-20
stability labels in crystal-discovery benchmarks
```

Commit: see the `v1.0-resubmission` tag target.

Zenodo DOI: https://doi.org/10.5281/zenodo.20392665

## Included public-safe artifacts

- `manuscript/figures/`: public manuscript figure PDFs.
- `DATA_PROVENANCE.md`: data-source provenance for Materials Project and
  MatterGen alex-mp-20.
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
python scripts/build_excluded_record_audit.py
python scripts/build_manuscript_figures.py
pytest -q tests -p no:cacheprovider
```

Observed test status: `33 passed`.

The public figure PDFs and repository text were scanned for legacy
review-facing labels and working-note references; none were present in the
checked public-facing artifacts.

## Scope

This release reports source-native label dependence on a strict MP-identifier
structure-matched MP--alex-mp-20 denominator. It is **not** a common-hull
reconstruction, prospective discovery study or independent DFT validation.

The second source is named **MatterGen alex-mp-20**, not unmodified Alexandria.
Raw Materials Project structure caches, restricted local reconstruction inputs
and article-writing files are intentionally not included in this public
repository.
