from pathlib import Path
import sys
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sourceaware.phase2.pipeline import rank_inversions

OUT = ROOT / "outputs" / "phase2_v1"


def test_phase2_rank_inversion_outputs_exist():
    inv = pd.read_csv(OUT / "rank_inversions" / "all_rank_inversions.csv")
    assert {"label_view_a", "label_view_b", "rank_inversion_count", "top_model_inversion"}.issubset(inv.columns)
    assert (inv.rank_inversion_count >= 0).all()
    assert (OUT / "rank_inversions" / "family_level_inversions.csv").exists()
    assert (OUT / "rank_inversions" / "budget_dependent_inversions.csv").exists()


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
