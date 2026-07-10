from __future__ import annotations

import json

from sourceaware.dd_submission import (
    build_claims,
    conflict_decomposition,
    denominator_summary,
    rank_flip_normalisation,
    write_claims_outputs,
)


def test_dd_denominator_names_and_counts():
    table = denominator_summary().set_index("set_id")
    assert "D0" not in table.index
    assert table.loc["F0", "n_rows"] == 34_962
    assert table.loc["D1", "n_rows"] == 43_139
    assert table.loc["D2", "n_rows"] == 36_802
    assert table.loc["D4", "n_rows"] == 36_802
    assert table.loc["D5", "n_rows"] == 36_801


def test_dd_conflict_decomposition_identities_close():
    values = conflict_decomposition().set_index("component")["n"]
    assert values["reconstructable_native"] == values["phase_pool_sensitive"] + values["persistent"]
    assert values["common_pool_conflicts"] == values["persistent"] + values["hidden_common_pool"]
    assert values["native_full"] == values["reconstructable_native"] + values["unreconstructable"]
    assert values.to_dict() == {
        "native_full": 5666,
        "reconstructable_native": 5661,
        "phase_pool_sensitive": 3659,
        "persistent": 2002,
        "common_pool_conflicts": 4897,
        "hidden_common_pool": 2895,
        "unreconstructable": 5,
    }


def test_dd_model_boundary_and_flip_normalisation():
    claims = build_claims()
    model = claims["model_evidence"]
    assert model["primary_real_models"] == ["ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP"]
    assert model["global_metric_top_model_inversion_rows"] == 0
    assert model["legacy_lower_rank_order_change_rows_all_denominators_metrics"] == 216
    rates = rank_flip_normalisation().set_index("scope")
    assert rates.loc["aggregate_diagnostic", "winner_flip_n"] == 10_468
    assert rates.loc["aggregate_diagnostic", "possible_pairwise_label_view_comparisons_n"] == 77_616
    assert rates.loc["real_models_only", "winner_flip_n"] == 377
    assert rates.loc["real_models_only", "possible_pairwise_label_view_comparisons_n"] == 7_056


def test_dd_claim_ledger_roundtrip(tmp_path):
    claims = write_claims_outputs(tmp_path)
    loaded = json.loads((tmp_path / "manuscript_claims.json").read_text())
    assert loaded == claims
    assert "Status: **PASS**" in (tmp_path / "manuscript_claims_audit.md").read_text()
