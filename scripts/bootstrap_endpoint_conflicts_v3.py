#!/usr/bin/env python3
"""Chemical-system bootstrap for threshold and indeterminate-zone conflicts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "outputs" / "phase1_v2"
DEFAULT_OUT = ROOT / "outputs" / "referee_revision_v3" / "bootstrap_conflicts"
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
ALL_PAIRS = (*NATIVE_PAIRS, ("mp_matched_pool_coordinate", "alex_pbe_matched_pool_coordinate"))
THRESHOLDS_MEV = (0, 10, 25, 50)
WIDTHS_MEV = (10, 20, 25, 30, 50)
NUMERICAL_TOLERANCE_EV = 1e-12


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--replicates", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260719)
    return parser.parse_args()


def coordinates() -> pd.DataFrame:
    labels = pd.read_parquet(PHASE1 / "labels_by_view.parquet")
    return labels[labels["label_view"].eq("mp_native")][
        ["row_id", "chemical_system", *COORDINATES.values()]
    ].drop_duplicates("row_id")


def sampled_indices(frame: pd.DataFrame, replicates: int, seed: int):
    codes, systems = pd.factorize(frame["chemical_system"].astype(str), sort=True)
    groups = [np.flatnonzero(codes == index) for index in range(len(systems))]
    rng = np.random.default_rng(seed)
    for replicate in range(replicates):
        sampled = rng.integers(0, len(systems), size=len(systems))
        yield replicate, np.concatenate([groups[value] for value in sampled])


def bootstrap(frame: pd.DataFrame, support: str, pairs, replicates: int, seed: int):
    energy = {
        endpoint: frame[column].astype(float).to_numpy()
        for endpoint, column in COORDINATES.items()
    }
    threshold_rows = []
    indeterminate_rows = []
    decomposition_rows = []
    for replicate, index in sampled_indices(frame, replicates, seed):
        for threshold_mev in THRESHOLDS_MEV:
            threshold = threshold_mev / 1000.0 + NUMERICAL_TOLERANCE_EV
            labels = {endpoint: values[index] <= threshold for endpoint, values in energy.items()}
            for left, right in pairs:
                switch = labels[left] != labels[right]
                threshold_rows.append(
                    {
                        "replicate": replicate,
                        "support": support,
                        "threshold_meV_per_atom": threshold_mev,
                        "endpoint_a": left,
                        "endpoint_b": right,
                        "switch_rate": float(switch.mean()),
                    }
                )
            if support == "D2_reconstructable":
                native = labels["mp_source_coordinate"] != labels["alex_pbe_source_coordinate"]
                reconstructed = labels["mp_matched_pool_coordinate"] != labels["alex_pbe_matched_pool_coordinate"]
                phase_sensitive = native & ~reconstructed
                persistent = native & reconstructed
                hidden = ~native & reconstructed
                decomposition_rows.append(
                    {
                        "replicate": replicate,
                        "support": support,
                        "threshold_meV_per_atom": threshold_mev,
                        "reconstructable_native_conflict_rate": float(native.mean()),
                        "common_pool_conflict_rate": float(reconstructed.mean()),
                        "phase_pool_sensitive_share_of_native_conflicts": float(phase_sensitive.sum() / native.sum()) if native.sum() else np.nan,
                        "persistent_share_of_native_conflicts": float(persistent.sum() / native.sum()) if native.sum() else np.nan,
                        "hidden_conflict_rate": float(hidden.mean()),
                    }
                )
        for width_mev in WIDTHS_MEV:
            width = width_mev / 1000.0
            state = {}
            for endpoint, values in energy.items():
                selected = values[index]
                stable = selected <= NUMERICAL_TOLERANCE_EV
                unstable = selected >= width
                state[endpoint] = (stable, unstable)
            for left, right in pairs:
                stable_a, unstable_a = state[left]
                stable_b, unstable_b = state[right]
                robust = (stable_a & unstable_b) | (unstable_a & stable_b)
                indeterminate_a = ~(stable_a | unstable_a)
                indeterminate_b = ~(stable_b | unstable_b)
                any_indeterminate = indeterminate_a | indeterminate_b
                decisive = ~any_indeterminate
                indeterminate_rows.append(
                    {
                        "replicate": replicate,
                        "support": support,
                        "indeterminate_width_meV_per_atom": width_mev,
                        "endpoint_a": left,
                        "endpoint_b": right,
                        "any_indeterminate_fraction": float(any_indeterminate.mean()),
                        "robust_conflict_rate_full_support": float(robust.mean()),
                        "robust_conflict_rate_decisive_support": float(robust.sum() / decisive.sum()) if decisive.sum() else np.nan,
                    }
                )
        if (replicate + 1) % 100 == 0 or replicate + 1 == replicates:
            print(f"{support} bootstrap {replicate + 1}/{replicates}", flush=True)
    return pd.DataFrame(threshold_rows), pd.DataFrame(indeterminate_rows), pd.DataFrame(decomposition_rows)


def quantile_summary(frame: pd.DataFrame, keys: list[str], values: list[str]) -> pd.DataFrame:
    summaries = []
    for value in values:
        x = frame.groupby(keys)[value].quantile([0.025, 0.5, 0.975]).unstack().reset_index()
        x.columns = [*keys, f"{value}_ci_low_95", f"{value}_median", f"{value}_ci_high_95"]
        summaries.append(x)
    out = summaries[0]
    for summary in summaries[1:]:
        out = out.merge(summary, on=keys, how="outer")
    return out


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    full = coordinates()
    native = full.dropna(subset=[COORDINATES[key] for pair in NATIVE_PAIRS for key in pair]).copy()
    reconstructed = full.dropna(subset=list(COORDINATES.values())).copy()
    outputs = [
        bootstrap(native, "D2_native_full", NATIVE_PAIRS, args.replicates, args.seed),
        bootstrap(reconstructed, "D2_reconstructable", ALL_PAIRS, args.replicates, args.seed),
    ]
    threshold = pd.concat([value[0] for value in outputs], ignore_index=True)
    indeterminate = pd.concat([value[1] for value in outputs], ignore_index=True)
    decomposition = pd.concat([value[2] for value in outputs if len(value[2])], ignore_index=True)
    threshold.to_parquet(args.out / "endpoint_threshold_cluster_bootstrap_replicates.parquet", index=False)
    indeterminate.to_parquet(args.out / "indeterminate_cluster_bootstrap_replicates.parquet", index=False)
    decomposition.to_parquet(args.out / "common_pool_decomposition_cluster_bootstrap_replicates.parquet", index=False)
    quantile_summary(
        threshold,
        ["support", "threshold_meV_per_atom", "endpoint_a", "endpoint_b"],
        ["switch_rate"],
    ).to_csv(args.out / "endpoint_threshold_cluster_bootstrap.csv", index=False)
    quantile_summary(
        indeterminate,
        ["support", "indeterminate_width_meV_per_atom", "endpoint_a", "endpoint_b"],
        ["any_indeterminate_fraction", "robust_conflict_rate_full_support", "robust_conflict_rate_decisive_support"],
    ).to_csv(args.out / "indeterminate_cluster_bootstrap.csv", index=False)
    quantile_summary(
        decomposition,
        ["support", "threshold_meV_per_atom"],
        [
            "reconstructable_native_conflict_rate", "common_pool_conflict_rate",
            "phase_pool_sensitive_share_of_native_conflicts",
            "persistent_share_of_native_conflicts", "hidden_conflict_rate",
        ],
    ).to_csv(args.out / "common_pool_decomposition_cluster_bootstrap.csv", index=False)
    metadata = {
        "cluster": "chemical_system",
        "replicates": args.replicates,
        "seed": args.seed,
        "paired_source_coordinates_retained_together": True,
        "indeterminate_definition": "stable E<=0; indeterminate 0<E<w; unstable E>=w",
    }
    (args.out / "bootstrap_conflict_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
