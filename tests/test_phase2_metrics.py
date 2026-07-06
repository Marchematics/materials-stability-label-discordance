from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "phase2_v1"


def test_phase2_metrics_cover_label_views_and_bounds():
    metrics = pd.read_csv(OUT / "model_metrics" / "metrics_by_model_label_view.csv")
    views = {"mp_native", "alexmp20_native", "alex_pbe_native", "common_pool", "source_union", "consensus", "uncertain", "audit_view"}
    assert views.issubset(set(metrics.label_view))
    source_union = metrics[metrics.label_view.eq("source_union")]
    assert source_union.metric_status.eq("not_evaluable_full_source_union_incomplete").all()
    ok = metrics[metrics.n > 0]
    for col in ["f1", "precision", "recall", "balanced_accuracy", "auroc", "auprc"]:
        vals = pd.to_numeric(ok[col], errors="coerce").dropna()
        assert ((0 <= vals) & (vals <= 1)).all()


def test_phase2_topk_and_uncertainty_ratio():
    topk = pd.read_csv(OUT / "model_metrics" / "topk_by_model_label_view.csv")
    views = {"mp_native", "alexmp20_native", "alex_pbe_native", "common_pool", "source_union", "consensus", "uncertain", "audit_view"}
    assert views.issubset(set(topk.label_view))
    assert {100, 300, 500, 1000, 5000, 10000}.issubset(set(topk.K))
    source_union = topk[topk.label_view.eq("source_union")]
    assert source_union.metric_status.eq("not_evaluable_full_source_union_incomplete").all()
    vals = topk.stable_yield_at_k.dropna()
    assert ((0 <= vals) & (vals <= 1)).all()
    ratio = pd.read_csv(OUT / "model_metrics" / "model_margin_to_label_uncertainty_ratio.csv")
    assert "uncertainty_dominance_ratio" in ratio.columns
    assert (pd.to_numeric(ratio.uncertainty_dominance_ratio, errors="coerce") > 1).any()
