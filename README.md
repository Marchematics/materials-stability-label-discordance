# Source-native stability-label uncertainty in crystal discovery benchmarks

This repository provides the public reproducibility materials for the study:

**Source-native stability-label uncertainty in crystal discovery benchmarks**

Manuscript and journal-submission files are not tracked in this repository.
They are handled separately through the journal submission system.

## Study summary

Machine-learning crystal discovery often evaluates models with binary
DFT-derived stability labels, but public materials databases use different
workflows, correction schemes and hull references. This study audits those
source-native public labels on strict Materials Project--Alexandria matched
crystal structures and quantifies their effect on benchmark reporting.

Main results:

- 43,139 strict Materials Project--Alexandria structure matches retained from
  43,984 Alexandria rows carrying Materials Project identifiers.
- 5,060 matched structures have discordant source-native binary stability
  labels, giving an 11.7% source-conflict rate.
- Chemical-system cluster bootstrap interval for the primary discordance rate:
  11.3--12.1%.
- Near-hull flags are reported as public-label burden diagnostics because stable
  public entries are clipped to `e_above_hull = 0`.
- A fixed CHGNet 5,000-structure ranking diagnostic shows MP-minus-Alexandria
  precision@300/500 shifts of 4.3/3.6 percentage points.

The manuscript does not claim that DFT labels are invalid, that either database
is wrong, or that CHGNet is a stability leaderboard model. The contribution is a
reproducible benchmark-reliability audit: source-sensitive and near-threshold
label burden should be disclosed alongside binary stability endpoints.

## Reproducibility materials

```text
outputs/publication/
  tables/
    table_source_aware_benchmark_card.csv
    table_claim_boundaries.csv
  source_data/

outputs/milestones/materials_label_discordance_full_mp_alex_43984/
  full-denominator MP--Alexandria exact-match outputs

outputs/milestones/benchmark_impact_label_source_choice/
  oracle label-transfer and conflict-exclusion diagnostics

outputs/milestones/model_facing_benchmark_sensitivity_check/
  CHGNet 5,000-structure fixed-ranking sensitivity diagnostics

scripts/
  analysis, diagnostic and figure-generation scripts

tests/
  integrity and claim-support checks
```

Historical preregistration and exploratory diagnostics are retained under
`outputs/milestones/materials_label_discordance_preregistration/` for
auditability, but they are not the public-facing contribution of the npj
submission.

## Data and code availability

Derived public-safe tables, figure source data, scripts and integrity manifests
are archived at Zenodo:

```text
https://doi.org/10.5281/zenodo.20392665
```

The raw Materials Project structure cache used during denominator construction
is a local API cache and is not redistributed. Public-safe matched summary
tables can be regenerated from public source records using the archived scripts,
subject to Materials Project API terms.

## Reproduce analyses

```bash
pytest -q tests
```

Optional figure regeneration can be run with:

```bash
python scripts/build_manuscript_figures.py
```

The figure builder writes generated figures under the local ignored
`manuscript/figures/` directory. If the hand-prepared Fig. 1 source is absent,
the script generates a programmatic fallback panel.
