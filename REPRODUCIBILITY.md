# Reproducibility guide

## Reproducing the submission release

The submission release uses the source-aware benchmark and model-facing
evaluation outputs described in the article.

Create the pinned environment with either:

```bash
conda env create -f environment.yml
conda activate sourceaware-dd-2.0.0
```

or:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
```

Regenerate cards, figures, claims, manifests and tests with:

```bash
bash run_all.sh
```

Every quantitative panel has a source CSV (and, for all-rank discovery
curves, parquet) under `outputs/dd_submission_v2/figure_source_data/`.
Submission figures are vector PDF plus 600-dpi TIFF. The rolling-window
metadata records the interval method, support threshold, seed and iterations.
The clean-environment log is archived at
`outputs/dd_submission_v2/logs/clean_environment_regeneration.log`.

This repository contains scripts, derived tables, figure inputs and SHA256
manifests for the source-native stability-label audit. Raw third-party database
exports remain with their original providers.

## M1 model-evaluation archive

The primary model-facing tables are in
`outputs/repaired_model_evaluation_v1/`. The archive includes
`score_construct_validity_audit.csv`, `evaluation_support_and_coverage.csv`,
`metrics_fixed_support.csv`, `topk_fixed_support.csv`,
`label_bands_cluster_bootstrap.csv`, paired bootstrap replicates,
`elemental_reference_structures.jsonl`, and
`fixed_subsystem_phase_pool_manifest.json`.

Regenerate the figure files and verify the released archive with:

```bash
python scripts/build_repaired_model_figures.py
python scripts/audit_repaired_model_claims.py
pytest -q tests/test_repaired_model_evaluation.py tests/test_dd_submission_curves.py
python scripts/build_repaired_release_manifest.py
```

The corresponding command logs and environment checksums are stored in
`outputs/repaired_model_evaluation_v1/reproducibility/`.

## Environment

Install the analysis dependencies:

```bash
pip install -r requirements.txt
```

Run repository tests:

```bash
pytest -q tests
```

## Integrity checks

Each milestone directory contains a local SHA256 manifest. Verify a milestone
from its directory, for example:

```bash
cd outputs/milestones/official_alexandria_pbe_extension
sha256sum -c MANIFEST_SHA256.txt
```

The root manifest can be checked from the repository root:

```bash
sha256sum -c MANIFEST_SHA256.txt
```

## Official Alexandria-PBE extension

The official Alexandria-PBE extension has two stages.

1. Feasibility and denominator construction:

```bash
python scripts/build_official_alexandria_pbe_feasibility.py
```

This stage requires the official Alexandria-PBE complete 3D JSON snapshot
`2025.07.02` under:

```text
raw/official_alexandria_pbe/
```

The `raw/` directory is intentionally ignored by Git. The script validates the
complete PBE 3D snapshot, checks `entries[].data.e_above_hull` coverage and
builds formula-prefiltered exact-structure matches to the strict
MP--alex-mp-20 denominator. It does not use MP identifiers to join official
Alexandria-PBE records.

2. Extension outputs:

```bash
python scripts/build_official_alexandria_pbe_extension_outputs.py
```

This stage reads the feasibility outputs and writes:

- cutoff-grid pairwise source-conflict burdens;
- source-conflict directionality;
- three-source label composition;
- alex-mp-20--official Alexandria-PBE source-native hull-value differences;
- chemistry-stratified chemical-system bootstrap intervals;
- fixed source-native ranking uncertainty bands;
- fixed CHGNet score ranking uncertainty bands when the optional score table is present;
- figure-source inputs;
- SHA256 manifest.

Verify the generated outputs:

```bash
sha256sum -c outputs/milestones/official_alexandria_pbe_extension/MANIFEST_SHA256.txt
```

## Main MP--alex-mp-20 denominator

The primary MP--alex-mp-20 denominator can be rebuilt with:

```bash
python scripts/run_full_mp_alex_denominator_43984.py
```

Rebuilding this stage requires Materials Project API access via `MP_API_KEY`.
Live API behaviour and database contents can change, so the archived derived
tables are the reference outputs for the submitted analysis.

## JARVIS-DFT extension

The JARVIS extension can be rebuilt with:

```bash
python scripts/build_jarvis_multisource_extension.py
```

The script queries the public JARVIS OPTIMADE endpoint and writes
denominator, pairwise source-conflict and three-source label-composition
tables. Formula matching is used only as a prefilter; reported rows require
exact structure matches.

## Interpretation

The analyses compare source-native public stability labels and report
common-pool, consensus and audit views as benchmark evaluations. A homogeneous
recalculation or prospective validation workflow can be layered onto these
released denominators in future studies.
