from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "phase2_v1"


def test_phase2_score_inventory_standardized_and_sufficient():
    inv = pd.read_csv(OUT / "model_scores" / "model_score_inventory.csv")
    assert len(inv[inv.score_status.eq("scored")]) >= 10
    assert inv[inv.score_status.eq("scored")].model_family.nunique() >= 4
    required = {
        "model_name", "model_family", "input_type", "training_data", "score_type",
        "score_direction", "coverage_n", "missing_n", "whether_calibrated_energy",
        "whether_hull_distance", "source_of_score", "include_in_primary_leaderboard",
    }
    assert required.issubset(inv.columns)
    assert inv.score_direction.eq("descending_higher_score_first").all()
    assert "external_score_rows_n" in inv.columns
    assert pd.to_numeric(inv.external_score_rows_n, errors="coerce").fillna(0).sum() > 500_000
    external = pd.read_parquet(OUT / "model_scores" / "matbench_external_scores_long.parquet")
    assert len(external) > 500_000
    audit = pd.read_csv(OUT / "model_scores" / "matbench_external_score_audit.csv")
    assert (audit.external_score_status == "downloaded_external_unmapped").any()
    scores = pd.read_parquet(OUT / "model_scores" / "all_model_scores_long.parquet")
    assert scores.score_standardized.notna().all()
    assert scores.score_direction_standardized.eq("higher_score_more_likely_stable").all()
