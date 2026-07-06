from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "phase2_v1"


def test_phase2_denominator_definitions_are_nonempty():
    full = pd.read_parquet(OUT / "denominators" / "denominator_d5_full_complete.parquet")
    family = pd.read_parquet(OUT / "denominators" / "denominator_d5_family_complete.parquet")
    pairwise = pd.read_parquet(OUT / "denominators" / "denominator_d5_pairwise_complete.parquet")
    maxcov = pd.read_parquet(OUT / "denominators" / "denominator_d5_max_coverage_by_model.parquet")
    audit = pd.read_csv(OUT / "denominators" / "model_denominator_audit.csv")
    assert len(full) >= 36000
    assert len(family) >= 36000
    assert {"model_a", "model_b", "row_id"}.issubset(pairwise.columns)
    assert pairwise.groupby(["model_a", "model_b"]).size().min() >= 36000
    assert maxcov.model_name.nunique() >= 10
    assert audit.d5_full_complete_n.iloc[0] == len(full)
