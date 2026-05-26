from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
RELEASE_NAME = "discordance-npjcompmat-data-code-2026-05-26"
RELEASE_ROOT = ROOT / "releases" / "zenodo" / RELEASE_NAME
ZIP_PATH = RELEASE_ROOT.with_suffix(".zip")


COPY_FILES = [
    "outputs/milestones/materials_label_discordance_full_mp_alex_43984/FULL_MP_ALEX_DENOMINATOR_CLOSEOUT.md",
    "outputs/milestones/materials_label_discordance_full_mp_alex_43984/MANIFEST_SHA256.txt",
    "outputs/milestones/materials_label_discordance_full_mp_alex_43984/table_full_denominator_source_counts.csv",
    "outputs/milestones/materials_label_discordance_full_mp_alex_43984/table_full_mp_alex_denominator_summary.csv",
    "outputs/milestones/materials_label_discordance_full_mp_alex_43984/table_full_mp_alex_match_status_counts.csv",
    "outputs/milestones/materials_label_discordance_full_mp_alex_43984/table_full_mp_alex_missing_mp_record_audit.csv",
    "outputs/milestones/materials_label_discordance_full_mp_alex_43984/table_full_mp_alex_structure_matches.csv",
    "outputs/milestones/materials_label_discordance_full_mp_alex_43984/table_major_revision_chemistry_stratified_discordance.csv",
    "outputs/milestones/materials_label_discordance_full_mp_alex_43984/table_major_revision_cluster_bootstrap_ci.csv",
    "outputs/milestones/materials_label_discordance_full_mp_alex_43984/table_major_revision_direction_delta_distribution.csv",
    "outputs/milestones/materials_label_discordance_full_mp_alex_43984/table_major_revision_missing_mp_record_bias.csv",
    "outputs/milestones/benchmark_impact_label_source_choice/BENCHMARK_IMPACT_LABEL_SOURCE_CHOICE_CLOSEOUT.md",
    "outputs/milestones/benchmark_impact_label_source_choice/MANIFEST_SHA256.txt",
    "outputs/milestones/benchmark_impact_label_source_choice/table_conflict_excluded_denominator_metrics.csv",
    "outputs/milestones/benchmark_impact_label_source_choice/table_label_confusion_matrix_full_denominator.csv",
    "outputs/milestones/benchmark_impact_label_source_choice/table_metric_shift_interpretation.csv",
    "outputs/milestones/benchmark_impact_label_source_choice/table_perfect_source_labeler_cross_evaluation.csv",
    "outputs/milestones/benchmark_impact_label_source_choice/table_source_native_ranking_topk_stable_yield.csv",
    "outputs/milestones/model_facing_benchmark_sensitivity_check/MANIFEST_SHA256.txt",
    "outputs/milestones/model_facing_benchmark_sensitivity_check/MODEL_FACING_BENCHMARK_SENSITIVITY_CHECK.md",
    "outputs/milestones/model_facing_benchmark_sensitivity_check/candidate_scores_chgnet_5000.csv",
    "outputs/milestones/model_facing_benchmark_sensitivity_check/table_chgnet_sample_representativeness.csv",
    "outputs/milestones/model_facing_benchmark_sensitivity_check/table_chgnet_score_direction_sanity.csv",
    "outputs/milestones/model_facing_benchmark_sensitivity_check/table_chgnet_scored_subset_manifest.csv",
    "outputs/milestones/model_facing_benchmark_sensitivity_check/table_model_metric_source_sensitivity.csv",
    "outputs/milestones/model_facing_benchmark_sensitivity_check/table_precision_at_k_metric_shift.csv",
    "outputs/milestones/model_facing_benchmark_sensitivity_check/table_precision_at_k_source_sensitivity.csv",
    "outputs/milestones/model_facing_benchmark_sensitivity_check/table_precision_shift_bootstrap.csv",
    "outputs/milestones/model_facing_benchmark_sensitivity_check/table_topk_discordance_decomposition.csv",
    "outputs/publication/source_data/table_conflict_excluded_denominator_metrics.csv",
    "outputs/publication/source_data/table_major_revision_chemistry_stratified_discordance.csv",
    "outputs/publication/source_data/table_precision_at_k_source_sensitivity.csv",
    "outputs/publication/source_data/table_precision_shift_bootstrap.csv",
    "outputs/publication/tables/table_claim_boundaries.csv",
    "outputs/publication/tables/table_source_aware_benchmark_card.csv",
    "outputs/milestones/materials_label_discordance_preregistration/table_fig2_delta_e_binned_discordance.csv",
    "outputs/milestones/materials_label_discordance_preregistration/table_fig2_delta_e_quantiles.csv",
    "outputs/milestones/materials_label_discordance_preregistration/table_fig2_delta_e_summary.csv",
    "outputs/milestones/materials_label_discordance_preregistration/table_fig2_delta_e_tail_thresholds.csv",
    "outputs/milestones/materials_label_discordance_preregistration/table_mp_alex_ehull_scatter_source.csv",
    "outputs/milestones/materials_label_discordance_preregistration/table_source_label_value_clipping.csv",
    "outputs/milestones/materials_label_discordance_preregistration/table_uncertainty_threshold_sweep.csv",
    "scripts/analyze_revised_fig2_energy_difference.py",
    "scripts/build_benchmark_impact_label_source_choice.py",
    "scripts/build_major_revision_diagnostics.py",
    "scripts/build_manuscript_figures.py",
    "scripts/build_model_facing_benchmark_sensitivity_check.py",
    "scripts/run_full_mp_alex_denominator_43984.py",
    "tests/test_data_code_release_artifacts.py",
]

FIGURE_FILES = [
    "fig.pdf",
    "fig1_pipeline.pdf",
    "fig1_pipeline.png",
    "fig2_delta_e.pdf",
    "fig2_delta_e.png",
    "fig3_benchmark_impact.pdf",
    "fig3_benchmark_impact.png",
    "fig4_chemical_stratification.pdf",
    "fig4_chemical_stratification.png",
]


README = """# Source-native stability-label uncertainty in crystal discovery benchmarks: data and code

This Zenodo package contains the public-safe data tables, source data, analysis
scripts, generated figures and integrity tests that support the manuscript
"Source-native stability-label uncertainty in crystal discovery benchmarks".

This is a supporting data/code archive, not a manuscript archive. It
intentionally excludes manuscript text files, compiled manuscript PDFs, cover
letters and other journal-submission documents.

## Main results supported by this package

- 43,139 strict Materials Project--Alexandria structure matches retained from
  43,984 Alexandria rows carrying Materials Project identifiers.
- 5,060 matched structures have discordant source-native binary stability
  labels, giving an 11.7% source-conflict rate.
- Chemical-system cluster-bootstrap 95% interval: 11.3--12.1%.
- Near-hull flags are reporting-burden diagnostics in the clipped public-label
  representation.
- A fixed CHGNet 5,000-structure ranking diagnostic shows MP-minus-Alexandria
  precision@300/500 shifts of 4.3/3.6 percentage points.

## Contents

```text
outputs/milestones/materials_label_discordance_full_mp_alex_43984/
  full MP--Alexandria denominator tables and uncertainty summaries

outputs/milestones/benchmark_impact_label_source_choice/
  oracle label-transfer and conflict-exclusion diagnostics

outputs/milestones/model_facing_benchmark_sensitivity_check/
  CHGNet 5,000-structure fixed-ranking sensitivity outputs

outputs/publication/
  publication-facing source data and claim-boundary tables

outputs/milestones/materials_label_discordance_preregistration/
  selected figure-2 and near-hull reporting-burden source tables

figures/
  generated main-figure files for audit and reuse

manuscript/figures/fig.pdf
  hand-prepared Fig. 1 source used by the figure-building script

scripts/
  public-safe analysis and figure-generation scripts

tests/
  data-code package integrity tests
```

## Data and code availability

The raw Materials Project structure cache used during denominator construction
is a local API cache and is not redistributed. Public-safe matched summary
tables can be regenerated from public source records using the archived scripts,
subject to the Materials Project API terms.
"""


DATA_AVAILABILITY = """# Data Availability

The matched summary tables, figure source data and derived public-safe analysis
outputs used in the manuscript are archived in this Zenodo data/code package.

The package contains:

- full Materials Project--Alexandria denominator outputs;
- chemistry-stratified diagnostics and cluster-bootstrap summaries;
- cross-source hull-energy and near-threshold reporting-burden diagnostics;
- oracle label-transfer and conflict-excluded denominator diagnostics;
- CHGNet 5,000-structure model-facing sensitivity outputs;
- publication-facing source-data tables, generated figures, file lists and
  SHA256 manifests.

The raw Materials Project structure cache used during denominator construction
is a local API cache and is not redistributed. Public-safe matched summary
tables can be regenerated from public source records using the archived scripts,
subject to the Materials Project API terms.
"""


CODE_AVAILABILITY = """# Code Availability

The code used to generate the full denominator, analysis tables, figures and
model-facing sensitivity diagnostics is archived in this Zenodo data/code
package and is also available in the public development repository:

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
scripts/build_manuscript_figures.py
```

Integrity tests are under `tests/` and can be run with:

```bash
pytest -q tests
```
"""


REPRODUCIBILITY = """# Reproducibility

This archive is a public-safe supporting data/code package for the npj
Computational Materials submission. It does not contain the manuscript text or
compiled manuscript PDF.

## Environment

The analysis scripts are Python-based and use standard scientific Python
packages including `pandas`, `numpy`, `matplotlib`, `scipy`, `pymatgen` and
model-specific packages for the archived CHGNet sensitivity diagnostic.

## Main checks

```bash
pytest -q tests
```

The figure-generation script can be run from the package root:

```bash
python scripts/build_manuscript_figures.py
```

It writes regenerated figure files under `manuscript/figures/` because that is
the path expected by the original manuscript workflow. The manuscript source
itself is intentionally not part of this data/code archive.

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
"""


RELEASE_NOTES = """# Zenodo data/code release

This package supports the npj Computational Materials submission draft for
"Source-native stability-label uncertainty in crystal discovery benchmarks".

Package scope: public-safe supporting data and code only.

The package intentionally excludes manuscript text files, compiled manuscript
PDFs, cover letters, reviewer-facing submission documents, local API caches,
exploratory history logs and internal decision documents.
"""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_file(relative_path: str) -> None:
    src = ROOT / relative_path
    if not src.exists():
        raise FileNotFoundError(relative_path)
    dst = RELEASE_ROOT / relative_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def write_text(relative_path: str, text: str) -> None:
    path = RELEASE_ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_metadata() -> None:
    metadata = {
        "title": "Source-native stability-label uncertainty in crystal discovery benchmarks: supporting data and code",
        "upload_type": "dataset",
        "description": (
            "Public-safe data tables, source data, analysis scripts, generated "
            "figures and integrity tests supporting a benchmark-reliability "
            "audit of Materials Project--Alexandria source-native stability-label "
            "discordance."
        ),
        "creators": [
            {
                "name": "Wen, Xinling",
                "affiliation": "School of Electronics and Information, Zhengzhou University of Aeronautics",
            },
            {
                "name": "Zhang, Jiahao",
                "affiliation": "School of Electronics and Information, Zhengzhou University of Aeronautics",
            },
            {
                "name": "Chen, Yu",
                "affiliation": "School of Electronics and Information, Zhengzhou University of Aeronautics",
            },
            {
                "name": "Hou, Yawei",
                "affiliation": "Zhengzhou University of Aeronautics",
                "orcid": "0009-0001-3975-2707",
            },
        ],
        "access_right": "open",
        "license": "cc-by-4.0",
        "keywords": [
            "crystal stability",
            "materials databases",
            "density functional theory",
            "benchmark uncertainty",
            "Materials Project",
            "Alexandria",
        ],
        "notes": "This is a data/code archive and intentionally excludes manuscript and journal-submission files.",
    }
    write_text("ZENODO_METADATA_DRAFT.json", json.dumps(metadata, indent=2))


def build_manifest() -> None:
    write_text("RELEASE_FILE_LIST.txt", "\n".join(f"./{p.relative_to(RELEASE_ROOT).as_posix()}" for p in sorted(RELEASE_ROOT.rglob("*")) if p.is_file() and p.name != "RELEASE_FILE_LIST.txt"))
    rows = []
    for path in sorted(RELEASE_ROOT.rglob("*")):
        if not path.is_file() or path.name == "MANIFEST_SHA256.txt":
            continue
        rel = path.relative_to(RELEASE_ROOT).as_posix()
        rows.append(f"{sha256_file(path)}  ./{rel}")
    write_text("MANIFEST_SHA256.txt", "\n".join(rows))


def build_zip() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with ZipFile(ZIP_PATH, "w", ZIP_DEFLATED) as zf:
        for path in sorted(RELEASE_ROOT.rglob("*")):
            if path.is_file():
                zf.write(path, f"{RELEASE_NAME}/{path.relative_to(RELEASE_ROOT).as_posix()}")
    ZIP_PATH.with_suffix(".zip.sha256").write_text(f"{sha256_file(ZIP_PATH)}  {ZIP_PATH.name}\n", encoding="utf-8")


def main() -> None:
    if RELEASE_ROOT.exists():
        shutil.rmtree(RELEASE_ROOT)
    RELEASE_ROOT.mkdir(parents=True)

    for relative_path in COPY_FILES:
        copy_file(relative_path)

    for figure in FIGURE_FILES:
        src = ROOT / "manuscript" / "figures" / figure
        if not src.exists():
            raise FileNotFoundError(src)
        dst = RELEASE_ROOT / "figures" / figure
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    if (ROOT / "manuscript" / "figures" / "fig.pdf").exists():
        copy_file("manuscript/figures/fig.pdf")

    write_text("README.md", README)
    write_text("DATA_AVAILABILITY.md", DATA_AVAILABILITY)
    write_text("CODE_AVAILABILITY.md", CODE_AVAILABILITY)
    write_text("REPRODUCIBILITY.md", REPRODUCIBILITY)
    write_text("RELEASE_NOTES.md", RELEASE_NOTES)
    write_metadata()
    build_manifest()
    build_zip()

    print(RELEASE_ROOT)
    print(ZIP_PATH)
    print(sha256_file(ZIP_PATH))


if __name__ == "__main__":
    main()
