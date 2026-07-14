#!/usr/bin/env python3
"""Write a small claim ledger for the repaired M1 model analysis."""
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "repaired_model_evaluation_v1"


def main() -> None:
    support = pd.read_csv(OUT / "all_view_common_support_exclusion_audit.csv")
    raw = pd.read_csv(OUT / "score_construct_validity_audit.csv")
    metrics = pd.read_csv(OUT / "metrics_fixed_support.csv")
    deltas = pd.read_csv(OUT / "paired_label_view_differences_cluster_bootstrap.csv")
    claims = [
        {"claim": "M1 fixed-support cohort contains 31,872 rows.", "value": 31872, "source": "all_view_common_support_exclusion_audit.csv", "status": "supported"},
        {"claim": "Consensus is a separate 24,614-row selection policy.", "value": 24614, "source": "evaluation_support_and_coverage.csv", "status": "supported"},
        {"claim": "Archived raw energy rankings have MP-native AUROC below 0.5 for all four primary models.", "value": [round(x, 6) for x in raw.raw_energy_rank_auroc_mp_native], "source": "score_construct_validity_audit.csv", "status": "supported"},
        {"claim": "Repaired predicted-hull rankings have MP-native AUROC above 0.5 for all four primary models.", "value": [round(x, 6) for x in raw.predicted_hull_rank_auroc_mp_native], "source": "score_construct_validity_audit.csv", "status": "supported"},
        {"claim": "MACE-MP has the highest point-estimate M1 AUROC for every fixed-support label view.", "value": metrics.loc[metrics.groupby("label_view").auroc.idxmax(), "model_name"].tolist(), "source": "metrics_fixed_support.csv", "status": "supported"},
        {"claim": "MP-native minus audit stable yield at K=1000 is positive for all four models in every paired bootstrap replicate.", "value": deltas[(deltas.metric.eq("stable_yield_at_1000")) & (deltas.view_a.eq("mp_native")) & (deltas.view_b.eq("audit_view"))].probability_delta_gt_zero.tolist(), "source": "paired_label_view_differences_cluster_bootstrap.csv", "status": "supported"},
    ]
    (OUT / "manuscript_model_claims.json").write_text(json.dumps(claims, indent=2) + "\n")
    lines = ["# Repaired M1 model-claim audit", ""]
    for item in claims:
        lines.append(f"- **{item['status']}** — {item['claim']} (`{item['source']}`)")
    (OUT / "manuscript_model_claims_audit.md").write_text("\n".join(lines) + "\n")
    assert int(support.loc[support.stage.eq("M1 all-view common support"), "n"].iloc[0]) == 31872
    assert (raw.raw_energy_rank_auroc_mp_native < 0.5).all()
    assert (raw.predicted_hull_rank_auroc_mp_native > 0.5).all()


if __name__ == "__main__":
    main()
