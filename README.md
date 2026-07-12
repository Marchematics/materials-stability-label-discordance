# SourceAware-Stability

Data, code and figure-source files for the study **“Source-aware stability labels
reshape AI crystal-discovery benchmarks.”**

## What this repository contains

This repository provides a reproducible evaluation framework for examining how
published crystal-stability labels affect reported model performance and
screening conclusions. It contains exact-structure denominator tables,
source-native and diagnostic label views, model-score evaluations, discovery
curves, benchmark cards, figure-source tables and integrity tests.

The primary article analyses a common exact-structure denominator across three
explicitly distinguished public sources:

- **Materials Project (MP)**;
- **MatterGen alex-mp-20**, the Alex-MP data release distributed with Microsoft
  MatterGen. This is not an unmodified official Alexandria label table;
- **official Alexandria-PBE**, obtained separately from the Alexandria
  Materials Database.

The provenance record in [`DATA_PROVENANCE.md`](DATA_PROVENANCE.md) specifies
snapshots, fields, matching rules and label definitions for each source.

## Scope of the released evidence

The article reports source-aware benchmark diagnostics. Source-native,
common-pool, source-union, consensus and audit labels are evaluation views, not
physical-truth labels. The release does not provide homogeneous-DFT referee
labels, validate generated materials, or claim a complete source-union hull.

The primary exact model comparison includes ALIGNN-FF, CHGNet, M3GNet and
MACE-MP on 36,801 commonly mapped structures. Other model artefacts are
retained as documented external context and are not used for the primary
real-model rank claims.

## Repository layout

- `sourceaware/` — benchmark, label-view and evaluation implementation;
- `outputs/phase1_v2/` — frozen source-aware benchmark tables and cards;
- `outputs/phase2_v1/` — model-facing evaluation outputs and candidate
  provenance audits;
- `outputs/dd_submission_v2/` — manuscript claim ledger, figure-source tables,
  vector figures, TIFF exports and checksums;
- `scripts/` and `tests/` — regeneration scripts and integrity tests.

## Reproduce the release

```bash
conda env create -f environment.yml
conda activate sourceaware-dd-2.0.0
bash run_all.sh
```

`run_all.sh` rebuilds the release checks, benchmark card, figure-source data,
publication figures, manifests and the frozen test suite. Figure 1 and Figure 2
use an explicitly attributed, MIT-licensed visual reference from Matbench
Discovery; all numerical results are calculated from the tables in this
repository.

## Citation

Please cite the software record for the tagged release and the associated
article. Citation metadata are provided in [`CITATION.cff`](CITATION.cff). The
Zenodo record for the current submission release will be linked here once its
archive DOI has been issued.

## License

The code in this repository is released under the MIT License. Upstream data
remain subject to the terms of their original providers.
