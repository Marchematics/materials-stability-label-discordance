# SourceAware-Stability

**The choice of stability reference changes what crystal-discovery benchmarks count as success.**

The same crystal can receive different stability labels across materials databases. On a fixed set of 36,650 candidates, the same MACE-MP ranking recovers 759 stable hits under Materials Project and 598 under Alexandria-PBE at a budget of 1,000. Across the four evaluated models, MACE-MP leads the three full-ranking metrics under all five stability definitions, while discovery counts change.

[Paper](manuscript/main.pdf) · [Supplementary Information](manuscript/supplementary_information.pdf) · [Latest release](https://github.com/Marchematics/materials-stability-label-discordance/releases/latest) · [Reproduce the figures](REPRODUCIBILITY.md)

## Results

| Comparison | Result |
|---|---|
| Labels across Materials Project, MatterGen alex-mp-20 and Alexandria-PBE | 10.5–15.4% pairwise switching at zero threshold among 36,802 matched structures |
| Labels at a 50 meV/atom threshold | 6.5–8.9% pairwise switching |
| MP–Alexandria original conflicts after sharing the competing-phase inventory | 3,659 of 5,661 reconstructable conflicts resolve (64.6%) |
| Four fixed rankings, 1,000 selections, three database references | 554–759 source-defined stable hits |

## Files

- [`manuscript/`](manuscript/): paper, supplementary information, LaTeX sources and six figures.
- [`outputs/publication/figure_source_tables/`](outputs/publication/figure_source_tables/): data used by the current figures.
- [`outputs/referee_revision_v3/`](outputs/referee_revision_v3/): matched labels, model scores, shared-inventory results and evaluation tables.
- [`outputs/referee_revision_v3/alternative_clustering_bootstrap/`](outputs/referee_revision_v3/alternative_clustering_bootstrap/): chemical-system, reduced-formula and structural-equivalence bootstrap summaries.
- [`DATA_PROVENANCE.md`](DATA_PROVENANCE.md): database versions, fields and structural matching.

## Run

```bash
conda env create -f environment.yml
conda activate sourceaware-dd-2.0.0
bash run_all.sh
```

This regenerates the current figures and runs the ranking and evaluation tests. LaTeX build commands and analysis instructions are in [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md).

## Cite

Citation metadata are in [`CITATION.cff`](CITATION.cff). Version history is in [`CHANGELOG.md`](CHANGELOG.md); archived versions are linked through the [Zenodo record](https://doi.org/10.5281/zenodo.21313779).

## License

Code: MIT. Database records retain their providers' terms, documented in [`DATA_PROVENANCE.md`](DATA_PROVENANCE.md).
