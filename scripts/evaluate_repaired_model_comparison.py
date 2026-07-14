#!/usr/bin/env python3
"""Evaluate predicted-hull model ranks on fixed label support.

This analysis reports two distinct estimands:

* label-only variation: five evaluable stability views on one fixed row set;
* selection/coverage variation: the consensus view, whose definition removes
  discordant rows and is therefore reported as a cohort-selection policy.

Scores are D2-subsystem predicted-hull ranks written by
``build_predicted_hull_scores.py``.  Every label-only metric uses the same
rows, fixed model ranking and (for classification metrics) fixed MP-native
positive-count threshold.  Uncertainty intervals use paired chemical-system
cluster bootstrap resampling.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.metrics import average_precision_score, balanced_accuracy_score, f1_score, precision_score, recall_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "outputs" / "phase1_v2"
RAW_SCORES = ROOT / "inputs" / "phase2_v1" / "sourceaware_model_scores_public_safe.parquet"
DEFAULT_IN = ROOT / "outputs" / "repaired_model_evaluation_v1"
MODELS = ("ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP")
FIXED_VIEWS = ("mp_native", "alexmp20_native", "alex_pbe_native", "common_pool", "audit_view")
K_GRID = (100, 300, 500, 1000, 5000, 10000)
DISCOVERY_VIEWS = ("mp_native", "common_pool", "audit_view")
BOOT_METRICS = ("f1_fixed_threshold", "auroc", "auprc", "ap_lift", "stable_yield_at_1000")


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="input_dir", type=Path, default=DEFAULT_IN)
    p.add_argument("--out", type=Path, default=DEFAULT_IN)
    p.add_argument("--bootstrap", type=int, default=1000)
    p.add_argument("--seed", type=int, default=20260714)
    return p.parse_args()


def safe_auc(y: np.ndarray, score: np.ndarray) -> float:
    return float(roc_auc_score(y, score)) if len(np.unique(y)) == 2 else np.nan


def frame(input_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    labels = pd.read_parquet(PHASE1 / "labels_by_view.parquet")
    chemistry = labels[labels["label_view"].eq("mp_native")][["row_id", "chemical_system"]].drop_duplicates("row_id").set_index("row_id")
    label_frames = []
    for view in [*FIXED_VIEWS, "consensus"]:
        x = labels[(labels["label_view"].eq(view)) & labels["is_evaluable"].astype(bool)][["row_id", "label"]].drop_duplicates("row_id")
        label_frames.append(x.rename(columns={"label": view}).set_index("row_id"))
    joined = chemistry.join(pd.concat(label_frames, axis=1, join="outer"), how="left")
    # The first five views form the label-only, all-view common support.
    fixed = joined.dropna(subset=list(FIXED_VIEWS)).copy()
    score_frames = []
    for model in MODELS:
        p = input_dir / f"predicted_hull_scores_{model}.parquet"
        if not p.exists():
            raise FileNotFoundError(p)
        x = pd.read_parquet(p)[["row_id", "score_for_stability_ranking"]].rename(columns={"score_for_stability_ranking": model})
        score_frames.append(x.set_index("row_id"))
    fixed = fixed.join(pd.concat(score_frames, axis=1, join="inner"), how="inner").dropna(subset=list(MODELS))
    fixed.index.name = "row_id"
    consensus = fixed.dropna(subset=["consensus"]).copy()
    for col in FIXED_VIEWS:
        fixed[col] = fixed[col].astype(bool)
    consensus["consensus"] = consensus["consensus"].astype(bool)
    return fixed.reset_index(), consensus.reset_index()


def metric_row(model: str, view: str, df: pd.DataFrame, reference_positive_n: int) -> dict:
    y = df[view].astype(int).to_numpy()
    score = df[model].astype(float).to_numpy()
    order = np.argsort(-score, kind="mergesort")
    pred = np.zeros(len(df), dtype=bool)
    pred[order[:reference_positive_n]] = True
    ap = float(average_precision_score(y, score)) if len(np.unique(y)) == 2 else np.nan
    return {
        "model_name": model,
        "label_view": view,
        "n": int(len(df)),
        "positive_rate": float(y.mean()),
        "fixed_predicted_positive_n": int(reference_positive_n),
        "fixed_predicted_positive_rate": float(reference_positive_n / len(df)),
        "f1_fixed_threshold": float(f1_score(y, pred, zero_division=0)),
        "precision_fixed_threshold": float(precision_score(y, pred, zero_division=0)),
        "recall_fixed_threshold": float(recall_score(y, pred, zero_division=0)),
        "balanced_accuracy_fixed_threshold": float(balanced_accuracy_score(y, pred)),
        "auroc": safe_auc(y, score),
        "auprc": ap,
        "ap_lift": float(ap - y.mean()) if pd.notna(ap) else np.nan,
    }


def topk_rows(model: str, view: str, df: pd.DataFrame) -> list[dict]:
    ranked = df.sort_values(model, ascending=False, kind="mergesort")
    y = ranked[view].astype(bool).to_numpy()
    total = int(y.sum())
    rows = []
    for k in K_GRID:
        kk = min(k, len(ranked))
        stable = int(y[:kk].sum())
        rows.append({
            "model_name": model,
            "label_view": view,
            "K": k,
            "K_effective": kk,
            "n_ranked": int(len(ranked)),
            "stable_n": stable,
            "stable_yield_at_k": stable / kk,
            "recall_at_k": stable / total if total else np.nan,
            "positive_rate": float(y.mean()),
        })
    return rows


def evaluate_fixed(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ref_n = int(df["mp_native"].sum())
    metrics = [metric_row(model, view, df, ref_n) for model in MODELS for view in FIXED_VIEWS]
    topk = [r for model in MODELS for view in FIXED_VIEWS for r in topk_rows(model, view, df)]
    return pd.DataFrame(metrics), pd.DataFrame(topk)


def evaluate_selection(consensus: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ref_n = int(consensus["mp_native"].sum())
    metrics = [metric_row(model, "consensus", consensus, ref_n) for model in MODELS]
    topk = [r for model in MODELS for r in topk_rows(model, "consensus", consensus)]
    return pd.DataFrame(metrics), pd.DataFrame(topk)


def exact_discovery_curves(df: pd.DataFrame) -> pd.DataFrame:
    """Write exact cumulative curves, rather than interpolating a sparse K grid.

    The selected label-only views share the identical M1 support and the model
    ordering is fixed once per model.  This makes every vertical separation a
    label assignment difference, not a coverage or score-table difference.
    """
    rows = []
    for model in MODELS:
        ranked = df.sort_values(model, ascending=False, kind="mergesort")
        rank = np.arange(1, len(ranked) + 1)
        for view in DISCOVERY_VIEWS:
            y = ranked[view].astype(np.int8).to_numpy()
            stable_n = np.cumsum(y)
            total = int(y.sum())
            rows.append(pd.DataFrame({
                "model_name": model,
                "label_view": view,
                "rank": rank,
                "stable_n": stable_n,
                "stable_yield": stable_n / rank,
                "recall": stable_n / total if total else np.nan,
                "uncertain_fraction": np.nan,
                "n_common_support": len(ranked),
            }))
    return pd.concat(rows, ignore_index=True)


def raw_score_audit(fixed: pd.DataFrame) -> pd.DataFrame:
    raw = pd.read_parquet(RAW_SCORES)
    rows = []
    for model in MODELS:
        source = raw[raw["model"].eq(model)][["row_id", "score"]].drop_duplicates("row_id")
        x = fixed[["row_id", "mp_native", model]].merge(source, on="row_id", how="inner")
        y = x["mp_native"].astype(int).to_numpy()
        rows.append({
            "model_name": model,
            "n": len(x),
            "raw_energy_rank_auroc_mp_native": safe_auc(y, x["score"].to_numpy()),
            "reverse_raw_energy_rank_auroc_mp_native": safe_auc(y, -x["score"].to_numpy()),
            "predicted_hull_rank_auroc_mp_native": safe_auc(y, x[model].to_numpy()),
            "raw_score_use": "excluded_from_primary_evaluation_composition_not_normalized",
            "predicted_hull_score_use": "primary_fixed_support_ranking",
        })
    return pd.DataFrame(rows)


def coverage_table(fixed: pd.DataFrame, consensus: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for view in FIXED_VIEWS:
        rows.append({"evaluation_type": "label_only_fixed_support", "view": view, "n": len(fixed), "positive_rate": float(fixed[view].mean())})
    rows.append({"evaluation_type": "selection_policy", "view": "consensus", "n": len(consensus), "positive_rate": float(consensus["consensus"].mean())})
    rows.append({"evaluation_type": "selection_policy", "view": "consensus_excluded_from_label_only_band", "n": len(fixed) - len(consensus), "positive_rate": np.nan})
    return pd.DataFrame(rows)


def common_support_exclusion_audit(fixed: pd.DataFrame) -> pd.DataFrame:
    """Make each exclusion between D2, D5 and M1 explicit."""
    labels = pd.read_parquet(PHASE1 / "labels_by_view.parquet")
    label_sets = []
    for view in FIXED_VIEWS:
        label_sets.append(set(labels[(labels["label_view"].eq(view)) & labels["is_evaluable"].astype(bool)]["row_id"].drop_duplicates()))
    d2 = set(labels[labels["label_view"].eq("mp_native")]["row_id"].drop_duplicates())
    all_label_support = set.intersection(*label_sets)
    raw = pd.read_parquet(RAW_SCORES)
    raw_score_support = set.intersection(*[set(raw[raw["model"].eq(model)]["row_id"].drop_duplicates()) for model in MODELS])
    rows = [
        {"stage": "D2 three-source exact rows", "n": len(d2), "excluded_vs_d2": 0, "excluded_vs_d5": np.nan, "rule": "single strict MP--alex-mp-20--Alexandria-PBE structure match"},
        {"stage": "D5 archived four-score intersection", "n": len(raw_score_support), "excluded_vs_d2": len(d2 - raw_score_support), "excluded_vs_d5": 0, "rule": "all four archived raw score tables available"},
        {"stage": "Five-view label support", "n": len(all_label_support), "excluded_vs_d2": len(d2 - all_label_support), "excluded_vs_d5": len(raw_score_support - all_label_support), "rule": "MP-native, alex-mp-20-native, Alexandria-PBE-native, common-pool and audit labels evaluable"},
        {"stage": "M1 all-view common support", "n": len(fixed), "excluded_vs_d2": len(d2 - set(fixed.row_id)), "excluded_vs_d5": len(raw_score_support - set(fixed.row_id)), "rule": "intersection of D5 and five-view label support; corrected predicted-hull scores available"},
    ]
    return pd.DataFrame(rows)


def bands(metrics: pd.DataFrame, topk: pd.DataFrame) -> pd.DataFrame:
    values = metrics.melt(id_vars=["model_name", "label_view"], value_vars=["f1_fixed_threshold", "precision_fixed_threshold", "recall_fixed_threshold", "balanced_accuracy_fixed_threshold", "auroc", "auprc", "ap_lift"], var_name="metric", value_name="value")
    t = topk[topk["K"].eq(1000)].rename(columns={"stable_yield_at_k": "value"})[["model_name", "label_view", "value"]]
    t["metric"] = "stable_yield_at_1000"
    values = pd.concat([values, t], ignore_index=True)
    out = []
    for (model, metric), g in values.groupby(["model_name", "metric"]):
        out.append({"scope": "label_view_band", "model_name": model, "metric": metric, "minimum": g.value.min(), "maximum": g.value.max(), "spread": g.value.max() - g.value.min(), "n_views": len(g)})
    for (view, metric), g in values.groupby(["label_view", "metric"]):
        out.append({"scope": "between_model_spread", "label_view": view, "metric": metric, "minimum": g.value.min(), "maximum": g.value.max(), "spread": g.value.max() - g.value.min(), "n_models": len(g)})
    return pd.DataFrame(out)


def cluster_bootstrap(fixed: pd.DataFrame, n_boot: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Paired chemical-system bootstrap for bands, paired deltas and winners.

    Each resample draws chemical systems with replacement and retains every
    row and every label view within each selected cluster.  Per-view values
    are retained so pairwise label-view differences and model winner
    probabilities are calculated from the same paired replicates.
    """
    chemistry = fixed["chemical_system"].astype(str).to_numpy()
    codes, systems = pd.factorize(chemistry, sort=True)
    group_indices = [np.flatnonzero(codes == i) for i in range(len(systems))]
    rng = np.random.default_rng(seed)
    labels = {view: fixed[view].astype(np.int8).to_numpy() for view in FIXED_VIEWS}
    scores = {model: fixed[model].astype(float).to_numpy() for model in MODELS}
    band_rows = []
    metric_rows = []
    for rep in range(n_boot):
        sampled = rng.integers(0, len(systems), size=len(systems))
        idx = np.concatenate([group_indices[i] for i in sampled])
        reference_n = int(labels["mp_native"][idx].sum())
        for model in MODELS:
            score = scores[model][idx]
            order = np.argsort(-score, kind="mergesort")
            rank_ascending = rankdata(score, method="average")
            pred = np.zeros(len(idx), dtype=bool)
            pred[order[:reference_n]] = True
            values = {"f1_fixed_threshold": [], "auroc": [], "auprc": [], "ap_lift": [], "stable_yield_at_1000": []}
            for view in FIXED_VIEWS:
                y = labels[view][idx]
                n_pos = int(y.sum())
                n_neg = int(len(y) - n_pos)
                ordered_y = y[order]
                group_end = np.r_[np.flatnonzero(score[order][1:] != score[order][:-1]), len(score) - 1]
                cumulative_pos = np.cumsum(ordered_y)[group_end]
                cumulative_n = group_end + 1
                group_pos = np.diff(np.r_[0, cumulative_pos])
                ap = float(np.sum((cumulative_pos / cumulative_n) * group_pos) / n_pos) if n_pos else np.nan
                auc = float((rank_ascending[y.astype(bool)].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)) if n_pos and n_neg else np.nan
                true_positive = int(y[pred].sum())
                values["f1_fixed_threshold"].append(float(2 * true_positive / (n_pos + reference_n)) if n_pos + reference_n else np.nan)
                values["auroc"].append(auc)
                values["auprc"].append(ap)
                values["ap_lift"].append(ap - float(y.mean()))
                values["stable_yield_at_1000"].append(float(y[order[: min(1000, len(y))]].mean()))
            for metric, vals in values.items():
                band_rows.append({"scope": "label_view_band", "model_name": model, "metric": metric, "spread": float(np.nanmax(vals) - np.nanmin(vals)), "replicate": rep})
                for view, value in zip(FIXED_VIEWS, vals):
                    metric_rows.append({"replicate": rep, "model_name": model, "label_view": view, "metric": metric, "value": float(value)})
        if (rep + 1) % 100 == 0 or rep + 1 == n_boot:
            print(f"cluster bootstrap {rep + 1}/{n_boot}", flush=True)
    return pd.DataFrame(band_rows), pd.DataFrame(metric_rows)


def paired_differences_and_winners(
    metrics: pd.DataFrame,
    topk: pd.DataFrame,
    boot_metrics: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Summarise paired label deltas and bootstrap model-win probabilities."""
    point = metrics.melt(
        id_vars=["model_name", "label_view"], value_vars=list(BOOT_METRICS[:-1]),
        var_name="metric", value_name="value",
    )
    point_topk = topk[topk["K"].eq(1000)][["model_name", "label_view", "stable_yield_at_k"]].rename(columns={"stable_yield_at_k": "value"})
    point_topk["metric"] = "stable_yield_at_1000"
    point = pd.concat([point, point_topk], ignore_index=True)

    delta_rows = []
    for model in MODELS:
        for metric in BOOT_METRICS:
            point_group = point[(point["model_name"].eq(model)) & (point["metric"].eq(metric))].set_index("label_view")["value"]
            boot_group = boot_metrics[(boot_metrics["model_name"].eq(model)) & (boot_metrics["metric"].eq(metric))]
            for ia, view_a in enumerate(FIXED_VIEWS):
                for view_b in FIXED_VIEWS[ia + 1:]:
                    paired = boot_group.pivot(index="replicate", columns="label_view", values="value")
                    delta = paired[view_a] - paired[view_b]
                    delta_rows.append({
                        "model_name": model,
                        "metric": metric,
                        "view_a": view_a,
                        "view_b": view_b,
                        "point_delta_a_minus_b": float(point_group[view_a] - point_group[view_b]),
                        "bootstrap_ci_low_95": float(delta.quantile(0.025)),
                        "bootstrap_median": float(delta.quantile(0.5)),
                        "bootstrap_ci_high_95": float(delta.quantile(0.975)),
                        "probability_delta_gt_zero": float((delta > 0).mean()),
                        "probability_delta_lt_zero": float((delta < 0).mean()),
                        "bootstrap_replicates": int(delta.notna().sum()),
                        "cluster": "chemical_system",
                    })

    winner_rows = []
    for view in FIXED_VIEWS:
        for metric in BOOT_METRICS:
            point_values = point[(point["label_view"].eq(view)) & (point["metric"].eq(metric))].set_index("model_name")["value"]
            point_best = point_values[point_values.eq(point_values.max())].index.tolist()
            rep = boot_metrics[(boot_metrics["label_view"].eq(view)) & (boot_metrics["metric"].eq(metric))]
            winners = rep.loc[rep.groupby("replicate")["value"].transform("max").eq(rep["value"])]
            counts = winners.groupby("model_name")["replicate"].nunique()
            n_rep = int(rep["replicate"].nunique())
            for model in MODELS:
                winner_rows.append({
                    "label_view": view,
                    "metric": metric,
                    "model_name": model,
                    "point_estimate_winner": bool(model in point_best),
                    "winner_probability": float(counts.get(model, 0) / n_rep) if n_rep else np.nan,
                    "bootstrap_replicates": n_rep,
                    "cluster": "chemical_system",
                })
    return pd.DataFrame(delta_rows), pd.DataFrame(winner_rows)


def main() -> None:
    a = args()
    a.out.mkdir(parents=True, exist_ok=True)
    fixed, consensus = frame(a.input_dir)
    support = coverage_table(fixed, consensus)
    exclusion_audit = common_support_exclusion_audit(fixed)
    metrics, topk = evaluate_fixed(fixed)
    selection_metrics, selection_topk = evaluate_selection(consensus)
    score_audit = raw_score_audit(fixed)
    band = bands(metrics, topk)
    curves = exact_discovery_curves(fixed)
    boot, boot_metric_values = cluster_bootstrap(fixed, a.bootstrap, a.seed)
    ci = boot.groupby(["model_name", "metric"])["spread"].quantile([0.025, 0.5, 0.975]).unstack().reset_index()
    ci.columns = ["model_name", "metric", "ci_low_95", "median", "ci_high_95"]
    label_bands = band[band["scope"].eq("label_view_band")].merge(ci, on=["model_name", "metric"], how="left")
    paired_deltas, winner_probabilities = paired_differences_and_winners(metrics, topk, boot_metric_values)

    fixed.to_parquet(a.out / "denominator_all_view_common_support.parquet", index=False)
    support.to_csv(a.out / "evaluation_support_and_coverage.csv", index=False)
    exclusion_audit.to_csv(a.out / "all_view_common_support_exclusion_audit.csv", index=False)
    metrics.to_csv(a.out / "metrics_fixed_support.csv", index=False)
    topk.to_csv(a.out / "topk_fixed_support.csv", index=False)
    curves.to_parquet(a.out / "exact_discovery_curves_fixed_support.parquet", index=False)
    curves.to_csv(a.out / "exact_discovery_curves_fixed_support.csv", index=False)
    selection_metrics.to_csv(a.out / "metrics_consensus_selection_policy.csv", index=False)
    selection_topk.to_csv(a.out / "topk_consensus_selection_policy.csv", index=False)
    score_audit.to_csv(a.out / "score_construct_validity_audit.csv", index=False)
    band.to_csv(a.out / "band_and_model_spread_fixed_support.csv", index=False)
    label_bands.to_csv(a.out / "label_bands_cluster_bootstrap.csv", index=False)
    boot.to_parquet(a.out / "label_bands_cluster_bootstrap_replicates.parquet", index=False)
    boot_metric_values.to_parquet(a.out / "paired_metric_values_cluster_bootstrap_replicates.parquet", index=False)
    paired_deltas.to_csv(a.out / "paired_label_view_differences_cluster_bootstrap.csv", index=False)
    winner_probabilities.to_csv(a.out / "model_winner_probabilities_cluster_bootstrap.csv", index=False)
    status = {
        "fixed_support_n": int(len(fixed)),
        "consensus_selection_support_n": int(len(consensus)),
        "label_only_views": list(FIXED_VIEWS),
        "selection_policy_view": "consensus",
        "classification_threshold": "fixed number of predicted positives equal to MP-native positives on fixed support",
        "bootstrap": {"cluster": "chemical_system", "replicates": int(a.bootstrap), "seed": int(a.seed), "reported_quantities": ["label-view bands", "paired label-view differences", "model winner probabilities"]},
        "raw_energy_scores": "excluded from primary evaluation",
        "primary_scores": "negative predicted e_above_hull over fixed D2 subsystem phase pool",
    }
    (a.out / "repaired_evaluation_status.json").write_text(json.dumps(status, indent=2) + "\n")


if __name__ == "__main__":
    main()
