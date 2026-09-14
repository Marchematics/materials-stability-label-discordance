#!/usr/bin/env python3
"""Sensitivity of SourceAware estimates to the bootstrap unit.

The primary analysis resamples chemical systems. This script repeats the
endpoint, ranking-metric and top-K audits with reduced-formula and structural
equivalence-family resampling. It keeps model scores and endpoint coordinates
fixed, matching the conditional interpretation of the primary bootstrap.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


MODELS = ["ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP"]
ENDPOINTS = {
    "mp_source_coordinate": "source_native_mp_ehull",
    "alexmp20_source_coordinate": "source_native_mattergen_ehull",
    "alex_pbe_source_coordinate": "source_native_alexandria_ehull",
    "mp_matched_pool_coordinate": "common_pool_mp_ehull",
    "alex_pbe_matched_pool_coordinate": "common_pool_alexandria_ehull",
}
THRESHOLDS = (0, 10, 25, 50)
K_VALUES = (100, 300, 500, 1000)
CLUSTERS = ("chemical_system", "reduced_formula", "equivalence_class_id")


def percentile_ci(values: list[float]) -> tuple[float, float, float]:
    x = np.asarray(values, dtype=float)
    return tuple(np.nanpercentile(x, [2.5, 50, 97.5]).tolist())


def bootstrap_weights(codes: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    n_clusters = int(codes.max()) + 1
    sampled = rng.integers(0, n_clusters, size=n_clusters)
    counts = np.bincount(sampled, minlength=n_clusters)
    return counts[codes].astype(float)


def weighted_average_precision(y: np.ndarray, score_order: np.ndarray, weights: np.ndarray) -> float:
    ordered_y = y[score_order].astype(float)
    ordered_w = weights[score_order]
    positive_weight = float(np.sum(ordered_y * ordered_w))
    if positive_weight == 0 or positive_weight == float(np.sum(ordered_w)):
        return float("nan")
    cumulative_positive = np.cumsum(ordered_y * ordered_w)
    cumulative_weight = np.cumsum(ordered_w)
    precision = np.divide(
        cumulative_positive,
        cumulative_weight,
        out=np.zeros_like(cumulative_positive),
        where=cumulative_weight > 0,
    )
    return float(np.sum(precision * ordered_y * ordered_w) / positive_weight)


def weighted_auc(y: np.ndarray, score_order: np.ndarray, weights: np.ndarray) -> float:
    ordered_y = y[score_order].astype(float)
    ordered_w = weights[score_order]
    positive_weight = float(np.sum(ordered_y * ordered_w))
    negative_weight = float(np.sum((1 - ordered_y) * ordered_w))
    if positive_weight == 0 or negative_weight == 0:
        return float("nan")
    cumulative_negative = np.cumsum((1 - ordered_y) * ordered_w)
    negative_after = negative_weight - cumulative_negative
    concordant = np.sum(ordered_y * ordered_w * negative_after)
    return float(concordant / (positive_weight * negative_weight))


def top_k_hits(y: np.ndarray, score_order: np.ndarray, weights: np.ndarray, k: int) -> float:
    ordered_y = y[score_order].astype(float)
    ordered_w = weights[score_order]
    before = np.concatenate(([0.0], np.cumsum(ordered_w[:-1])))
    selected = np.clip(k - before, 0, ordered_w)
    return float(np.sum(selected * ordered_y))


def metric_triplet(y: np.ndarray, score_order: np.ndarray, weights: np.ndarray) -> tuple[float, float, float]:
    auc = weighted_auc(y, score_order, weights)
    ap = weighted_average_precision(y, score_order, weights)
    prevalence = float(np.average(y, weights=weights))
    nap = (ap - prevalence) / (1 - prevalence) if prevalence < 1 else float("nan")
    return auc, ap, nap


def binary_labels(ehull: np.ndarray, threshold_meV_per_atom: int) -> np.ndarray:
    cutoff = 1e-8 if threshold_meV_per_atom == 0 else threshold_meV_per_atom / 1000.0
    return (ehull <= cutoff).astype(np.int8)


def load_inputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    root = root.resolve()
    analysis = (root / "outputs/referee_revision_v3" if (root / "outputs").exists()
                else root / "06_source_data/analysis_outputs")
    labels = pd.read_parquet(analysis / "row_level_hull_distance_labels.parquet")
    support = pd.read_parquet(analysis / "evaluation/mphys_fixed_support.parquet")
    manifest = pd.read_parquet(analysis / "candidate_pool_manifest.parquet")
    structural_manifest = pd.read_parquet(
        analysis / "structural_equivalence_classes.parquet",
        columns=["row_id", "reduced_formula", "equivalence_class_id"],
    )
    join_cols = ["row_id", "reduced_formula", "equivalence_class_id"]
    support = support.merge(manifest[join_cols], on=["row_id", "equivalence_class_id"], how="left")
    if support["reduced_formula"].isna().any():
        raise ValueError("Reduced-formula join is incomplete for M_phys")
    labels = labels.merge(structural_manifest[join_cols], on="row_id", how="left")
    labels["reduced_formula"] = labels["reduced_formula"].fillna(labels["formula"])
    labels["equivalence_class_id"] = labels["equivalence_class_id"].fillna(
        "fallback_structure_hash::" + labels["structure_hash"].astype(str)
    )
    return support, labels


def add_cluster_codes(df: pd.DataFrame, cluster: str) -> np.ndarray:
    values = df[cluster].astype(str)
    return pd.factorize(values, sort=True)[0]


def summarise(group: pd.DataFrame, value: str, keys: list[str] | None = None) -> pd.DataFrame:
    rows = []
    keys = keys or [key for key in group.columns if key not in {value, "replicate"}]
    for key, subset in group.groupby(keys, dropna=False):
        if not isinstance(key, tuple):
            key = (key,)
        low, median, high = percentile_ci(subset[value].tolist())
        rows.append(
            dict(zip(keys, key))
            | {
                f"{value}_ci_low_95": low,
                f"{value}_median": median,
                f"{value}_ci_high_95": high,
                "bootstrap_replicates": len(subset),
            }
        )
    return pd.DataFrame(rows)


def summarise_frequency(group: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    return (
        group.groupby(keys, dropna=False)["winner_share"]
        .agg(winner_frequency="mean", winner_equivalent_replicates="sum", bootstrap_replicates="count")
        .reset_index()
    )


def calculate_topk_regret(topk: pd.DataFrame) -> pd.DataFrame:
    rows = []
    base_keys = ["cluster", "replicate", "threshold_meV_per_atom", "K"]
    for key, subset in topk.groupby(base_keys, dropna=False):
        endpoint_model_hits = {
            endpoint: group.set_index("model")["stable_hits"].to_dict()
            for endpoint, group in subset.groupby("endpoint", dropna=False)
        }
        mp_hits = endpoint_model_hits["mp_source_coordinate"]
        mp_best = max(mp_hits.values())
        mp_winners = [model for model, value in mp_hits.items() if value == mp_best]
        for endpoint, hits in endpoint_model_hits.items():
            endpoint_best = max(hits.values())
            selected_hits = [hits[model] for model in mp_winners]
            rows.append(
                dict(zip(base_keys, key))
                | {
                    "endpoint": endpoint,
                    "mp_selected_models": "|".join(sorted(mp_winners)),
                    "regret_min_hits": endpoint_best - max(selected_hits),
                    "regret_max_hits": endpoint_best - min(selected_hits),
                }
            )
    return pd.DataFrame(rows)


def write_summaries(
    switch: pd.DataFrame,
    metric: pd.DataFrame,
    winner: pd.DataFrame,
    topk: pd.DataFrame,
    output: Path,
) -> None:
    topk_keys = ["cluster", "threshold_meV_per_atom", "endpoint", "K", "model"]
    regret = calculate_topk_regret(topk)
    regret.to_csv(output / "topk_regret_replicates.csv", index=False)
    summarise(switch, "switch_rate").to_csv(output / "switch_rate_ci.csv", index=False)
    summarise(metric, "value").to_csv(output / "metric_ci.csv", index=False)
    summarise_frequency(
        winner,
        ["cluster", "threshold_meV_per_atom", "endpoint", "metric", "model"],
    ).to_csv(output / "metric_winner_frequency.csv", index=False)
    summarise(topk, "stable_hits", topk_keys).to_csv(output / "topk_stable_hits_ci.csv", index=False)
    summarise_frequency(topk, topk_keys).to_csv(output / "topk_winner_frequency.csv", index=False)
    summarise(topk, "first_second_margin_hits", topk_keys).to_csv(output / "topk_margin_ci.csv", index=False)
    regret_keys = ["cluster", "threshold_meV_per_atom", "K", "endpoint"]
    summarise(regret, "regret_min_hits", regret_keys).to_csv(output / "topk_regret_min_ci.csv", index=False)
    summarise(regret, "regret_max_hits", regret_keys).to_csv(output / "topk_regret_max_ci.csv", index=False)


def run(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.summarize_existing:
        switch = pd.read_csv(output / "switch_rate_replicates.csv")
        metric = pd.read_csv(output / "metric_replicates.csv")
        winner = pd.read_csv(output / "metric_winner_replicates.csv")
        topk = pd.read_csv(output / "topk_winner_replicates.csv")
        write_summaries(switch, metric, winner, topk, output)
        return

    support, labels = load_inputs(root)
    rng = np.random.default_rng(args.seed)
    switch_rows: list[dict] = []
    metric_rows: list[dict] = []
    winner_rows: list[dict] = []
    topk_rows: list[dict] = []
    support_orders = {
        model: np.argsort(-support[model].to_numpy(float), kind="mergesort") for model in MODELS
    }
    label_ehulls = {name: labels[column].to_numpy(float) for name, column in ENDPOINTS.items()}
    support_ehulls = {name: support[column].to_numpy(float) for name, column in ENDPOINTS.items()}

    for cluster in CLUSTERS:
        support_codes = add_cluster_codes(support, cluster)
        label_codes = add_cluster_codes(labels, cluster)
        for replicate in range(args.replicates):
            support_weights = bootstrap_weights(support_codes, rng)
            label_weights = bootstrap_weights(label_codes, rng)
            for threshold in THRESHOLDS:
                binary = {
                    name: binary_labels(values, threshold)
                    for name, values in label_ehulls.items()
                }
                for endpoint_a, endpoint_b in (
                    ("mp_source_coordinate", "alexmp20_source_coordinate"),
                    ("mp_source_coordinate", "alex_pbe_source_coordinate"),
                    ("alexmp20_source_coordinate", "alex_pbe_source_coordinate"),
                ):
                    switch_rows.append(
                        {
                            "cluster": cluster,
                            "replicate": replicate,
                            "threshold_meV_per_atom": threshold,
                            "endpoint_a": endpoint_a,
                            "endpoint_b": endpoint_b,
                            "switch_rate": np.average(
                                binary[endpoint_a] != binary[endpoint_b], weights=label_weights
                            ),
                        }
                    )
                for endpoint, ehull in support_ehulls.items():
                    y = binary_labels(ehull, threshold)
                    endpoint_metrics: dict[str, float] = {}
                    endpoint_hits: dict[str, dict[int, float]] = {}
                    for model in MODELS:
                        order = support_orders[model]
                        auc, ap, nap = metric_triplet(y, order, support_weights)
                        for metric_name, value in (("auroc", auc), ("ap", ap), ("normalized_ap", nap)):
                            metric_rows.append(
                                {
                                    "cluster": cluster,
                                    "replicate": replicate,
                                    "threshold_meV_per_atom": threshold,
                                    "endpoint": endpoint,
                                    "model": model,
                                    "metric": metric_name,
                                    "value": value,
                                }
                            )
                            endpoint_metrics[f"{model}::{metric_name}"] = value
                        endpoint_hits[model] = {
                            k: top_k_hits(y, order, support_weights, k) for k in K_VALUES
                        }
                    for metric_name in ("auroc", "ap", "normalized_ap"):
                        values = {model: endpoint_metrics[f"{model}::{metric_name}"] for model in MODELS}
                        best = max(values.values())
                        winners = [model for model, value in values.items() if np.isclose(value, best)]
                        for model in MODELS:
                            winner_rows.append(
                                {
                                    "cluster": cluster,
                                    "replicate": replicate,
                                    "threshold_meV_per_atom": threshold,
                                    "endpoint": endpoint,
                                    "metric": metric_name,
                                    "model": model,
                                    "winner_share": 1.0 / len(winners) if model in winners else 0.0,
                                }
                            )
                    for k in K_VALUES:
                        values = {model: endpoint_hits[model][k] for model in MODELS}
                        ordered_hits = sorted(values.values(), reverse=True)
                        best = ordered_hits[0]
                        winners = [model for model, value in values.items() if value == best]
                        second = ordered_hits[len(winners)] if len(ordered_hits) > len(winners) else best
                        for model in MODELS:
                            topk_rows.append(
                                {
                                    "cluster": cluster,
                                    "replicate": replicate,
                                    "threshold_meV_per_atom": threshold,
                                    "endpoint": endpoint,
                                    "K": k,
                                    "model": model,
                                    "stable_hits": values[model],
                                    "winner_share": 1.0 / len(winners) if model in winners else 0.0,
                                    "first_second_margin_hits": best - second,
                                }
                            )

    switch = pd.DataFrame(switch_rows)
    metric = pd.DataFrame(metric_rows)
    winner = pd.DataFrame(winner_rows)
    topk = pd.DataFrame(topk_rows)
    switch.to_csv(output / "switch_rate_replicates.csv", index=False)
    metric.to_csv(output / "metric_replicates.csv", index=False)
    winner.to_csv(output / "metric_winner_replicates.csv", index=False)
    topk.to_csv(output / "topk_winner_replicates.csv", index=False)

    write_summaries(switch, metric, winner, topk, output)

    metadata = {
        "experiment": "A1_alternative_clustering_bootstrap",
        "seed": args.seed,
        "replicates": args.replicates,
        "cluster_units": list(CLUSTERS),
        "thresholds_meV_per_atom": list(THRESHOLDS),
        "K_values": list(K_VALUES),
        "models": MODELS,
        "endpoints": list(ENDPOINTS),
        "conditional_on": [
            "fixed model scores",
            "fixed endpoint coordinates",
            "fixed candidate cohort",
            "fixed structural-equivalence classes",
        ],
        "structural_prototype_available": False,
        "element_family_supercluster_available": False,
        "notes": "equivalence_class_id is the available structural-equivalence family; no prototype labels are archived",
        "support_n": int(len(support)),
        "d2_n": int(len(labels)),
        "cluster_counts": {
            cluster: int(pd.concat([support[cluster], labels[cluster]]).astype(str).nunique())
            for cluster in CLUSTERS
        },
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "outputs")
    parser.add_argument("--replicates", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260826)
    parser.add_argument("--summarize-existing", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
