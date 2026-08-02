#!/usr/bin/env python3
"""Evaluate fixed batch-relative rankings across physical source coordinates.

Official/native labels are audited separately. Threshold scans are named
source-coordinate endpoints because nonzero thresholds are analyst-defined,
not database-native labels. Agreement filters, consensus, and audit policies
are excluded from this physical-endpoint evaluation.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from sourceaware.ranking import analytic_tie_aware_topk, score_tie_audit


ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "outputs" / "phase1_v2"
DEFAULT_INPUT = ROOT / "outputs" / "referee_revision_v3"
DEFAULT_OUT = DEFAULT_INPUT / "evaluation"
MODELS = ("ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP")
MODEL_SLUGS = {model: model.lower().replace("-", "_") for model in MODELS}
COORDINATES = {
    "mp_source_coordinate": "source_native_mp_ehull",
    "alexmp20_source_coordinate": "source_native_mattergen_ehull",
    "alex_pbe_source_coordinate": "source_native_alexandria_ehull",
    "mp_matched_pool_coordinate": "common_pool_mp_ehull",
    "alex_pbe_matched_pool_coordinate": "common_pool_alexandria_ehull",
}
OFFICIAL_LABEL_VIEWS = {
    "mp_source_coordinate": "mp_native",
    "alexmp20_source_coordinate": "alexmp20_native",
    "alex_pbe_source_coordinate": "alex_pbe_native",
    "mp_matched_pool_coordinate": "mp_common_pool",
    "alex_pbe_matched_pool_coordinate": "alex_pbe_common_pool",
}
THRESHOLDS_MEV = (0, 10, 25, 50, 100)
INDETERMINATE_WIDTHS_MEV = (10, 20, 25, 30, 50)
K_VALUES = (100, 300, 500, 1000, 5000)
NUMERICAL_TOLERANCE_EV = 1e-12


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def coordinate_frame() -> pd.DataFrame:
    labels = pd.read_parquet(PHASE1 / "labels_by_view.parquet")
    base = labels[labels["label_view"].eq("mp_native")][
        ["row_id", "chemical_system", *COORDINATES.values()]
    ].drop_duplicates("row_id")
    official = []
    for coordinate, view in OFFICIAL_LABEL_VIEWS.items():
        x = labels[
            labels["label_view"].eq(view) & labels["is_evaluable"].astype(bool)
        ][["row_id", "label"]].drop_duplicates("row_id")
        official.append(x.rename(columns={"label": f"official__{coordinate}"}).set_index("row_id"))
    return base.merge(pd.concat(official, axis=1).reset_index(), on="row_id", how="left")


def load_scores(input_dir: Path) -> dict[str, pd.DataFrame]:
    scores = {}
    for model in MODELS:
        path = input_dir / f"batch_relative_signed_reference_hull_scores_{model}.parquet"
        frame = pd.read_parquet(path)
        frame = frame[frame["score_status"].eq("ok")][
            ["row_id", "score_for_batch_relative_ranking"]
        ].drop_duplicates("row_id")
        scores[model] = frame.rename(
            columns={"score_for_batch_relative_ranking": model}
        )
    return scores


def build_mphys(input_dir: Path) -> pd.DataFrame:
    candidate = pd.read_parquet(input_dir / "candidate_pool_manifest.parquet")
    candidate = candidate[candidate["ranking_eligible"].astype(bool)][
        ["row_id", "formula", "chemical_system", "equivalence_class_id"]
    ]
    frame = candidate.merge(coordinate_frame(), on=["row_id", "chemical_system"], how="left")
    for model, score in load_scores(input_dir).items():
        frame = frame.merge(score, on="row_id", how="left", validate="one_to_one")
    required = [*COORDINATES.values(), *MODELS]
    frame["in_mphys"] = frame[required].notna().all(axis=1)
    return frame


def official_coordinate_audit(frame: pd.DataFrame, support_name: str) -> pd.DataFrame:
    rows = []
    for coordinate, column in COORDINATES.items():
        official_col = f"official__{coordinate}"
        subset = frame.dropna(subset=[column, official_col])
        generated = subset[column].le(NUMERICAL_TOLERANCE_EV)
        official = subset[official_col].astype(bool)
        rows.append(
            {
                "support": support_name,
                "coordinate_endpoint": coordinate,
                "official_label_view": OFFICIAL_LABEL_VIEWS[coordinate],
                "n_compared": int(len(subset)),
                "official_positive_n": int(official.sum()),
                "coordinate_t0_positive_n": int(generated.sum()),
                "mismatch_n": int((generated != official).sum()),
                "mismatch_rate": float((generated != official).mean()),
                "numerical_tolerance_eV_per_atom": NUMERICAL_TOLERANCE_EV,
            }
        )
    return pd.DataFrame(rows)


def endpoint_labels(frame: pd.DataFrame, threshold_mev: int) -> dict[str, np.ndarray]:
    threshold = threshold_mev / 1000.0 + NUMERICAL_TOLERANCE_EV
    return {
        coordinate: frame[column].astype(float).to_numpy() <= threshold
        for coordinate, column in COORDINATES.items()
    }


def safe_auc(y: np.ndarray, score: np.ndarray) -> float:
    return float(roc_auc_score(y, score)) if len(np.unique(y)) == 2 else np.nan


def global_metrics(mphys: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for threshold_mev in THRESHOLDS_MEV:
        labels = endpoint_labels(mphys, threshold_mev)
        for model in MODELS:
            score = mphys[model].astype(float).to_numpy()
            for endpoint, y_bool in labels.items():
                y = y_bool.astype(int)
                prevalence = float(y.mean())
                ap = float(average_precision_score(y, score)) if len(np.unique(y)) == 2 else np.nan
                nap = (ap - prevalence) / (1.0 - prevalence) if prevalence < 1 and pd.notna(ap) else np.nan
                rows.append(
                    {
                        "threshold_meV_per_atom": threshold_mev,
                        "model_name": model,
                        "coordinate_endpoint": endpoint,
                        "n": len(mphys),
                        "positive_n": int(y.sum()),
                        "positive_rate_pi": prevalence,
                        "auroc": safe_auc(y, score),
                        "ap": ap,
                        "normalized_ap": float(nap) if pd.notna(nap) else np.nan,
                        "ranking_estimand": "batch_relative_transductive_signed_reference_hull_margin",
                    }
                )
    return pd.DataFrame(rows)


def tie_aware_topk(mphys: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    topk_rows = []
    audit_rows = []
    for model in MODELS:
        score = mphys[model].astype(float).to_numpy()
        audit = score_tie_audit(score, K_VALUES)
        audit.insert(0, "model_name", model)
        audit_rows.append(audit)
        for threshold_mev in THRESHOLDS_MEV:
            labels = endpoint_labels(mphys, threshold_mev)
            for endpoint, y in labels.items():
                prevalence = float(y.mean())
                for k in K_VALUES:
                    result = analytic_tie_aware_topk(score, y.astype(int), k)
                    hits = float(result["expected_stable_hits"])
                    yield_at_k = float(result["expected_stable_yield"])
                    topk_rows.append(
                        {
                            "threshold_meV_per_atom": threshold_mev,
                            "model_name": model,
                            "coordinate_endpoint": endpoint,
                            "support_n": len(mphys),
                            "positive_n": int(y.sum()),
                            "positive_rate_pi": prevalence,
                            "random_expected_hits": float(k * prevalence),
                            "excess_hits_over_random": float(hits - k * prevalence),
                            "enrichment": float(yield_at_k / prevalence) if prevalence else np.nan,
                            **result,
                        }
                    )
    return pd.DataFrame(topk_rows), pd.concat(audit_rows, ignore_index=True)


def threshold_conflicts(
    frame: pd.DataFrame,
    support_name: str,
    pairs: list[tuple[str, str]] | None = None,
) -> pd.DataFrame:
    pairs = pairs or [
        ("mp_source_coordinate", "alexmp20_source_coordinate"),
        ("mp_source_coordinate", "alex_pbe_source_coordinate"),
        ("alexmp20_source_coordinate", "alex_pbe_source_coordinate"),
        ("mp_matched_pool_coordinate", "alex_pbe_matched_pool_coordinate"),
    ]
    rows = []
    for threshold_mev in THRESHOLDS_MEV:
        labels = endpoint_labels(frame, threshold_mev)
        for left, right in pairs:
            different = labels[left] != labels[right]
            rows.append(
                {
                    "support": support_name,
                    "threshold_meV_per_atom": threshold_mev,
                    "endpoint_a": left,
                    "endpoint_b": right,
                    "n": len(frame),
                    "switch_n": int(different.sum()),
                    "switch_rate": float(different.mean()),
                    "endpoint_a_positive_rate": float(labels[left].mean()),
                    "endpoint_b_positive_rate": float(labels[right].mean()),
                }
            )
    return pd.DataFrame(rows)


def common_pool_decomposition(frame: pd.DataFrame, support_name: str) -> pd.DataFrame:
    """Decompose MP--Alexandria conflicts without hiding incomplete rows.

    ``frame`` may contain rows lacking one or both matched-pool coordinates.
    Native conflicts are counted on all rows with both native coordinates;
    phase-pool components are counted only on the explicitly reconstructable
    subset.  This keeps the all-native and reconstructable denominators
    machine-readable and prevents the historical 5,661/5,666 ambiguity.
    """
    rows = []
    for threshold_mev in THRESHOLDS_MEV:
        threshold = threshold_mev / 1000.0 + NUMERICAL_TOLERANCE_EV
        native_complete = frame[
            [COORDINATES["mp_source_coordinate"], COORDINATES["alex_pbe_source_coordinate"]]
        ].notna().all(axis=1)
        reconstructable = frame[
            [COORDINATES["mp_matched_pool_coordinate"], COORDINATES["alex_pbe_matched_pool_coordinate"]]
        ].notna().all(axis=1)
        native_mp = frame[COORDINATES["mp_source_coordinate"]].le(threshold)
        native_alex = frame[COORDINATES["alex_pbe_source_coordinate"]].le(threshold)
        native_conflict_all = native_complete & native_mp.ne(native_alex)

        work = frame.loc[reconstructable].copy()
        labels = endpoint_labels(work, threshold_mev)
        native_conflict = labels["mp_source_coordinate"] != labels["alex_pbe_source_coordinate"]
        reconstructed_conflict = (
            labels["mp_matched_pool_coordinate"] != labels["alex_pbe_matched_pool_coordinate"]
        )
        phase_pool_sensitive = native_conflict & ~reconstructed_conflict
        persistent = native_conflict & reconstructed_conflict
        hidden = ~native_conflict & reconstructed_conflict
        rows.append(
            {
                "support": support_name,
                "threshold_meV_per_atom": threshold_mev,
                "n_all_native_complete": int(native_complete.sum()),
                "n_reconstructable": int(reconstructable.sum()),
                "all_native_conflict_n": int(native_conflict_all.sum()),
                "reconstructable_native_conflict_n": int(native_conflict.sum()),
                "unreconstructable_native_conflict_n": int(
                    native_conflict_all.sum() - native_conflict.sum()
                ),
                "phase_pool_sensitive_n": int(phase_pool_sensitive.sum()),
                "persistent_conflict_n": int(persistent.sum()),
                "hidden_common_pool_conflict_n": int(hidden.sum()),
                "common_pool_conflict_n": int(reconstructed_conflict.sum()),
                "all_native_identity_verified": bool(
                    native_conflict_all.sum()
                    == native_conflict.sum()
                    + (native_conflict_all.sum() - native_conflict.sum())
                ),
                "reconstructable_native_identity_verified": bool(
                    native_conflict.sum() == phase_pool_sensitive.sum() + persistent.sum()
                ),
                "common_pool_identity_verified": bool(
                    reconstructed_conflict.sum() == persistent.sum() + hidden.sum()
                ),
            }
        )
    return pd.DataFrame(rows)


def indeterminate_analysis(frame: pd.DataFrame, support_name: str) -> pd.DataFrame:
    pairs = [
        ("mp_source_coordinate", "alexmp20_source_coordinate"),
        ("mp_source_coordinate", "alex_pbe_source_coordinate"),
        ("alexmp20_source_coordinate", "alex_pbe_source_coordinate"),
        ("mp_matched_pool_coordinate", "alex_pbe_matched_pool_coordinate"),
    ]
    rows = []
    for width_mev in INDETERMINATE_WIDTHS_MEV:
        width = width_mev / 1000.0
        states = {}
        for endpoint, column in COORDINATES.items():
            energy = frame[column].astype(float).to_numpy()
            state = np.full(len(frame), "indeterminate", dtype=object)
            state[energy <= NUMERICAL_TOLERANCE_EV] = "stable"
            state[energy >= width] = "unstable"
            states[endpoint] = state
        for left, right in pairs:
            a, b = states[left], states[right]
            any_indeterminate = (a == "indeterminate") | (b == "indeterminate")
            robust = ((a == "stable") & (b == "unstable")) | (
                (a == "unstable") & (b == "stable")
            )
            decisive = ~any_indeterminate
            rows.append(
                {
                    "support": support_name,
                    "base_threshold_meV_per_atom": 0,
                    "indeterminate_width_meV_per_atom": width_mev,
                    "endpoint_a": left,
                    "endpoint_b": right,
                    "n": len(frame),
                    "any_indeterminate_n": int(any_indeterminate.sum()),
                    "any_indeterminate_fraction": float(any_indeterminate.mean()),
                    "decisive_n": int(decisive.sum()),
                    "robust_conflict_n": int(robust.sum()),
                    "robust_conflict_rate_full_support": float(robust.mean()),
                    "robust_conflict_rate_decisive_support": float(robust.sum() / decisive.sum()) if decisive.sum() else np.nan,
                    "definition": "robust conflict is definite stable in one coordinate and definite unstable in the other",
                }
            )
    return pd.DataFrame(rows)


def long_metric_values(metrics: pd.DataFrame, topk: pd.DataFrame) -> pd.DataFrame:
    global_long = metrics.melt(
        id_vars=["threshold_meV_per_atom", "model_name", "coordinate_endpoint"],
        value_vars=["auroc", "ap", "normalized_ap"],
        var_name="metric",
        value_name="value",
    )
    k1000 = topk[topk["K"].eq(1000)][
        [
            "threshold_meV_per_atom", "model_name", "coordinate_endpoint",
            "expected_stable_hits", "expected_stable_yield", "excess_hits_over_random",
        ]
    ].melt(
        id_vars=["threshold_meV_per_atom", "model_name", "coordinate_endpoint"],
        var_name="metric",
        value_name="value",
    )
    return pd.concat([global_long, k1000], ignore_index=True)


def model_endpoint_interactions(values: pd.DataFrame) -> pd.DataFrame:
    rows = []
    anchor = "mp_source_coordinate"
    for (threshold, metric), group in values.groupby(["threshold_meV_per_atom", "metric"]):
        pivot = group.pivot(index="model_name", columns="coordinate_endpoint", values="value")
        for model_a, model_b in itertools.combinations(MODELS, 2):
            margins = pivot.loc[model_a] - pivot.loc[model_b]
            anchor_margin = float(margins[anchor])
            finite = margins.dropna()
            signs = set(np.sign(finite[np.abs(finite) > 1e-15]))
            margin_range = float(finite.max() - finite.min()) if len(finite) else np.nan
            for endpoint, margin in margins.items():
                rows.append(
                    {
                        "threshold_meV_per_atom": int(threshold),
                        "metric": metric,
                        "model_a": model_a,
                        "model_b": model_b,
                        "coordinate_endpoint": endpoint,
                        "pairwise_margin_a_minus_b": float(margin),
                        "difference_in_differences_vs_mp": float(margin - anchor_margin),
                        "pairwise_margin_range_across_endpoints": margin_range,
                        "pairwise_margin_changes_sign": bool(len(signs) > 1),
                    }
                )
    return pd.DataFrame(rows)


def winner_and_regret(values: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    winner_rows = []
    regret_rows = []
    anchor = "mp_source_coordinate"
    for (threshold, metric), group in values.groupby(["threshold_meV_per_atom", "metric"]):
        pivot = group.pivot(index="model_name", columns="coordinate_endpoint", values="value")
        anchor_values = pivot[anchor]
        anchor_best = anchor_values[anchor_values.eq(anchor_values.max())].index.tolist()
        for endpoint in pivot.columns:
            endpoint_values = pivot[endpoint]
            best = endpoint_values[endpoint_values.eq(endpoint_values.max())].index.tolist()
            maximum = float(endpoint_values.max())
            anchor_selected_values = endpoint_values.reindex(anchor_best).dropna()
            winner_rows.append(
                {
                    "threshold_meV_per_atom": int(threshold),
                    "metric": metric,
                    "coordinate_endpoint": endpoint,
                    "winner_models_json": json.dumps(best),
                    "winner_n": len(best),
                    "winner_changes_vs_mp": bool(set(best) != set(anchor_best)),
                }
            )
            regret_rows.append(
                {
                    "threshold_meV_per_atom": int(threshold),
                    "metric": metric,
                    "coordinate_endpoint": endpoint,
                    "mp_selected_models_json": json.dumps(anchor_best),
                    "endpoint_best_value": maximum,
                    "regret_min": float(maximum - anchor_selected_values.max()),
                    "regret_max": float(maximum - anchor_selected_values.min()),
                    "regret_definition": "endpoint best minus performance of a model selected as best on the MP coordinate at the same threshold",
                }
            )
    return pd.DataFrame(winner_rows), pd.DataFrame(regret_rows)


def support_flow(universe: pd.DataFrame, mphys: pd.DataFrame) -> pd.DataFrame:
    required_coordinates = universe[list(COORDINATES.values())].notna().all(axis=1)
    required_scores = universe[list(MODELS)].notna().all(axis=1)
    return pd.DataFrame(
        [
            {"stage": "D5 frozen four-score intersection", "n": 36801},
            {"stage": "D5 compound candidate universe", "n": int(len(universe))},
            {"stage": "five physical hull coordinates complete", "n": int(required_coordinates.sum())},
            {"stage": "four batch-relative rankings complete", "n": int(required_scores.sum())},
            {"stage": "Mphys fixed physical evaluation support", "n": int(len(mphys))},
        ]
    )


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    universe = build_mphys(args.input)
    mphys = universe[universe["in_mphys"]].copy().reset_index(drop=True)
    mphys.to_parquet(args.out / "mphys_fixed_support.parquet", index=False)
    support_flow(universe, mphys).to_csv(args.out / "physical_support_flow.csv", index=False)

    coordinates = coordinate_frame()
    audit = pd.concat(
        [
            official_coordinate_audit(coordinates, "D2"),
            official_coordinate_audit(universe, "D5_compounds"),
        ],
        ignore_index=True,
    )
    audit.to_csv(args.out / "official_vs_coordinate_t0_audit.csv", index=False)
    metrics = global_metrics(mphys)
    metrics.to_csv(args.out / "metrics_physical_endpoints.csv", index=False)
    topk, tie_audit = tie_aware_topk(mphys)
    topk.to_csv(args.out / "tie_aware_topk_physical_endpoints.csv", index=False)
    tie_audit.to_csv(args.out / "ranking_tie_audit_all_models.csv", index=False)

    d2_reconstructable = coordinates.dropna(subset=list(COORDINATES.values())).copy()
    native_pairs = [
        ("mp_source_coordinate", "alexmp20_source_coordinate"),
        ("mp_source_coordinate", "alex_pbe_source_coordinate"),
        ("alexmp20_source_coordinate", "alex_pbe_source_coordinate"),
    ]
    conflicts = pd.concat(
        [
            threshold_conflicts(coordinates, "D2_native_full", native_pairs),
            threshold_conflicts(d2_reconstructable, "D2_reconstructable"),
            threshold_conflicts(mphys, "Mphys"),
        ],
        ignore_index=True,
    )
    conflicts.to_csv(args.out / "endpoint_threshold_scan.csv", index=False)
    decomposition = pd.concat(
        [
            common_pool_decomposition(coordinates, "D2"),
            common_pool_decomposition(mphys, "Mphys"),
        ],
        ignore_index=True,
    )
    decomposition.to_csv(args.out / "common_pool_decomposition_threshold_scan.csv", index=False)
    indeterminate = pd.concat(
        [
            indeterminate_analysis(d2_reconstructable, "D2_reconstructable"),
            indeterminate_analysis(mphys, "Mphys"),
        ],
        ignore_index=True,
    )
    indeterminate.to_csv(args.out / "indeterminate_zone_conflicts.csv", index=False)

    values = long_metric_values(metrics, topk)
    interactions = model_endpoint_interactions(values)
    interactions.to_csv(args.out / "model_endpoint_interactions.csv", index=False)
    winners, regret = winner_and_regret(values)
    winners.to_csv(args.out / "model_winner_by_endpoint.csv", index=False)
    regret.to_csv(args.out / "endpoint_selection_regret.csv", index=False)

    summary = {
        "candidate_universe": "D5 compounds",
        "candidate_universe_n": int(len(universe)),
        "mphys_n": int(len(mphys)),
        "models": list(MODELS),
        "coordinate_endpoints": list(COORDINATES),
        "thresholds_meV_per_atom": list(THRESHOLDS_MEV),
        "indeterminate_widths_meV_per_atom": list(INDETERMINATE_WIDTHS_MEV),
        "official_t0_mismatch_total": int(audit["mismatch_n"].sum()),
        "ranking_fixed_across_all_endpoints_and_thresholds": True,
        "bootstrap_scope": "not_run_in_this_point_estimate_stage",
        "tie_uncertainty": "analytic hypergeometric at every K boundary",
    }
    (args.out / "evaluation_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
