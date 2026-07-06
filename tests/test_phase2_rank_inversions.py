from pathlib import Path
import sys
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sourceaware.phase2.pipeline import rank_inversions

OUT = ROOT / "outputs" / "phase2_v1"


def test_phase2_rank_inversion_outputs_exist():
    lb = pd.read_csv(OUT / "leaderboard" / "sourceaware_leaderboard_alpha.csv")
    assert {"rank_mp_native", "rank_alexmp20_native", "rank_alex_pbe_native", "rank_common_pool", "rank_source_union", "rank_consensus", "rank_uncertain", "rank_audit_view"}.issubset(lb.columns)
    assert lb["rank_source_union"].isna().all()
    inv = pd.read_csv(OUT / "rank_inversions" / "all_rank_inversions.csv")
    assert {"label_view_a", "label_view_b", "rank_inversion_count", "top_model_inversion"}.issubset(inv.columns)
    assert (inv.rank_inversion_count >= 0).all()
    assert (OUT / "rank_inversions" / "family_level_inversions.csv").exists()
    assert (OUT / "rank_inversions" / "budget_dependent_inversions.csv").exists()
    real_audit = pd.read_csv(OUT / "rank_inversions" / "real_model_rank_claim_audit.csv")
    assert len(real_audit) > 0
    assert {"top_real_model_inversion", "claim_interpretation", "real_model_rank_inversion_count"}.issubset(real_audit.columns)
    assert real_audit.common_real_model_n.ge(4).all()
    assert real_audit.claim_interpretation.str.contains("real_model|lower_rank|stable", regex=True).all()
    real_rank = pd.read_csv(OUT / "model_metrics" / "real_model_rankings_by_label_view.csv")
    assert set(real_rank.model_name).issuperset({"ALIGNN-FF", "CHGNet", "MACE-MP", "M3GNet"})
    corr = pd.read_csv(OUT / "model_metrics" / "rank_correlation_by_label_view.csv")
    assert len(corr) > 0
    assert {"spearman_rank_correlation", "kendall_tau_b", "discordant_pair_fraction"}.issubset(corr.columns)
    ok = corr[corr.metric_status.eq("ok")]
    for col in ["spearman_rank_correlation", "kendall_tau_b"]:
        vals = pd.to_numeric(ok[col], errors="coerce").dropna()
        assert ((-1 <= vals) & (vals <= 1)).all()
    discord = pd.to_numeric(ok.discordant_pair_fraction, errors="coerce").dropna()
    assert ((0 <= discord) & (discord <= 1)).all()
    assert not set(corr.label_view_a).union(set(corr.label_view_b)).intersection({"source_union"})


def test_rank_inversion_toy_case(tmp_path):
    rankings = pd.DataFrame([
        {"denominator":"toy", "label_view":"a", "metric":"f1", "model_name":"m1", "metric_value":0.9, "rank":1},
        {"denominator":"toy", "label_view":"a", "metric":"f1", "model_name":"m2", "metric_value":0.8, "rank":2},
        {"denominator":"toy", "label_view":"b", "metric":"f1", "model_name":"m1", "metric_value":0.7, "rank":2},
        {"denominator":"toy", "label_view":"b", "metric":"f1", "model_name":"m2", "metric_value":0.95, "rank":1},
    ])
    inv = pd.DataFrame({"model_name":["m1","m2"], "model_family":["fam1","fam2"]})
    out = rank_inversions(rankings, inv, tmp_path)["all"]
    assert int(out.rank_inversion_count.iloc[0]) == 1
    assert bool(out.top_model_inversion.iloc[0]) is True
