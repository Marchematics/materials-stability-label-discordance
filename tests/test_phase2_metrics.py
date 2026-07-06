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


def test_phase2_resampled_bootstrap_intervals_exist():
    boot = pd.read_csv(OUT / "model_metrics" / "metrics_by_model_label_view_bootstrap_resampled.csv")
    assert len(boot) > 0
    assert boot.bootstrap_method.eq("deterministic_row_resampling_phase2_v1").all()
    assert boot.bootstrap_replicates.ge(40).all()
    assert {"f1", "precision", "recall", "balanced_accuracy", "auroc", "auprc"}.issubset(set(boot.metric))
    assert {"mp_native", "alexmp20_native", "alex_pbe_native", "common_pool", "source_union", "consensus", "uncertain", "audit_view"}.issubset(set(boot.label_view))
    ok = boot[boot.metric_status.eq("ok")].copy()
    for col in ["value", "ci_low_95", "ci_high_95"]:
        vals = pd.to_numeric(ok[col], errors="coerce").dropna()
        assert ((0 <= vals) & (vals <= 1)).all()
    assert (pd.to_numeric(ok.ci_low_95, errors="coerce") <= pd.to_numeric(ok.ci_high_95, errors="coerce")).all()
    source_union = boot[boot.label_view.eq("source_union")]
    assert source_union.metric_status.eq("not_evaluable_full_source_union_incomplete").all()


def test_phase2_topk_bootstrap_intervals_exist():
    boot = pd.read_csv(OUT / "model_metrics" / "topk_by_model_label_view_bootstrap.csv")
    assert len(boot) > 0
    assert boot.bootstrap_method.eq("deterministic_binomial_topk_approximation_phase2_v1").all()
    assert {"precision@100", "recall@100", "stable_yield@100", "uncertain_fraction@100", "false_positive_burden@100", "DAF@100"}.issubset(set(boot.metric))
    assert {100, 300, 500, 1000, 5000, 10000}.issubset(set(pd.to_numeric(boot.K, errors="coerce").dropna().astype(int)))
    ok = boot[boot.metric_status.eq("ok")].copy()
    for col in ["value", "ci_low_95", "ci_high_95"]:
        vals = pd.to_numeric(ok[col], errors="coerce").dropna()
        assert ((0 <= vals) & (vals <= 1)).all()
    assert (pd.to_numeric(ok.ci_low_95, errors="coerce") <= pd.to_numeric(ok.ci_high_95, errors="coerce")).all()
    daf = boot[boot.metric.str.startswith("DAF@")]
    assert daf.metric_status.isin(["point_estimate_only_ratio_metric", "not_evaluable_full_source_union_incomplete", "uncertainty_indicator_not_primary_stability_metric"]).all()
