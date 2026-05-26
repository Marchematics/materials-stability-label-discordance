from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


PUBLIC_TEXT_FILES = [
    ROOT / "README.md",
    ROOT / "REPRODUCIBILITY.md",
    ROOT / "DATA_AVAILABILITY.md",
    ROOT / "CODE_AVAILABILITY.md",
    ROOT / "submission" / "npj" / "cover_letter.md",
    ROOT / "submission" / "npj" / "significance_statement.md",
    ROOT / "submission" / "npj" / "reviewer_checklist.md",
    ROOT / "manuscript" / "main.tex",
]


def test_publication_facing_files_avoid_internal_route_language() -> None:
    forbidden = [
        "Route" + "-B",
        "Route" + " B",
        "ROUTE" + "_B",
        "SCS" + "/" + "PARC",
        "N" + "MI",
        "NO" + "_GO",
        "go" + "/" + "no-go",
        "launch" + " gate",
        "failed" + "-gate",
    ]
    for path in PUBLIC_TEXT_FILES:
        text = path.read_text(encoding="utf-8")
        for term in forbidden:
            assert term not in text, f"{term!r} leaked into {path}"


def test_publication_tables_exist_and_define_benchmark_card() -> None:
    card_path = ROOT / "outputs" / "publication" / "tables" / "table_source_aware_benchmark_card.csv"
    boundary_path = ROOT / "outputs" / "publication" / "tables" / "table_claim_boundaries.csv"
    assert card_path.exists()
    assert boundary_path.exists()

    card = pd.read_csv(card_path)
    required = {
        "label_source",
        "hull_reference",
        "stability_threshold",
        "matched_denominator_n",
        "source_conflict_fraction",
        "near_hull_flag_burden",
        "conflict_excluded_denominator_fraction",
        "model_readout_sensitivity",
        "recommended_reporting",
    }
    assert required.issubset(card.columns)
    assert int(card.iloc[0]["matched_denominator_n"]) == 43139
    assert 0.11 < float(card.iloc[0]["source_conflict_fraction"]) < 0.12

    boundaries = pd.read_csv(boundary_path)
    assert len(boundaries) >= 5
    assert {"issue", "what_this_study_shows", "what_this_study_does_not_show", "why"}.issubset(
        boundaries.columns
    )
