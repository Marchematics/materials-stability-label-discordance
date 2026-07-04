"""
M1: Signed hull-distance near-hull analysis (non-tautological).

Replaces the tautological "either-source |e_hull|" threshold sweep with
source-specific signed analyses:
1. Per-source flagging: at threshold t, flag structures with |e_hull| < t in THAT source
2. Cross-source prediction: can MP's near-hull flag predict Alex disagreement?
3. Both-sources analysis: structures flagged by BOTH sources vs EITHER source
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np

ROOT = Path("")
FULL = ROOT / "outputs" / "milestones" / "materials_label_discordance_full_mp_alex_43984"
OUT = ROOT / "outputs" / "milestones" / "benchmark_reliability_enhancement"
MATCHES_CSV = FULL / "table_full_mp_alex_structure_matches.csv"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(MATCHES_CSV)
    strict = df[df["match_status"] == "strict_structure_match"].copy()
    strict["discordant"] = (strict["mp_stable_exact"] != strict["alex_stable_exact"]).astype(int)
    strict["mp_ehull"] = pd.to_numeric(strict["mp_e_above_hull"], errors="coerce")
    strict["alex_ehull"] = pd.to_numeric(strict["alex_e_above_hull"], errors="coerce")
    strict["signed_delta"] = strict["mp_ehull"] - strict["alex_ehull"]

    n_total = len(strict)
    n_disc = strict["discordant"].sum()
    print(f"Total: {n_total}, Discordant: {n_disc}", flush=True)

    # ---- Per-source signed threshold sweep ----
    thresholds_meV = [1, 2, 5, 10, 25, 50, 100]
    rows = []
    for thresh_meV in thresholds_meV:
        thresh = thresh_meV / 1000.0  # convert to eV

        for source in ["mp", "alex", "either", "both"]:
            ehull_col = f"{source}_ehull" if source in ["mp", "alex"] else None

            if source == "mp":
                flagged = strict["mp_ehull"].abs() < thresh
            elif source == "alex":
                flagged = strict["alex_ehull"].abs() < thresh
            elif source == "either":
                flagged = (strict["mp_ehull"].abs() < thresh) | (strict["alex_ehull"].abs() < thresh)
            elif source == "both":
                flagged = (strict["mp_ehull"].abs() < thresh) & (strict["alex_ehull"].abs() < thresh)

            n_flagged = flagged.sum()
            n_disc_captured = (flagged & strict["discordant"].astype(bool)).sum()
            n_concordant_flagged = (flagged & ~strict["discordant"].astype(bool)).sum()

            recall = n_disc_captured / n_disc if n_disc > 0 else 0
            precision = n_disc_captured / n_flagged if n_flagged > 0 else 0
            burden = n_flagged / n_total

            rows.append({
                "threshold_meV": thresh_meV,
                "source": source,
                "n_flagged": n_flagged,
                "flagged_fraction": burden,
                "discordant_captured": n_disc_captured,
                "discordant_total": n_disc,
                "discordant_recall": recall,
                "concordant_flagged": n_concordant_flagged,
                "flag_precision": precision,
                "non_tautological": source in ["mp", "alex", "both"],  # "either" is tautological
            })

    sweep_df = pd.DataFrame(rows)
    sweep_df.to_csv(OUT / "table_signed_hull_distance_sweep.csv", index=False)

    # ---- Key summary ----
    print("\n=== Signed hull-distance sweep (non-tautological) ===")
    print(f"{'thr_meV':>8s} {'src':>6s} {'flagged':>8s} {'flagged%':>9s} {'disc_capt':>9s} {'recall':>7s} {'precision':>10s}")
    for _, r in sweep_df.iterrows():
        if r["non_tautological"]:
            print(f"{r['threshold_meV']:8d} {r['source']:>6s} {r['n_flagged']:8d} {r['flagged_fraction']:9.4f} {r['discordant_captured']:9d} {r['discordant_recall']:7.4f} {r['flag_precision']:10.4f}")

    # ---- Physical interpretation ----
    print("\n=== Physical interpretation ===")
    # At 5 meV: MP flags 4171/5060 (82.4%) discordant, Alexandria flags 2572/5060 (50.8%)
    mp_5 = sweep_df[(sweep_df["threshold_meV"] == 5) & (sweep_df["source"] == "mp")]
    al_5 = sweep_df[(sweep_df["threshold_meV"] == 5) & (sweep_df["source"] == "alex")]
    both_5 = sweep_df[(sweep_df["threshold_meV"] == 5) & (sweep_df["source"] == "both")]
    either_5 = sweep_df[(sweep_df["threshold_meV"] == 5) & (sweep_df["source"] == "either")]

    print(f"MP 5meV flag: {int(mp_5['discordant_captured'].iloc[0])}/{n_disc} = {mp_5['discordant_recall'].iloc[0]:.3f} recall, "
          f"{mp_5['flagged_fraction'].iloc[0]:.3f} burden")
    print(f"Alex 5meV flag: {int(al_5['discordant_captured'].iloc[0])}/{n_disc} = {al_5['discordant_recall'].iloc[0]:.3f} recall, "
          f"{al_5['flagged_fraction'].iloc[0]:.3f} burden")
    print(f"Both 5meV flag: {int(both_5['discordant_captured'].iloc[0])}/{n_disc} = {both_5['discordant_recall'].iloc[0]:.3f} recall, "
          f"{both_5['flagged_fraction'].iloc[0]:.3f} burden")
    print(f"Either 5meV flag: {int(either_5['discordant_captured'].iloc[0])}/{n_disc} = {either_5['discordant_recall'].iloc[0]:.3f} recall, "
          f"{either_5['flagged_fraction'].iloc[0]:.3f} burden (TAUTOLOGICAL — do not use as headline)")

    # ---- Discordance decomposed by MP signed e_hull bin ----
    bins = [-float("inf"), -0.100, -0.050, -0.025, -0.010, -0.005, 0, 0.005, 0.010, 0.025, 0.050, 0.100, float("inf")]
    labels = ["<-100", "-100:-50", "-50:-25", "-25:-10", "-10:-5", "-5:0", "0:5", "5:10", "10:25", "25:50", "50:100", ">100"]
    strict["mp_ehull_bin"] = pd.cut(strict["mp_ehull"], bins=bins, labels=labels)
    bin_stats = strict.groupby("mp_ehull_bin", observed=False).agg(
        n=("discordant", "count"),
        discordant_n=("discordant", "sum"),
        mp_stable_rate=("mp_stable_exact", lambda x: (x.astype(str).str.lower() == "true").mean()),
        alex_stable_rate=("alex_stable_exact", lambda x: (x.astype(str).str.lower() == "true").mean()),
    ).reset_index()
    bin_stats["discordance_rate"] = bin_stats["discordant_n"] / bin_stats["n"]
    bin_stats.to_csv(OUT / "table_signed_ehull_bin_discordance.csv", index=False)

    print("\n=== Discordance by MP signed e_hull bin ===")
    print(bin_stats.to_string(index=False))


if __name__ == "__main__":
    main()
