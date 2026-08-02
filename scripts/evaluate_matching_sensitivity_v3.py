#!/usr/bin/env python3
"""Evaluate denominator, conflict, and top-1000 sensitivity to matching tolerances."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from sourceaware.ranking import analytic_tie_aware_topk


ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "outputs" / "phase1_v2"
OUT = ROOT / "outputs" / "referee_revision_v3" / "matching_sensitivity"
MODELS = ("ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP")
TOLERANCES = ("tight", "default", "loose")
COORDINATES = {
    "mp_source_coordinate": "source_native_mp_ehull",
    "alexmp20_source_coordinate": "source_native_mattergen_ehull",
    "alex_pbe_source_coordinate": "source_native_alexandria_ehull",
    "mp_matched_pool_coordinate": "common_pool_mp_ehull",
    "alex_pbe_matched_pool_coordinate": "common_pool_alexandria_ehull",
}
NATIVE_PAIRS = (
    ("mp_source_coordinate", "alexmp20_source_coordinate"),
    ("mp_source_coordinate", "alex_pbe_source_coordinate"),
    ("alexmp20_source_coordinate", "alex_pbe_source_coordinate"),
)
ANCHOR = "mp_source_coordinate"
K = 1000
NUMERICAL_TOLERANCE_EV = 1e-12


def coordinate_frame() -> pd.DataFrame:
    labels = pd.read_parquet(PHASE1 / "labels_by_view.parquet")
    return labels[labels["label_view"].eq("mp_native")][
        ["row_id", "chemical_system", *COORDINATES.values()]
    ].drop_duplicates("row_id")


def scores(tolerance: str) -> pd.DataFrame:
    frame = None
    for model in MODELS:
        path = OUT / tolerance / f"batch_relative_signed_reference_hull_scores_{model}.parquet"
        score = pd.read_parquet(path)
        score = score[score["score_status"].eq("ok")][
            ["row_id", "score_for_batch_relative_ranking"]
        ].drop_duplicates("row_id").rename(columns={"score_for_batch_relative_ranking": model})
        frame = score if frame is None else frame.merge(score, on="row_id", how="inner")
    return frame


def topk_rows(frame: pd.DataFrame, tolerance: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for model in MODELS:
        score = frame[model].astype(float).to_numpy()
        for endpoint, column in COORDINATES.items():
            y = frame[column].astype(float).le(NUMERICAL_TOLERANCE_EV).astype(int).to_numpy()
            result = analytic_tie_aware_topk(score, y, K)
            rows.append(
                {
                    "matching_tolerance": tolerance,
                    "support_n": int(len(frame)),
                    "model_name": model,
                    "coordinate_endpoint": endpoint,
                    "positive_n": int(y.sum()),
                    "positive_rate": float(y.mean()),
                    **result,
                }
            )
    topk = pd.DataFrame(rows)
    decisions = []
    anchor_values = topk[topk["coordinate_endpoint"].eq(ANCHOR)].set_index(
        "model_name"
    )["expected_stable_hits"]
    anchor_winners = sorted(anchor_values[anchor_values.eq(anchor_values.max())].index)
    for endpoint, group in topk.groupby("coordinate_endpoint"):
        values = group.set_index("model_name")["expected_stable_hits"]
        maximum = float(values.max())
        winners = sorted(values[values.eq(maximum)].index)
        ordered = values.sort_values(ascending=False).to_numpy()
        selected_values = values.reindex(anchor_winners)
        decisions.append(
            {
                "matching_tolerance": tolerance,
                "K": K,
                "coordinate_endpoint": endpoint,
                "point_winner_models_json": json.dumps(winners),
                "point_winner_n": len(winners),
                "first_second_margin_hits": float(ordered[0] - ordered[1]),
                "mp_selected_models_json": json.dumps(anchor_winners),
                "mp_selection_regret_min_hits": maximum - float(selected_values.max()),
                "mp_selection_regret_max_hits": maximum - float(selected_values.min()),
                "maximum_boundary_tie_n_across_models": int(group["boundary_tie_n"].max()),
            }
        )
    return topk, pd.DataFrame(decisions)


def main() -> None:
    d1 = pd.read_parquet(OUT / "d1_pair_survival_by_tolerance.parquet")
    d2 = pd.read_parquet(OUT / "d2_pair_survival_by_tolerance.parquet")
    coordinates = coordinate_frame()
    summaries = []
    switch_rows = []
    topk_frames = []
    decision_frames = []
    retained_sets = {
        tolerance: set(d2.loc[d2[f"d2_retained_{tolerance}"], "row_id"])
        for tolerance in TOLERANCES
    }
    default_set = retained_sets["default"]
    d1_retained_sets = {
        tolerance: set(d1.loc[d1[f"matched_{tolerance}"], "row_id"])
        for tolerance in TOLERANCES
    }
    d1_default_set = d1_retained_sets["default"]

    for tolerance in TOLERANCES:
        d1_retained = d1[f"matched_{tolerance}"].astype(bool)
        d2_retained = d2[f"d2_retained_{tolerance}"].astype(bool)
        retained_ids = retained_sets[tolerance]
        ranking_scores = scores(tolerance)
        d2_frame = coordinates[coordinates["row_id"].isin(retained_ids)].copy()
        d2_frame = d2_frame.dropna(
            subset=[COORDINATES[endpoint] for pair in NATIVE_PAIRS for endpoint in pair]
        ).reset_index(drop=True)
        frame = d2_frame.merge(
            ranking_scores, on="row_id", how="inner", validate="one_to_one"
        )
        frame = frame.dropna(subset=[*COORDINATES.values(), *MODELS]).reset_index(drop=True)

        equivalence = json.loads(
            (OUT / tolerance / "structural_equivalence_metadata.json").read_text()
        )
        summary_row = {
                "matching_tolerance": tolerance,
                "d1_frozen_n": int(len(d1)),
                "d1_structure_available_n": int(d1["structures_available"].sum()),
                "d1_retained_n": int(d1_retained.sum()),
                "d1_lost_vs_default_n": int(
                    len(d1_default_set - d1_retained_sets[tolerance])
                ),
                "d1_gained_vs_default_n": int(
                    len(d1_retained_sets[tolerance] - d1_default_set)
                ),
                "d2_frozen_n": int(len(d2)),
                "d2_official_structure_available_n": int(
                    d2["official_structures_available"].sum()
                ),
                "d2_retained_n": int(d2_retained.sum()),
                "d2_lost_vs_default_n": int(len(default_set - retained_ids)),
                "d2_gained_vs_default_n": int(len(retained_ids - default_set)),
                "mphys_tolerance_specific_n": int(len(frame)),
                "equivalence_class_n": equivalence["equivalence_class_n"],
                "non_singleton_equivalence_class_n": equivalence["non_singleton_class_n"],
                "largest_equivalence_class_n": equivalence["largest_class_n"],
                "failed_equivalence_pair_comparisons": equivalence["failed_pair_comparisons"],
                "cross_source_estimand": "survival of frozen D1/D2 mappings; no search for new loose matches",
                "ranking_recomputed_with_tolerance_specific_equivalence_exclusions": True,
                "default_ranking_max_abs_difference_vs_primary": np.nan,
                "default_ranking_reproduction_verified": None,
            }
        if tolerance == "default":
            differences = []
            for model in MODELS:
                primary = pd.read_parquet(
                    OUT.parent / f"batch_relative_signed_reference_hull_scores_{model}.parquet"
                )[["row_id", "score_for_batch_relative_ranking"]]
                reproduced = pd.read_parquet(
                    OUT / tolerance / f"batch_relative_signed_reference_hull_scores_{model}.parquet"
                )[["row_id", "score_for_batch_relative_ranking"]]
                joined = primary.merge(reproduced, on="row_id", suffixes=("_primary", "_sensitivity"))
                differences.append(
                    float(
                        (
                            joined.score_for_batch_relative_ranking_primary
                            - joined.score_for_batch_relative_ranking_sensitivity
                        ).abs().max()
                    )
                )
            summary_row["default_ranking_max_abs_difference_vs_primary"] = max(differences)
            summary_row["default_ranking_reproduction_verified"] = bool(max(differences) <= 1e-12)
        summaries.append(summary_row)
        for support_name, support_frame in (
            ("D2_tolerance_specific", d2_frame),
            ("Mphys_tolerance_specific", frame),
        ):
            labels = {
                endpoint: support_frame[column].astype(float).le(NUMERICAL_TOLERANCE_EV).to_numpy()
                for endpoint, column in COORDINATES.items()
            }
            for left, right in NATIVE_PAIRS:
                switched = labels[left] != labels[right]
                switch_rows.append(
                    {
                        "matching_tolerance": tolerance,
                        "support": support_name,
                        "threshold_meV_per_atom": 0,
                        "endpoint_a": left,
                        "endpoint_b": right,
                        "n": int(len(support_frame)),
                        "switch_n": int(switched.sum()),
                        "switch_rate": float(switched.mean()),
                    }
                )
        topk, decisions = topk_rows(frame, tolerance)
        topk_frames.append(topk)
        decision_frames.append(decisions)

    chemistry_rows = []
    for tolerance in TOLERANCES:
        current = retained_sets[tolerance]
        for direction, row_ids in (
            ("lost_vs_default", default_set - current),
            ("gained_vs_default", current - default_set),
        ):
            subset = d2[d2["row_id"].isin(row_ids)]
            counts = subset.groupby("chemical_system").size().sort_values(ascending=False)
            for rank, (system, count) in enumerate(counts.items(), start=1):
                chemistry_rows.append(
                    {
                        "matching_tolerance": tolerance,
                        "direction": direction,
                        "chemical_system": system,
                        "row_n": int(count),
                        "rank_within_direction": rank,
                        "total_changed_rows": int(len(subset)),
                    }
                )

    pd.DataFrame(summaries).to_csv(OUT / "matching_sensitivity_summary.csv", index=False)
    pd.DataFrame(switch_rows).to_csv(OUT / "matching_sensitivity_switch_burden.csv", index=False)
    pd.concat(topk_frames, ignore_index=True).to_csv(
        OUT / "matching_sensitivity_top1000_by_model_endpoint.csv", index=False
    )
    pd.concat(decision_frames, ignore_index=True).to_csv(
        OUT / "matching_sensitivity_top1000_decisions.csv", index=False
    )
    pd.DataFrame(chemistry_rows).to_csv(
        OUT / "matching_sensitivity_changed_chemistry.csv", index=False
    )
    print(pd.DataFrame(summaries).to_string(index=False), flush=True)
    print(pd.concat(decision_frames, ignore_index=True).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
