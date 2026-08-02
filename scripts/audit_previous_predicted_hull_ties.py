#!/usr/bin/env python3
"""Audit the superseded self-included predicted-hull ranking and row-ID tie rule."""

from pathlib import Path

import numpy as np
import pandas as pd

from sourceaware.ranking import analytic_tie_aware_topk, score_tie_audit


ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "outputs" / "repaired_model_evaluation_v2" / "denominator_all_view_common_support.parquet"
OUT = ROOT / "outputs" / "referee_revision_v3" / "superseded_ranking_audit"
MODELS = ("ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP")
ENDPOINTS = ("mp_native", "alexmp20_native", "alex_pbe_native", "common_pool")
K_VALUES = (100, 300, 500, 1000, 5000)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = pd.read_parquet(OLD)
    audit_rows = []
    comparison_rows = []
    for model in MODELS:
        audit = score_tie_audit(frame[model], K_VALUES)
        audit.insert(0, "model_name", model)
        audit_rows.append(audit)
        ranked = frame.sort_values([model, "row_id"], ascending=[False, True], kind="mergesort")
        for endpoint in ENDPOINTS:
            y = frame[endpoint].astype(int)
            for k in K_VALUES:
                analytic = analytic_tie_aware_topk(frame[model], y, k)
                row_id_hits = int(ranked.head(k)[endpoint].sum())
                comparison_rows.append(
                    {
                        "model_name": model,
                        "endpoint": endpoint,
                        "K": k,
                        "row_id_selected_hits": row_id_hits,
                        "row_id_selected_yield": row_id_hits / k,
                        "row_id_minus_tie_expected_hits": row_id_hits - analytic["expected_stable_hits"],
                        **analytic,
                    }
                )
    pd.concat(audit_rows, ignore_index=True).to_csv(
        OUT / "previous_self_included_hull_tie_audit.csv", index=False
    )
    pd.DataFrame(comparison_rows).to_csv(
        OUT / "previous_row_id_vs_analytic_tie_topk.csv", index=False
    )


if __name__ == "__main__":
    main()
