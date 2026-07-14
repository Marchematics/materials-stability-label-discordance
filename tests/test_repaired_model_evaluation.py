from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "repaired_model_evaluation_v1"


def test_m1_support_and_consensus_selection_are_separate():
    coverage = pd.read_csv(OUT / "evaluation_support_and_coverage.csv")
    fixed = coverage[coverage["evaluation_type"].eq("label_only_fixed_support")]
    assert set(fixed["n"]) == {31872}
    consensus = coverage[coverage["view"].eq("consensus")].iloc[0]
    assert consensus["n"] == 24614
    assert 31872 - 24614 == 7258


def test_raw_energy_failure_and_predicted_hull_repair_are_explicit():
    audit = pd.read_csv(OUT / "score_construct_validity_audit.csv")
    assert (audit["raw_energy_rank_auroc_mp_native"] < 0.5).all()
    assert (audit["predicted_hull_rank_auroc_mp_native"] > 0.5).all()
    assert audit["raw_score_use"].str.startswith("excluded_").all()


def test_paired_bootstrap_products_are_complete():
    deltas = pd.read_csv(OUT / "paired_label_view_differences_cluster_bootstrap.csv")
    wins = pd.read_csv(OUT / "model_winner_probabilities_cluster_bootstrap.csv")
    assert {"point_delta_a_minus_b", "bootstrap_ci_low_95", "bootstrap_ci_high_95", "probability_delta_gt_zero"}.issubset(deltas.columns)
    assert (deltas["bootstrap_replicates"] == 1000).all()
    assert (wins["bootstrap_replicates"] == 1000).all()
    assert wins["winner_probability"].between(0, 1).all()
