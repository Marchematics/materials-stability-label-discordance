#!/usr/bin/env python3
"""Regenerate threshold and structure-matching sensitivity tables from row data.

The threshold analysis evaluates source-native endpoint switches and the four
real-model rankings at 0, 25, 50 and 100 meV atom-1.  It uses the fixed M1
score support for model metrics and writes each threshold-specific label count
before calculating AUROC, AUPRC and discovery yield.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "outputs" / "phase1_v2"
REPAIRED = ROOT / "outputs" / "repaired_model_evaluation_v1"
MODELS = ("ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP")
THRESHOLDS = (0.0, 0.025, 0.050, 0.100)
K_GRID = (100, 300, 500, 1000, 5000, 10000)
ZERO_NUMERICAL_TOLERANCE = 1e-8


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=ROOT / "outputs" / "evidence_strengthening_v1" / "endpoint_sensitivity")
    p.add_argument("--matching-sweep", type=Path, default=Path("/home/waas/paper_experiments/github/materials-stability-label-discordance/outputs/milestones/benchmark_reliability_enhancement/table_structure_matching_tolerance_sweep.csv"))
    return p.parse_args()


def _energy_frame() -> pd.DataFrame:
    labels = pd.read_parquet(PHASE1 / "labels_by_view.parquet")
    base = labels.loc[labels["label_view"].eq("mp_native"), [
        "row_id", "chemical_system", "formula", "source_native_mp_ehull",
        "source_native_mattergen_ehull", "source_native_alexandria_ehull",
        "common_pool_mp_ehull", "common_pool_alexandria_ehull",
    ]].drop_duplicates("row_id")
    return base


def _labels_at_threshold(frame: pd.DataFrame, threshold: float) -> pd.DataFrame:
    x = frame.copy()
    # Phase 1 common-pool labels use a 1e-8 eV atom-1 numerical tolerance at
    # the 0 meV endpoint.  Keeping that tolerance reproduces the frozen
    # baseline while leaving the requested nonzero thresholds unchanged.
    effective_threshold = max(float(threshold), ZERO_NUMERICAL_TOLERANCE)
    mappings = {
        "mp_native": "source_native_mp_ehull",
        "alexmp20_native": "source_native_mattergen_ehull",
        "alex_pbe_native": "source_native_alexandria_ehull",
        "mp_common_pool": "common_pool_mp_ehull",
        "alex_pbe_common_pool": "common_pool_alexandria_ehull",
    }
    for name, energy in mappings.items():
        x[name] = pd.to_numeric(x[energy], errors="coerce").le(effective_threshold).where(pd.to_numeric(x[energy], errors="coerce").notna()).astype("boolean")
    agree = x["mp_common_pool"].notna() & x["alex_pbe_common_pool"].notna() & x["mp_common_pool"].eq(x["alex_pbe_common_pool"])
    x["common_pool_agreement"] = x["mp_common_pool"].where(agree, pd.NA).astype("boolean")
    return x


def endpoint_switches(frame: pd.DataFrame, threshold: float) -> pd.DataFrame:
    x = _labels_at_threshold(frame, threshold)
    pairs = [
        ("mp_native", "alexmp20_native"),
        ("mp_native", "alex_pbe_native"),
        ("alexmp20_native", "alex_pbe_native"),
        ("mp_common_pool", "alex_pbe_common_pool"),
    ]
    rows = []
    for a, b in pairs:
        valid = x[a].notna() & x[b].notna()
        switched = x.loc[valid, a].ne(x.loc[valid, b])
        rows.append({
            "threshold_eV_per_atom": threshold,
            "threshold_meV_per_atom": int(round(threshold * 1000)),
            "endpoint_a": a, "endpoint_b": b,
            "n": int(valid.sum()), "switch_n": int(switched.sum()),
            "switch_rate": float(switched.mean()),
            "endpoint_a_stable_rate": float(x.loc[valid, a].mean()),
            "endpoint_b_stable_rate": float(x.loc[valid, b].mean()),
        })
    rows.append({
        "threshold_eV_per_atom": threshold,
        "threshold_meV_per_atom": int(round(threshold * 1000)),
        "endpoint_a": "common_pool_agreement", "endpoint_b": "evaluable_support",
        "n": int(x["common_pool_agreement"].notna().sum()),
        "switch_n": int(x["common_pool_agreement"].isna().sum()),
        "switch_rate": float(x["common_pool_agreement"].isna().mean()),
        "endpoint_a_stable_rate": float(x["common_pool_agreement"].mean()),
        "endpoint_b_stable_rate": np.nan,
    })
    return pd.DataFrame(rows)


def model_metrics(frame: pd.DataFrame, threshold: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    fixed = pd.read_parquet(REPAIRED / "fixed_support" / "denominator_all_view_common_support.parquet")
    labels = _labels_at_threshold(frame, threshold).set_index("row_id")
    fixed = fixed.drop(columns=[c for c in ("mp_native", "alexmp20_native", "alex_pbe_native", "common_pool") if c in fixed.columns])
    fixed = fixed.set_index("row_id").join(labels[["mp_native", "alexmp20_native", "alex_pbe_native", "common_pool_agreement"]], how="inner")
    rows, topk_rows = [], []
    views = ("mp_native", "alexmp20_native", "alex_pbe_native", "common_pool_agreement")
    for model in MODELS:
        ranked = fixed.sort_values(model, ascending=False, kind="mergesort")
        score = ranked[model].to_numpy(float)
        for view in views:
            y = ranked[view].astype("boolean")
            evaluable = y.notna().to_numpy()
            yy = y.loc[y.notna()].astype(int).to_numpy()
            ss = ranked.loc[y.notna(), model].to_numpy(float)
            auroc = float(roc_auc_score(yy, ss)) if len(np.unique(yy)) == 2 else np.nan
            auprc = float(average_precision_score(yy, ss)) if len(np.unique(yy)) == 2 else np.nan
            rows.append({
                "threshold_eV_per_atom": threshold, "threshold_meV_per_atom": int(round(threshold * 1000)),
                "model_name": model, "label_view": view, "n": int(evaluable.sum()),
                "stable_n": int(yy.sum()), "stable_rate": float(yy.mean()), "auroc": auroc, "auprc": auprc,
            })
            full_y = y.fillna(False).astype(bool).to_numpy()
            for k in K_GRID:
                kk = min(k, len(ranked))
                stable_n = int(full_y[:kk].sum())
                supported_n = int(evaluable[:kk].sum())
                topk_rows.append({
                    "threshold_eV_per_atom": threshold, "threshold_meV_per_atom": int(round(threshold * 1000)),
                    "model_name": model, "label_view": view, "K": k, "K_effective": kk,
                    "topk_stable_n": stable_n, "stable_yield_at_k": stable_n / kk,
                    "topk_evaluable_n": supported_n, "topk_evaluable_fraction": supported_n / kk,
                })
    return pd.DataFrame(rows), pd.DataFrame(topk_rows)


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    energies = _energy_frame()
    switch_tables, metric_tables, topk_tables = [], [], []
    for threshold in THRESHOLDS:
        switch_tables.append(endpoint_switches(energies, threshold))
        metrics, topk = model_metrics(energies, threshold)
        metric_tables.append(metrics)
        topk_tables.append(topk)
    pd.concat(switch_tables, ignore_index=True).to_csv(args.out / "endpoint_switch_threshold_sensitivity.csv", index=False)
    pd.concat(metric_tables, ignore_index=True).to_csv(args.out / "model_auc_threshold_sensitivity.csv", index=False)
    pd.concat(topk_tables, ignore_index=True).to_csv(args.out / "topk_yield_threshold_sensitivity.csv", index=False)
    if args.matching_sweep.exists():
        sweep = pd.read_csv(args.matching_sweep)
        sweep.to_csv(args.out / "structure_matching_tolerance_sensitivity.csv", index=False)
        matching_status = "loaded"
    else:
        pd.DataFrame(columns=["tolerance", "ltol", "stol", "angle_tol", "n_checked", "n_matched", "match_fraction", "n_discordant", "discordance_rate"]).to_csv(args.out / "structure_matching_tolerance_sensitivity.csv", index=False)
        matching_status = "input_not_found"
    metadata = {
        "thresholds_eV_per_atom": list(THRESHOLDS),
        "zero_meV_numerical_tolerance_eV_per_atom": ZERO_NUMERICAL_TOLERANCE,
        "model_support": "M1 all-view common support", "models": list(MODELS),
        "metrics": ["AUROC", "AUPRC", "stable_yield_at_K"],
        "matching_sweep_status": matching_status,
        "matching_sweep_input": str(args.matching_sweep),
    }
    (args.out / "endpoint_sensitivity_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"wrote endpoint sensitivity analysis to {args.out}")


if __name__ == "__main__":
    main()
