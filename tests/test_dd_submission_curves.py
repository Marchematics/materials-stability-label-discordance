from __future__ import annotations

import numpy as np

from sourceaware.dd_submission import (
    DISCOVERY_LABEL_VIEWS,
    REAL_MODELS,
    exact_discovery_curves,
    exact_primary_metrics,
    rolling_conflict_table,
    uncertainty_dominance_tables,
)


def test_exact_discovery_curves_are_row_level_and_contiguous():
    curves = exact_discovery_curves()
    assert set(curves["curve_method"]) == {"row_level_exact_cumulative_no_interpolation"}
    assert set(curves["model_name"]) == set(REAL_MODELS)
    assert set(curves["label_view"]) == set(DISCOVERY_LABEL_VIEWS)
    for _, group in curves.groupby(["model_name", "label_view"]):
        ranks = group["rank"].to_numpy()
        assert np.array_equal(ranks, np.arange(1, len(group) + 1))
        stable = group["cumulative_stable_n"].to_numpy()
        assert np.all(np.diff(stable) >= 0)
        assert np.allclose(group["stable_yield"], stable / ranks)
        assert group["row_id"].is_unique


def test_primary_metrics_only_four_real_models():
    metrics, topk = exact_primary_metrics()
    assert set(metrics["model_name"]) == set(REAL_MODELS)
    assert set(topk["model_name"]) == set(REAL_MODELS)
    assert metrics["score_interpretation"].eq("diagnostic_ranking_not_calibrated_source_comparable_hull_distance").all()
    dominance, _, slope = uncertainty_dominance_tables(metrics, topk)
    assert len(dominance) == 4 * 5
    assert dominance["uncertainty_dominance_ratio"].notna().all()
    assert set(slope["model_name"]) == set(REAL_MODELS)


def test_rolling_conflict_windows_record_support_and_intervals():
    rolling, density, metadata = rolling_conflict_table()
    assert metadata["window_width_eV"] == 0.040
    assert metadata["x_max_eV"] == 0.20
    assert metadata["minimum_n"] == 1000
    assert metadata["bootstrap_seed"] is None
    assert metadata["bootstrap_iterations"] == 0
    assert rolling["n_rows"].notna().all()
    supported = rolling["supported"]
    assert rolling.loc[supported, ["endpoint_switch_rate", "ci_low", "ci_high"]].notna().all().all()
    assert rolling.loc[~supported, ["endpoint_switch_rate", "ci_low", "ci_high"]].isna().all().all()
    assert (rolling.loc[supported, "ci_low"] <= rolling.loc[supported, "endpoint_switch_rate"]).all()
    assert (rolling.loc[supported, "endpoint_switch_rate"] <= rolling.loc[supported, "ci_high"]).all()
    assert density["row_count"].sum() > 0
