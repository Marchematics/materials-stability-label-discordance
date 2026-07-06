from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "phase2_v1"


def test_phase2_pairwise_complete_margins_and_inversions():
    margins = pd.read_csv(OUT / "model_metrics" / "pairwise_complete_model_margins.csv")
    assert len(margins) > 10_000
    assert margins.denominator.eq("D5_pairwise_complete").all()
    required_metrics = {"f1", "auroc", "auprc", "precision@100", "recall@100", "stable_yield@100", "uncertain_fraction@100", "DAF@100"}
    assert required_metrics.issubset(set(margins.metric))
    assert {"mp_native", "alex_pbe_native", "common_pool", "source_union", "consensus", "audit_view"}.issubset(set(margins.label_view))
    source_union = margins[margins.label_view.eq("source_union")]
    assert source_union.winner.eq("not_evaluable").all()
    evaluable = margins[margins.winner.ne("not_evaluable")]
    assert {"model_a", "model_b", "margin_a_minus_b", "winner", "pairwise_n"}.issubset(margins.columns)
    assert pd.to_numeric(evaluable.pairwise_n, errors="coerce").gt(0).all()
    inv = pd.read_csv(OUT / "rank_inversions" / "pairwise_complete_label_dependent_inversions.csv")
    assert len(inv) > 0
    assert {"label_view_a", "label_view_b", "winner_a", "winner_b"}.issubset(inv.columns)
