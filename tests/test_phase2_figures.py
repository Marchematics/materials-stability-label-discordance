from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "phase2_v1"


def test_phase2_all_figure_files_and_source_tables_exist():
    figs = OUT / "figures"
    src = OUT / "figure_source_data"
    for stem in [
        "fig1_leaderboard_bands",
        "fig2_uncertainty_vs_spread",
        "fig3_rank_inversions",
        "fig4_topk_heatmap",
        "fig5_generated_consequence",
        "fig6_workflow",
    ]:
        for suffix in [".svg", ".pdf"]:
            path = figs / f"{stem}{suffix}"
            assert path.exists(), path
            assert path.stat().st_size > 1000, path
    for csv_name in [
        "fig1_leaderboard_bands.csv",
        "fig2_uncertainty_vs_spread.csv",
        "fig3_rank_inversions.csv",
        "fig4_topk_heatmap.csv",
        "fig5_generated_consequence.csv",
        "fig6_workflow.csv",
    ]:
        path = src / csv_name
        assert path.exists(), path
        df = pd.read_csv(path)
        assert len(df) > 0, path
