# SourceAware-Stability

Code and data for **“Source-aware stability labels reshape AI crystal-discovery
benchmarks.”**

SourceAware-Stability examines how stability labels from public materials
databases affect crystal-discovery model evaluation. The repository includes
structure-matched benchmark tables, label views, model metrics, discovery curves
and the source data for the article figures.

## Model-ranking construction

The archived raw model tables contain predicted energies per atom and are
accompanied by a construct-validity audit. The primary model results use
model-specific formation energies and negative predicted energy above hull on a
fixed D2-subsystem pool to rank structures, then evaluate the 31,872-row M1
all-view common-support cohort. MP-native, alex-mp-20-native,
Alexandria-PBE-native, common-pool and audit labels share M1; consensus is
reported separately as an agreement-based selection policy.

## Data sources

- Materials Project (MP)
- MatterGen alex-mp-20 (Microsoft MatterGen Alex-MP release)
- official Alexandria-PBE (Alexandria Materials Database)

Source versions, fields and matching procedures are documented in
[`DATA_PROVENANCE.md`](DATA_PROVENANCE.md).

## Contents

- `sourceaware/` — analysis package
- `outputs/phase1_v2/` — benchmark tables and label views
- `outputs/repaired_model_evaluation_v1/` — M1 model metrics, exact discovery
  curves, raw-score validity audit, paired bootstrap differences, winner
  probabilities and fixed subsystem phase-pool manifest
- `outputs/dd_submission_v2/` — figure source data, figures and manifests
- `scripts/` and `tests/` — regeneration scripts and tests

## Reproduce

```bash
conda env create -f environment.yml
conda activate sourceaware-dd-2.0.0
bash run_all.sh
```

## Citation

Citation metadata are in [`CITATION.cff`](CITATION.cff).

## License

MIT License. Upstream data retain their original terms of use.
