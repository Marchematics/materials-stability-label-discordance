# Reproducibility

This repository is organized around the npj Computational Materials submission
artifact. The public-safe tables are archived at Zenodo:

```text
https://doi.org/10.5281/zenodo.20392665
```

## Environment

The analysis scripts are Python-based and use standard scientific Python
packages including `pandas`, `numpy`, `matplotlib`, `scipy`, `pymatgen` and
model-specific packages for the archived CHGNet sensitivity diagnostic.

Manuscript and journal-submission files are not tracked in this public
reproducibility repository.

## Main reproduction commands

```bash
pytest -q tests
```

## Public-safe derived outputs

The primary derived tables are in:

```text
outputs/milestones/materials_label_discordance_full_mp_alex_43984/
outputs/milestones/benchmark_impact_label_source_choice/
outputs/milestones/model_facing_benchmark_sensitivity_check/
outputs/publication/
```

The raw Materials Project structure cache used to construct the full
denominator is not redistributed. Regeneration of the full denominator from
public records requires Materials Project API access and is subject to the
Materials Project API terms.
