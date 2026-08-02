#!/usr/bin/env python3
"""Compare complete source-pool hull endpoints with archived label views."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "outputs" / "phase1_v2"
REFEREE = ROOT / "outputs" / "evidence_strengthening_v1" / "unified_referee_subset_1200" / "unified_referee_subset_1200.parquet"
POOL = ROOT / "outputs" / "evidence_strengthening_v1" / "full_phase_pool_referee_1200"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pool", type=Path, default=POOL)
    args = p.parse_args()
    targets = pd.read_parquet(REFEREE, columns=["referee_subset_id", "row_id", "referee_stratum", "chemical_system"])
    hulls = pd.read_parquet(args.pool / "referee_full_phase_pool_hull_labels.parquet")
    wide = hulls.pivot(index="referee_subset_id", columns="source", values=["full_pool_e_above_hull_eV_per_atom", "full_pool_stable", "pool_status", "phase_pool_n"])
    wide.columns = ["_".join(map(str, x)) for x in wide.columns]
    out = targets.merge(wide.reset_index(), on="referee_subset_id", how="left", validate="one_to_one")
    labels = pd.read_parquet(PHASE1 / "labels_by_view.parquet")
    blocks = []
    for view in ("mp_native", "alex_pbe_native", "mp_common_pool", "alex_pbe_common_pool"):
        x = labels.loc[labels.label_view.eq(view), ["row_id", "label"]].drop_duplicates("row_id")
        blocks.append(x.rename(columns={"label": view}).set_index("row_id"))
    out = out.join(pd.concat(blocks, axis=1), on="row_id")
    out["mp_full_pool_vs_alexandria_full_pool_switch"] = out["full_pool_stable_mp"].astype("boolean") != out["full_pool_stable_alexandria_pbe"].astype("boolean")
    out["mp_native_vs_full_pool_changed"] = out["mp_native"].astype("boolean") != out["full_pool_stable_mp"].astype("boolean")
    out["alex_native_vs_full_pool_changed"] = out["alex_pbe_native"].astype("boolean") != out["full_pool_stable_alexandria_pbe"].astype("boolean")
    out.to_parquet(args.pool / "referee_full_phase_pool_comparison.parquet", index=False)
    out.to_csv(args.pool / "referee_full_phase_pool_comparison.csv", index=False)
    both = out["full_pool_stable_mp"].notna() & out["full_pool_stable_alexandria_pbe"].notna()
    summary = {
        "target_n": len(out), "both_source_full_pool_evaluable_n": int(both.sum()),
        "mp_full_pool_evaluable_n": int(out["full_pool_stable_mp"].notna().sum()),
        "alexandria_full_pool_evaluable_n": int(out["full_pool_stable_alexandria_pbe"].notna().sum()),
        "full_pool_source_switch_n": int(out.loc[both, "mp_full_pool_vs_alexandria_full_pool_switch"].sum()),
        "full_pool_source_switch_rate": float(out.loc[both, "mp_full_pool_vs_alexandria_full_pool_switch"].mean()),
        "mp_native_to_full_pool_change_n": int(out["mp_native_vs_full_pool_changed"].dropna().sum()),
        "alex_native_to_full_pool_change_n": int(out["alex_native_vs_full_pool_changed"].dropna().sum()),
    }
    pd.DataFrame([summary]).to_csv(args.pool / "referee_full_phase_pool_comparison_summary.csv", index=False)
    out.groupby("referee_stratum", dropna=False).agg(target_n=("row_id", "size"), both_source_evaluable=("mp_full_pool_vs_alexandria_full_pool_switch", "count"), full_pool_switch_rate=("mp_full_pool_vs_alexandria_full_pool_switch", "mean"), mp_pool_phase_median=("phase_pool_n_mp", "median"), alex_pool_phase_median=("phase_pool_n_alexandria_pbe", "median")).reset_index().to_csv(args.pool / "referee_full_phase_pool_by_stratum.csv", index=False)
    (args.pool / "referee_full_phase_pool_comparison_metadata.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
