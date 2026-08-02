#!/usr/bin/env python3
"""Paired chemical-system bootstrap conditional on fixed rankings/reference pool.

Tie uncertainty and cohort uncertainty remain distinct. Every bootstrap
replicate uses the analytic expectation at a tied top-K boundary. The
replicate distribution then measures chemical-system cohort uncertainty only;
it does not represent model-energy, DFT-workflow, or reference-pool uncertainty.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "outputs" / "referee_revision_v3" / "evaluation" / "mphys_fixed_support.parquet"
DEFAULT_OUT = ROOT / "outputs" / "referee_revision_v3" / "bootstrap"
MODELS = ("ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP")
COORDINATES = {
    "mp_source_coordinate": "source_native_mp_ehull",
    "alexmp20_source_coordinate": "source_native_mattergen_ehull",
    "alex_pbe_source_coordinate": "source_native_alexandria_ehull",
    "mp_matched_pool_coordinate": "common_pool_mp_ehull",
    "alex_pbe_matched_pool_coordinate": "common_pool_alexandria_ehull",
}
THRESHOLDS_MEV = (0, 10, 25, 50)
K_VALUES = (100, 300, 500, 1000, 5000)
TOPK_METRICS = tuple(f"expected_stable_hits_at_{k}" for k in K_VALUES)
METRICS = ("auroc", "ap", "normalized_ap", *TOPK_METRICS)
ANCHOR = "mp_source_coordinate"
TIE_DECIMALS = 12
NUMERICAL_TOLERANCE_EV = 1e-12


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--replicates", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260719)
    return parser.parse_args()


def labels_by_threshold(frame: pd.DataFrame) -> dict[tuple[int, str], np.ndarray]:
    out = {}
    for threshold_mev in THRESHOLDS_MEV:
        threshold = threshold_mev / 1000.0 + NUMERICAL_TOLERANCE_EV
        for endpoint, column in COORDINATES.items():
            out[(threshold_mev, endpoint)] = (
                frame[column].astype(float).to_numpy() <= threshold
            ).astype(np.int8)
    return out


def expected_hits_at_k(sorted_key: np.ndarray, sorted_y: np.ndarray, k: int) -> float:
    boundary = sorted_key[k - 1]
    before = sorted_key > boundary
    block = sorted_key == boundary
    a = int(before.sum())
    r = k - a
    h = int(sorted_y[before].sum())
    b = int(block.sum())
    s = int(sorted_y[block].sum())
    return float(h + r * s / b)


def metric_values(
    key: np.ndarray,
    order: np.ndarray,
    ascending_ranks: np.ndarray,
    y: np.ndarray,
) -> dict[str, float]:
    n = len(y)
    n_pos = int(y.sum())
    n_neg = n - n_pos
    prevalence = float(n_pos / n)
    if not n_pos or not n_neg:
        return {metric: np.nan for metric in METRICS}

    sorted_key = key[order]
    sorted_y = y[order]
    group_end = np.r_[np.flatnonzero(sorted_key[1:] != sorted_key[:-1]), n - 1]
    cumulative_pos = np.cumsum(sorted_y)[group_end]
    cumulative_n = group_end + 1
    group_pos = np.diff(np.r_[0, cumulative_pos])
    ap = float(np.sum((cumulative_pos / cumulative_n) * group_pos) / n_pos)
    auc = float(
        (ascending_ranks[y.astype(bool)].sum() - n_pos * (n_pos + 1) / 2)
        / (n_pos * n_neg)
    )
    nap = float((ap - prevalence) / (1.0 - prevalence))
    result = {
        "auroc": auc,
        "ap": ap,
        "normalized_ap": nap,
    }
    for k in K_VALUES:
        result[f"expected_stable_hits_at_{k}"] = expected_hits_at_k(
            sorted_key, sorted_y, min(k, n)
        )
    return result


def bootstrap_values(frame: pd.DataFrame, replicates: int, seed: int) -> pd.DataFrame:
    chemistry = frame["chemical_system"].astype(str).to_numpy()
    codes, systems = pd.factorize(chemistry, sort=True)
    group_indices = [np.flatnonzero(codes == index) for index in range(len(systems))]
    labels = labels_by_threshold(frame)
    scores = {model: frame[model].astype(float).to_numpy() for model in MODELS}
    rng = np.random.default_rng(seed)
    rows = []
    for replicate in range(replicates):
        sampled = rng.integers(0, len(systems), size=len(systems))
        index = np.concatenate([group_indices[value] for value in sampled])
        for model in MODELS:
            key = np.round(scores[model][index], decimals=TIE_DECIMALS)
            order = np.argsort(-key, kind="mergesort")
            ascending_ranks = rankdata(key, method="average")
            for threshold_mev in THRESHOLDS_MEV:
                for endpoint in COORDINATES:
                    y = labels[(threshold_mev, endpoint)][index]
                    values = metric_values(key, order, ascending_ranks, y)
                    prevalence = float(y.mean())
                    for metric, value in values.items():
                        rows.append(
                            {
                                "replicate": replicate,
                                "threshold_meV_per_atom": threshold_mev,
                                "coordinate_endpoint": endpoint,
                                "model_name": model,
                                "metric": metric,
                                "value": value,
                                "positive_rate_pi": prevalence,
                                "resampled_row_n": len(index),
                            }
                        )
        if (replicate + 1) % 100 == 0 or replicate + 1 == replicates:
            print(f"bootstrap {replicate + 1}/{replicates}", flush=True)
    return pd.DataFrame(rows)


def summarise_values(values: pd.DataFrame) -> pd.DataFrame:
    summary = (
        values.groupby(
            ["threshold_meV_per_atom", "coordinate_endpoint", "model_name", "metric"]
        )["value"]
        .quantile([0.025, 0.5, 0.975])
        .unstack()
        .reset_index()
    )
    summary.columns = [
        "threshold_meV_per_atom", "coordinate_endpoint", "model_name", "metric",
        "bootstrap_ci_low_95", "bootstrap_median", "bootstrap_ci_high_95",
    ]
    return summary


def winners(values: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    grouping = ["replicate", "threshold_meV_per_atom", "coordinate_endpoint", "metric"]
    maximum = values.groupby(grouping)["value"].transform("max")
    marked = values[values["value"].eq(maximum)].copy()
    replicate_n = values["replicate"].nunique()
    summary = (
        marked.groupby(["threshold_meV_per_atom", "coordinate_endpoint", "metric", "model_name"])["replicate"]
        .nunique()
        .rename("winner_replicate_n")
        .reset_index()
    )
    complete = pd.MultiIndex.from_product(
        [THRESHOLDS_MEV, list(COORDINATES), METRICS, MODELS],
        names=["threshold_meV_per_atom", "coordinate_endpoint", "metric", "model_name"],
    ).to_frame(index=False)
    summary = complete.merge(summary, how="left").fillna({"winner_replicate_n": 0})
    summary["winner_replicate_n"] = summary["winner_replicate_n"].astype(int)
    summary["winner_frequency"] = summary["winner_replicate_n"] / replicate_n
    summary["bootstrap_replicates"] = replicate_n
    return marked, summary


def interactions(values: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    range_rows = []
    for (replicate, threshold, metric), group in values.groupby(
        ["replicate", "threshold_meV_per_atom", "metric"], sort=False
    ):
        pivot = group.pivot(index="model_name", columns="coordinate_endpoint", values="value")
        for model_a, model_b in itertools.combinations(MODELS, 2):
            margins = pivot.loc[model_a] - pivot.loc[model_b]
            anchor_margin = float(margins[ANCHOR])
            nonzero_signs = set(np.sign(margins[np.abs(margins) > 1e-15]))
            margin_range = float(margins.max() - margins.min())
            range_rows.append(
                {
                    "replicate": int(replicate),
                    "threshold_meV_per_atom": int(threshold),
                    "metric": metric,
                    "model_a": model_a,
                    "model_b": model_b,
                    "pairwise_margin_range_across_endpoints": margin_range,
                    "pairwise_margin_changes_sign": bool(len(nonzero_signs) > 1),
                }
            )
            for endpoint, margin in margins.items():
                rows.append(
                    {
                        "replicate": int(replicate),
                        "threshold_meV_per_atom": int(threshold),
                        "metric": metric,
                        "model_a": model_a,
                        "model_b": model_b,
                        "coordinate_endpoint": endpoint,
                        "pairwise_margin_a_minus_b": float(margin),
                        "difference_in_differences_vs_mp": float(margin - anchor_margin),
                    }
                )
    return pd.DataFrame(rows), pd.DataFrame(range_rows)


def interaction_summary(interaction: pd.DataFrame, ranges: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    keys = ["threshold_meV_per_atom", "metric", "model_a", "model_b", "coordinate_endpoint"]
    summaries = []
    for column in ["pairwise_margin_a_minus_b", "difference_in_differences_vs_mp"]:
        x = interaction.groupby(keys)[column].quantile([0.025, 0.5, 0.975]).unstack().reset_index()
        x.columns = [*keys, f"{column}_ci_low_95", f"{column}_median", f"{column}_ci_high_95"]
        summaries.append(x)
    point = summaries[0].merge(summaries[1], on=keys)
    range_keys = ["threshold_meV_per_atom", "metric", "model_a", "model_b"]
    range_summary = ranges.groupby(range_keys).agg(
        margin_range_ci_low_95=("pairwise_margin_range_across_endpoints", lambda x: x.quantile(0.025)),
        margin_range_median=("pairwise_margin_range_across_endpoints", "median"),
        margin_range_ci_high_95=("pairwise_margin_range_across_endpoints", lambda x: x.quantile(0.975)),
        sign_change_frequency=("pairwise_margin_changes_sign", "mean"),
        bootstrap_replicates=("replicate", "nunique"),
    ).reset_index()
    return point, range_summary


def regrets(values: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (replicate, threshold, metric), group in values.groupby(
        ["replicate", "threshold_meV_per_atom", "metric"], sort=False
    ):
        pivot = group.pivot(index="model_name", columns="coordinate_endpoint", values="value")
        anchor_values = pivot[ANCHOR]
        selected = anchor_values[anchor_values.eq(anchor_values.max())].index.tolist()
        for endpoint in COORDINATES:
            endpoint_values = pivot[endpoint]
            best = float(endpoint_values.max())
            selected_values = endpoint_values.reindex(selected)
            rows.append(
                {
                    "replicate": int(replicate),
                    "threshold_meV_per_atom": int(threshold),
                    "metric": metric,
                    "coordinate_endpoint": endpoint,
                    "mp_selected_models_json": json.dumps(selected),
                    "regret_min": float(best - selected_values.max()),
                    "regret_max": float(best - selected_values.min()),
                }
            )
    return pd.DataFrame(rows)


def regret_summary(regret: pd.DataFrame) -> pd.DataFrame:
    keys = ["threshold_meV_per_atom", "metric", "coordinate_endpoint"]
    rows = []
    for key, group in regret.groupby(keys):
        row = dict(zip(keys, key))
        for column in ["regret_min", "regret_max"]:
            row[f"{column}_ci_low_95"] = float(group[column].quantile(0.025))
            row[f"{column}_median"] = float(group[column].median())
            row[f"{column}_ci_high_95"] = float(group[column].quantile(0.975))
        row["positive_regret_frequency"] = float((group["regret_max"] > 0).mean())
        row["bootstrap_replicates"] = int(group["replicate"].nunique())
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    frame = pd.read_parquet(args.input)
    values = bootstrap_values(frame, args.replicates, args.seed)
    values.to_parquet(args.out / "paired_metric_values_cluster_bootstrap_replicates.parquet", index=False)
    summarise_values(values).to_csv(args.out / "paired_metric_values_cluster_bootstrap.csv", index=False)
    marked_winners, winner_summary = winners(values)
    marked_winners.to_parquet(args.out / "winner_rows_cluster_bootstrap_replicates.parquet", index=False)
    winner_summary.to_csv(args.out / "model_winner_frequencies_cluster_bootstrap.csv", index=False)
    interaction, ranges = interactions(values)
    interaction.to_parquet(args.out / "model_endpoint_interactions_cluster_bootstrap_replicates.parquet", index=False)
    ranges.to_parquet(args.out / "model_margin_ranges_cluster_bootstrap_replicates.parquet", index=False)
    interaction_ci, range_summary = interaction_summary(interaction, ranges)
    interaction_ci.to_csv(args.out / "model_endpoint_interactions_cluster_bootstrap.csv", index=False)
    range_summary.to_csv(args.out / "model_margin_ranges_cluster_bootstrap.csv", index=False)
    regret = regrets(values)
    regret.to_parquet(args.out / "endpoint_selection_regret_cluster_bootstrap_replicates.parquet", index=False)
    regret_summary(regret).to_csv(args.out / "endpoint_selection_regret_cluster_bootstrap.csv", index=False)
    metadata = {
        "cluster": "chemical_system",
        "replicates": args.replicates,
        "seed": args.seed,
        "conditional_on": [
            "fixed model-predicted scores",
            "fixed D5 batch-relative reference phase pool",
            "fixed structural-equivalence classes",
        ],
        "not_quantified": [
            "model energy prediction uncertainty",
            "DFT workflow uncertainty",
            "reference phase pool uncertainty",
        ],
        "tie_policy_within_each_replicate": "analytic expectation at rounded-12-decimal score boundary",
    }
    (args.out / "bootstrap_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
