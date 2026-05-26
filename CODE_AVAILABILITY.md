# Code Availability

The code used to generate the full denominator, analysis tables, figures and
model-facing sensitivity diagnostics is archived with the Zenodo record:

```text
https://doi.org/10.5281/zenodo.20392665
```

The development repository is:

```text
https://github.com/Marchematics/materials-stability-label-discordance
```

Main scripts:

```text
scripts/run_full_mp_alex_denominator_43984.py
scripts/build_major_revision_diagnostics.py
scripts/build_benchmark_impact_label_source_choice.py
scripts/build_model_facing_benchmark_sensitivity_check.py
scripts/analyze_revised_fig2_energy_difference.py
```

Integrity tests are under `tests/` and can be run with:

```bash
pytest -q tests
```
