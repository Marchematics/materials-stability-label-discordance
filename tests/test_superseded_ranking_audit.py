from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "referee_revision_v3" / "superseded_ranking_audit"


def test_previous_top1000_was_entirely_inside_zero_score_ties() -> None:
    audit = pd.read_csv(OUT / "previous_self_included_hull_tie_audit.csv")
    top1000 = audit[audit.K.eq(1000)].set_index("model_name")
    assert top1000.boundary_score.eq(0).all()
    assert top1000.strictly_before_boundary_n.eq(0).all()
    assert top1000.boundary_tie_n.to_dict() == {
        "ALIGNN-FF": 15_688,
        "CHGNet": 19_190,
        "M3GNet": 17_178,
        "MACE-MP": 17_364,
    }


def test_previous_mace_mp_native_row_id_yield_exceeded_tie_interval() -> None:
    comparison = pd.read_csv(OUT / "previous_row_id_vs_analytic_tie_topk.csv")
    row = comparison[
        comparison.model_name.eq("MACE-MP")
        & comparison.endpoint.eq("mp_native")
        & comparison.K.eq(1000)
    ].iloc[0]
    assert row.row_id_selected_hits == 802
    assert row.expected_stable_hits < 710
    assert row.row_id_selected_hits > row.tie_interval_high_hits
