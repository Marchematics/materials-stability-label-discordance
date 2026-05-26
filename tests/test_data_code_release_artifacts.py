from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
IS_DATA_CODE_RELEASE = (ROOT / "ZENODO_METADATA_DRAFT.json").exists()


def test_primary_denominator_tables_support_main_claims() -> None:
    summary = pd.read_csv(
        ROOT
        / "outputs"
        / "milestones"
        / "materials_label_discordance_full_mp_alex_43984"
        / "table_full_mp_alex_denominator_summary.csv"
    ).iloc[0]
    assert int(summary["alex_mp_identifier_rows"]) == 43_984
    assert int(summary["strict_structure_matches"]) == 43_139
    assert int(summary["discordant_n"]) == 5_060
    assert 0.117 < float(summary["discordance_rate"]) < 0.118


def test_publication_source_data_and_benchmark_tables_exist() -> None:
    required = [
        ROOT / "outputs/publication/tables/table_source_aware_benchmark_card.csv",
        ROOT / "outputs/publication/tables/table_claim_boundaries.csv",
        ROOT / "outputs/publication/source_data/table_major_revision_chemistry_stratified_discordance.csv",
        ROOT / "outputs/publication/source_data/table_precision_at_k_source_sensitivity.csv",
        ROOT
        / "outputs/milestones/model_facing_benchmark_sensitivity_check"
        / "table_precision_shift_bootstrap.csv",
        ROOT
        / "outputs/milestones/benchmark_impact_label_source_choice"
        / "table_perfect_source_labeler_cross_evaluation.csv",
    ]
    missing = [str(path) for path in required if not path.exists()]
    assert missing == []

    card = pd.read_csv(required[0]).iloc[0]
    assert int(card["matched_denominator_n"]) == 43_139
    assert "source" in str(card["recommended_reporting"]).lower()


def test_release_excludes_manuscript_and_submission_materials() -> None:
    if not IS_DATA_CODE_RELEASE:
        return
    excluded = [
        ROOT / "manuscript/main.tex",
        ROOT / "manuscript/main.pdf",
        ROOT / "manuscript/references.bib",
        ROOT / "submission/npj/cover_letter.md",
    ]
    assert [str(path) for path in excluded if path.exists()] == []


def test_no_obvious_credentials_or_local_caches_are_packaged() -> None:
    if not IS_DATA_CODE_RELEASE:
        return
    forbidden_names = {
        ".DS_Store",
        ".pytest_cache",
        "__pycache__",
        ".git",
        "mp_records_summary_structures.jsonl",
    }
    bad_paths = []
    texts = []
    for path in ROOT.rglob("*"):
        if any(part in {".git", ".pytest_cache"} for part in path.parts):
            bad_paths.append(path)
            continue
        if "__pycache__" in path.parts:
            continue
        if path.name in forbidden_names:
            bad_paths.append(path)
            continue
        if path.is_file() and path.stat().st_size < 2_000_000:
            try:
                texts.append(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                continue
    assert [str(path) for path in bad_paths] == []
    combined = "\n".join(texts).lower()
    assert ("mp_api" + "_key=") not in combined
    assert ("token" + "=") not in combined
    assert ("secret" + "=") not in combined
