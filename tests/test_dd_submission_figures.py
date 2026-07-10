from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "dd_submission_v2"


def test_dd_submission_figure_bundle_exists():
    qa = json.loads((OUT / "figure_qa.json").read_text())
    assert qa["status"] == "PASS"
    assert len(qa["figures"]) == 6
    for row in qa["figures"]:
        assert row["tiff_dpi"] == 600
        assert row["vector_pdf"] is True
        for key in ["pdf", "tiff"]:
            path = Path(row[key])
            assert path.exists()
            assert path.stat().st_size > 10_000
    assert len((OUT / "toc_text.txt").read_text().strip()) <= 250


def test_dd_figure_sources_exist_before_plot_contract():
    source = OUT / "figure_source_data"
    expected = [
        "fig1_exact_discovery_curves.csv",
        "fig1_exact_discovery_curves_all_ranks.parquet",
        "fig2_rolling_conflict_40mev.csv",
        "fig2_rolling_conflict_metadata.json",
        "fig3_conflict_decomposition.csv",
        "fig4_uncertainty_dominance.csv",
        "fig5_exact_matched_screened_candidates.csv",
        "toc_graphic_source.csv",
    ]
    for name in expected:
        path = source / name
        assert path.exists() and path.stat().st_size > 0
