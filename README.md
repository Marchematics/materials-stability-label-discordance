# SourceAware-Stability

Code and data for **“Source-aware stability labels reshape AI crystal-discovery
benchmarks.”**

SourceAware-Stability examines how stability labels from public materials
databases affect crystal-discovery model evaluation. The repository includes
structure-matched benchmark tables, label views, model metrics, discovery curves
and the source data for the article figures.

## Data sources

- Materials Project (MP)
- MatterGen alex-mp-20 (Microsoft MatterGen Alex-MP release)
- official Alexandria-PBE (Alexandria Materials Database)

Source versions, fields and matching procedures are documented in
[`DATA_PROVENANCE.md`](DATA_PROVENANCE.md).

## Contents

- `sourceaware/` — analysis package
- `outputs/phase1_v2/` — benchmark tables and label views
- `outputs/phase2_v1/` — model-evaluation outputs
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
