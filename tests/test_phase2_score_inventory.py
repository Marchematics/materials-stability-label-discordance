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
    assert pd.to_numeric(inv.external_score_rows_n, errors="coerce").fillna(0).sum() > 1_500_000
    assert "external_formula_overlap_rows_n" in inv.columns
    assert pd.to_numeric(inv.external_formula_overlap_rows_n, errors="coerce").fillna(0).sum() > 0
    assert {"eSEN-30M-MP", "MEGNet-RS2RE"}.issubset(set(inv.model_name))
    external = pd.read_parquet(OUT / "model_scores" / "matbench_external_scores_long.parquet")
    assert len(external) > 1_500_000
    assert {"raw_github_csv_gz"}.issubset(set(external.source_artifact_kind))
    audit = pd.read_csv(OUT / "model_scores" / "matbench_external_score_audit.csv")
    assert (audit.external_score_status == "downloaded_external_unmapped").sum() >= 7
    assert (audit.external_score_status.str.contains("figshare_download_unavailable_http_403")).any()
    formula_audit = pd.read_csv(OUT / "model_scores" / "matbench_external_formula_overlap_audit.csv")
    assert len(formula_audit) >= 7
    assert formula_audit.mapping_status.eq("formula_overlap_only_no_exact_structure_mapping").all()
    assert formula_audit.formula_overlap_rows_n.sum() > 0
    assert formula_audit.guardrail.str.contains("never used for SourceAware", regex=False).all()
    target_audit = pd.read_csv(OUT / "model_scores" / "matbench_target_prediction_artifact_audit.csv")
    assert {"ALIGNN", "Wrenformer", "BOWSR", "SevenNet", "ORB", "EquiformerV2+DeNS"}.issubset(set(target_audit.model_name))
    scores = pd.read_parquet(OUT / "model_scores" / "all_model_scores_long.parquet")
    assert scores.score_standardized.notna().all()
    assert scores.score_direction_standardized.eq("higher_score_more_likely_stable").all()


def test_external_wbm_native_metrics_are_context_only_not_sourceaware():
    metrics = pd.read_csv(OUT / "model_scores" / "external_wbm_native_metrics.csv")
    topk = pd.read_csv(OUT / "model_scores" / "external_wbm_native_topk.csv")
    assert len(metrics) >= 7
    assert metrics.model_name.nunique() >= 7
    assert topk.model_name.nunique() == metrics.model_name.nunique()
    assert {100, 300, 500, 1000, 5000, 10000}.issubset(set(pd.to_numeric(topk.K, errors="coerce").astype(int)))
    assert metrics.evaluation_scope.eq("external_wbm_native_context_only").all()
    assert topk.evaluation_scope.eq("external_wbm_native_context_only").all()
    assert metrics.guardrail.str.contains("not SourceAware label-view evidence", regex=False).all()
    assert topk.guardrail.str.contains("not SourceAware label-view evidence", regex=False).all()
    for col in ["f1", "precision", "recall", "balanced_accuracy", "auroc", "auprc"]:
        vals = pd.to_numeric(metrics[col], errors="coerce").dropna()
        assert ((0 <= vals) & (vals <= 1)).all()
    sy = pd.to_numeric(topk.stable_yield_at_k, errors="coerce").dropna()
    assert ((0 <= sy) & (sy <= 1)).all()
    inv = pd.read_csv(OUT / "model_scores" / "model_score_inventory.csv")
    assert "external_wbm_native_metric_status" in inv.columns
    assert inv.external_wbm_native_metric_status.eq("computed_context_only_not_sourceaware").sum() >= 7
    sourceaware_metrics = pd.read_csv(OUT / "model_metrics" / "metrics_by_model_label_view.csv")
    external_only_models = set(metrics.model_name) - set(inv[inv.score_status.eq("scored")].model_name)
    assert external_only_models.isdisjoint(set(sourceaware_metrics.model_name))
