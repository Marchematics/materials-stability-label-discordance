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


def test_phase2_pairwise_and_max_coverage_denominators_are_self_describing():
    pairwise = pd.read_parquet(OUT / "denominators" / "denominator_d5_pairwise_complete.parquet")
    maxcov = pd.read_parquet(OUT / "denominators" / "denominator_d5_max_coverage_by_model.parquet")
    required = {"row_id", "mp_id", "formula", "chemical_system", "structure_hash", "denominator"}
    assert required.issubset(pairwise.columns)
    assert required.issubset(maxcov.columns)
    assert pairwise.denominator.eq("D5_pairwise_complete").all()
    assert maxcov.denominator.eq("D5_max_coverage_by_model").all()
    assert pairwise[["mp_id", "formula", "chemical_system", "structure_hash"]].notna().all().all()
    assert maxcov[["mp_id", "formula", "chemical_system", "structure_hash"]].notna().all().all()
    audit = pd.read_csv(OUT / "denominators" / "model_denominator_audit.csv")
    for col in ["pairwise_overlap_median_n", "pairwise_overlap_max_n", "d5_max_coverage_n_for_model", "is_d5_family_representative", "d5_full_complete_missing_n_for_model"]:
        assert col in audit.columns
    scored = audit[audit.score_status.eq("scored")]
    assert pd.to_numeric(scored.d5_max_coverage_n_for_model, errors="coerce").gt(0).all()
    assert scored.is_d5_family_representative.astype(bool).any()
