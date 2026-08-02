#!/usr/bin/env python3
"""Assemble K-dependent point winners, margins, winner frequencies, and regret."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "referee_revision_v3"
EVAL = OUT / "evaluation"
BOOT = OUT / "bootstrap"
K_VALUES = (100, 300, 500, 1000, 5000)
ANCHOR = "mp_source_coordinate"


def main() -> None:
    topk = pd.read_csv(EVAL / "tie_aware_topk_physical_endpoints.csv")
    winner_frequency = pd.read_csv(BOOT / "model_winner_frequencies_cluster_bootstrap.csv")
    regret = pd.read_csv(BOOT / "endpoint_selection_regret_cluster_bootstrap.csv")
    replicate_values = pd.read_parquet(
        BOOT / "paired_metric_values_cluster_bootstrap_replicates.parquet"
    )
    bootstrapped_thresholds = set(regret["threshold_meV_per_atom"].unique())
    topk = topk[topk["threshold_meV_per_atom"].isin(bootstrapped_thresholds)].copy()

    rows = []
    margin_replicates = []
    for (threshold, k, endpoint), group in topk.groupby(
        ["threshold_meV_per_atom", "K", "coordinate_endpoint"]
    ):
        values = group.set_index("model_name")["expected_stable_hits"]
        maximum = float(values.max())
        point_winners = sorted(values[values.eq(maximum)].index)
        ordered = values.sort_values(ascending=False).to_numpy()
        point_margin = float(ordered[0] - ordered[1])
        metric = f"expected_stable_hits_at_{int(k)}"
        frequency = winner_frequency[
            winner_frequency.threshold_meV_per_atom.eq(threshold)
            & winner_frequency.coordinate_endpoint.eq(endpoint)
            & winner_frequency.metric.eq(metric)
        ].set_index("model_name")["winner_frequency"]
        regret_row = regret[
            regret.threshold_meV_per_atom.eq(threshold)
            & regret.coordinate_endpoint.eq(endpoint)
            & regret.metric.eq(metric)
        ].iloc[0]
        anchor_group = topk[
            topk.threshold_meV_per_atom.eq(threshold)
            & topk.K.eq(k)
            & topk.coordinate_endpoint.eq(ANCHOR)
        ]
        anchor_values = anchor_group.set_index("model_name")["expected_stable_hits"]
        anchor_best = sorted(anchor_values[anchor_values.eq(anchor_values.max())].index)
        endpoint_selected = values.reindex(anchor_best)
        point_regret_min = maximum - float(endpoint_selected.max())
        point_regret_max = maximum - float(endpoint_selected.min())
        for record in group.itertuples():
            rows.append(
                {
                    "threshold_meV_per_atom": int(threshold),
                    "K": int(k),
                    "coordinate_endpoint": endpoint,
                    "model_name": record.model_name,
                    "point_stable_hits": float(record.expected_stable_hits),
                    "point_stable_yield": float(record.expected_stable_yield),
                    "point_winner": bool(record.model_name in point_winners),
                    "point_winner_models_json": json.dumps(point_winners),
                    "point_first_second_margin_hits": point_margin,
                    "bootstrap_winner_frequency": float(frequency.get(record.model_name, 0.0)),
                    "mp_selected_models_json": json.dumps(anchor_best),
                    "point_mp_selection_regret_min_hits": point_regret_min,
                    "point_mp_selection_regret_max_hits": point_regret_max,
                    "bootstrap_regret_min_median_hits": float(regret_row.regret_min_median),
                    "bootstrap_regret_min_ci_low_95_hits": float(regret_row.regret_min_ci_low_95),
                    "bootstrap_regret_min_ci_high_95_hits": float(regret_row.regret_min_ci_high_95),
                    "bootstrap_regret_max_median_hits": float(regret_row.regret_max_median),
                    "bootstrap_regret_max_ci_low_95_hits": float(regret_row.regret_max_ci_low_95),
                    "bootstrap_regret_max_ci_high_95_hits": float(regret_row.regret_max_ci_high_95),
                    "positive_regret_frequency": float(regret_row.positive_regret_frequency),
                    "boundary_tie_n": int(record.boundary_tie_n),
                    "strictly_before_boundary_n": int(record.strictly_before_boundary_n),
                    "tie_interval_low_hits": int(record.tie_interval_low_hits),
                    "tie_interval_high_hits": int(record.tie_interval_high_hits),
                }
            )

    for k in K_VALUES:
        metric = f"expected_stable_hits_at_{k}"
        subset = replicate_values[replicate_values.metric.eq(metric)]
        for key, group in subset.groupby(
            ["replicate", "threshold_meV_per_atom", "coordinate_endpoint"]
        ):
            ordered = group["value"].sort_values(ascending=False).to_numpy()
            margin_replicates.append(
                {
                    "replicate": int(key[0]),
                    "threshold_meV_per_atom": int(key[1]),
                    "coordinate_endpoint": key[2],
                    "K": k,
                    "first_second_margin_hits": float(ordered[0] - ordered[1]),
                }
            )
    margin_replicates = pd.DataFrame(margin_replicates)
    margin_summary = (
        margin_replicates.groupby(
            ["threshold_meV_per_atom", "coordinate_endpoint", "K"]
        )["first_second_margin_hits"]
        .quantile([0.025, 0.5, 0.975])
        .unstack()
        .reset_index()
    )
    margin_summary.columns = [
        "threshold_meV_per_atom", "coordinate_endpoint", "K",
        "first_second_margin_ci_low_95_hits", "first_second_margin_median_hits",
        "first_second_margin_ci_high_95_hits",
    ]
    audit = pd.DataFrame(rows).merge(
        margin_summary,
        on=["threshold_meV_per_atom", "coordinate_endpoint", "K"],
        how="left",
    )
    audit.to_csv(EVAL / "budget_sensitivity_audit.csv", index=False)
    margin_replicates.to_parquet(
        BOOT / "first_second_margin_cluster_bootstrap_replicates.parquet", index=False
    )
    margin_summary.to_csv(
        BOOT / "first_second_margin_cluster_bootstrap.csv", index=False
    )
    print(
        audit[
            audit.threshold_meV_per_atom.eq(0) & audit.point_winner.astype(bool)
        ][
            [
                "K", "coordinate_endpoint", "model_name",
                "point_first_second_margin_hits", "bootstrap_winner_frequency",
                "bootstrap_regret_max_median_hits",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
