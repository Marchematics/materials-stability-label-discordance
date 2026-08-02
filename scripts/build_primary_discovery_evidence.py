#!/usr/bin/env python3
"""Promote fixed-budget discovery outcomes and paired endpoint differences."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
M1 = ROOT / "outputs" / "repaired_model_evaluation_v1" / "fixed_support" / "denominator_all_view_common_support.parquet"
REPAIRED = ROOT / "outputs" / "repaired_model_evaluation_v1" / "fixed_support"
BOOT = ROOT / "outputs" / "evidence_strengthening_v1" / "cluster_bootstrap_sensitivity" / "paired_cluster_bootstrap_summary.csv"
MODELS = ("ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP")
VIEWS = ("mp_native", "alex_pbe_native", "common_pool", "audit_view")
K_GRID = (100, 300, 500, 1000, 5000, 10000)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=ROOT / "outputs" / "evidence_strengthening_v1" / "primary_discovery_evidence")
    return p.parse_args()


def main() -> None:
    args = parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    m1 = pd.read_parquet(M1)
    rows = []
    for model in MODELS:
        ranked = m1.sort_values(model, ascending=False, kind="mergesort")
        for k in K_GRID:
            selected = ranked.head(k)
            for i, a in enumerate(VIEWS):
                ids_a = set(selected.loc[selected[a].astype(bool), "row_id"])
                for b in VIEWS[i + 1:]:
                    ids_b = set(selected.loc[selected[b].astype(bool), "row_id"])
                    union = ids_a | ids_b
                    rows.append({"model_name": model, "K": k, "view_a": a, "view_b": b,
                                 "stable_yield_a": len(ids_a) / k, "stable_yield_b": len(ids_b) / k,
                                 "stable_yield_delta_a_minus_b": (len(ids_a) - len(ids_b)) / k,
                                 "stable_candidate_jaccard": len(ids_a & ids_b) / len(union) if union else 1.0,
                                 "endpoint_changed_candidate_n": len(ids_a ^ ids_b), "ranked_candidate_n": k})
    pd.DataFrame(rows).to_csv(args.out / "topk_endpoint_decision_deltas.csv", index=False)
    metrics = pd.read_csv(REPAIRED / "metrics_fixed_support.csv")
    metrics.loc[metrics.label_view.isin(VIEWS), ["model_name", "label_view", "auprc", "auroc", "ap_lift"]].to_csv(args.out / "primary_fixed_support_auc.csv", index=False)
    topk = pd.read_csv(REPAIRED / "topk_fixed_support.csv")
    topk.loc[topk.label_view.isin(VIEWS) & topk.K.isin(K_GRID)].to_csv(args.out / "primary_fixed_budget_outcomes.csv", index=False)
    boot = pd.read_csv(BOOT)
    boot.loc[boot.comparison_type.eq("label_view")].to_csv(args.out / "paired_endpoint_differences_cluster_bootstrap_5000.csv", index=False)
    registry = pd.DataFrame([
        {"result_family": "fixed_budget_discovery", "primary_quantity": "stable_yield_at_K", "support": "M1", "row_n": 31872, "K": "100,300,500,1000,5000,10000"},
        {"result_family": "ranking_quality", "primary_quantity": "AUPRC", "support": "M1", "row_n": 31872, "K": ""},
        {"result_family": "endpoint_difference", "primary_quantity": "paired AUPRC and stable-yield difference", "support": "M1", "row_n": 31872, "K": 1000},
        {"result_family": "selection_change", "primary_quantity": "stable-candidate Jaccard and endpoint-changed candidate count", "support": "M1", "row_n": 31872, "K": "100,300,500,1000,5000,10000"},
    ])
    registry.to_csv(args.out / "primary_result_registry.csv", index=False)
    (args.out / "primary_discovery_evidence_metadata.json").write_text(json.dumps({"support": "M1 all-view common support", "row_n": 31872, "models": list(MODELS), "views": list(VIEWS), "bootstrap_replicates": 5000, "cluster_schemes": ["chemical_system", "reduced_formula", "prototype_proxy"]}, indent=2) + "\n")
    print(f"wrote primary discovery evidence to {args.out}")


if __name__ == "__main__":
    main()
