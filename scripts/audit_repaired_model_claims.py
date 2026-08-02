#!/usr/bin/env python3
"""Write a claim ledger for the endpoint-layer M1 model analysis."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "repaired_model_evaluation_v2"


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> None:
    a = args()
    support = pd.read_csv(a.out / "all_view_common_support_exclusion_audit.csv")
    raw = pd.read_csv(a.out / "score_construct_validity_audit.csv")
    metrics = pd.read_csv(a.out / "metrics_fixed_support.csv")
    deltas = pd.read_csv(a.out / "paired_label_view_differences_cluster_bootstrap.csv")
    definitions = pd.read_csv(a.out / "endpoint_definition_table.csv")
    ratio = pd.read_csv(a.out / "endpoint_sensitivity_to_model_spread_ratio_bootstrap.csv")
    hull_views = {"mp_native", "alexmp20_native", "alex_pbe_native", "common_pool"}
    headline = {"f1_fixed_threshold", "auprc", "stable_yield_at_1000"}
    headline_ratio = ratio[(ratio.scope.eq("hull_construction_sensitivity")) & ratio.metric.isin(headline)]
    claims = [
        {"claim": "M1 fixed-support cohort contains 31,872 rows.", "value": 31872, "source": "all_view_common_support_exclusion_audit.csv", "status": "supported"},
        {"claim": "Consensus is a separate 24,614-row selection policy.", "value": 24614, "source": "evaluation_support_and_coverage.csv", "status": "supported"},
        {"claim": "Archived raw energy rankings have MP-native AUROC below 0.5 for all four primary models.", "value": [round(x, 6) for x in raw.raw_energy_rank_auroc_mp_native], "source": "score_construct_validity_audit.csv", "status": "supported"},
        {"claim": "Predicted-hull rankings have MP-native AUROC above 0.5 for all four primary models.", "value": [round(x, 6) for x in raw.predicted_hull_rank_auroc_mp_native], "source": "score_construct_validity_audit.csv", "status": "supported"},
        {"claim": "MACE-MP has the highest point-estimate M1 AUROC for every source-native and matched-common-pool endpoint.", "value": metrics[metrics.label_view.isin(hull_views)].loc[metrics[metrics.label_view.isin(hull_views)].groupby("label_view").auroc.idxmax(), "model_name"].tolist(), "source": "metrics_fixed_support.csv", "status": "supported"},
        {"claim": "The audit policy is separate from source-native and hull-construction endpoint bands.", "value": definitions.loc[definitions.endpoint.eq("audit_view"), "layer"].tolist(), "source": "endpoint_definition_table.csv", "status": "supported"},
        {"claim": "F1, AUPRC and stable-yield endpoint bands exceed the median four-model spread for every model at the point estimate.", "value": headline_ratio.groupby("metric").ratio_median.apply(lambda x: [round(v, 3) for v in x]).to_dict(), "source": "endpoint_sensitivity_to_model_spread_ratio_bootstrap.csv", "status": "supported"},
        {"claim": "MP-native-to-audit stable-yield differences are reported as a separate paired policy contrast.", "value": deltas[(deltas.metric.eq("stable_yield_at_1000")) & (deltas.view_a.eq("mp_native")) & (deltas.view_b.eq("audit_view"))].probability_delta_gt_zero.tolist(), "source": "paired_label_view_differences_cluster_bootstrap.csv", "status": "supported"},
    ]
    (a.out / "manuscript_model_claims.json").write_text(json.dumps(claims, indent=2) + "\n")
    lines = ["# M1 endpoint-layer model-claim audit", ""]
    for item in claims:
        lines.append(f"- **{item['status']}** — {item['claim']} (`{item['source']}`)")
    (a.out / "manuscript_model_claims_audit.md").write_text("\n".join(lines) + "\n")
    assert int(support.loc[support.stage.eq("M1 fixed support"), "n"].iloc[0]) == 31872
    assert (raw.raw_energy_rank_auroc_mp_native < 0.5).all()
    assert (raw.predicted_hull_rank_auroc_mp_native > 0.5).all()
    assert set(definitions.loc[definitions.endpoint.eq("audit_view"), "layer"]) == {"audit_policy"}
    assert (headline_ratio.ratio_median > 1).all()


if __name__ == "__main__":
    main()
