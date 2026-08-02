# SourceAware-Stability

Source-aware stability endpoints for crystal-discovery benchmark evaluation.

This release contains source provenance cards, frozen denominator and endpoint manifests, tolerance-equivalence audits, batch-relative signed reference-hull rankings, threshold and matching sensitivity analyses, model hits and regret summaries, figure-source tables, claim maps, scripts, tests and reproducibility metadata.

## Data sources

- Materials Project (MP)
- MatterGen alex-mp-20
- official Alexandria-PBE

Source versions, fields and matching procedures are documented in [`DATA_PROVENANCE.md`](DATA_PROVENANCE.md). The principal revision outputs are in [`outputs/referee_revision_v3/`](outputs/referee_revision_v3/).

## Reproduce

```bash
conda env create -f environment.yml
conda activate sourceaware-dd-2.0.0
bash run_all.sh
```

## Archive and citation

Repository: <https://github.com/Marchematics/materials-stability-label-discordance>

Zenodo concept DOI: <https://doi.org/10.5281/zenodo.21313779>

Citation metadata are in [`CITATION.cff`](CITATION.cff).

## License

MIT License. Upstream data retain their original terms of use.
