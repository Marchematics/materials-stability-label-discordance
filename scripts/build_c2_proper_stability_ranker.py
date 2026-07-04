"""
C2 fix: Replace CHGNet formation-energy proxy with proper e_above_hull predictor.

1. Query MP formation_energy_per_atom for all 5000 CHGNet-scored structures
2. Compute MP.hull_ref = MP.formation_energy_per_atom - MP.energy_above_hull
3. Compute pred_e_above_hull = CHGNet_formation_energy_proxy - MP.hull_ref
4. New score = -pred_e_above_hull (proper stability ranker)
5. Recompute all metrics and check if precision@K shift > base-rate gap
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from mp_api.client import MPRester
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path("")
OUT = ROOT / "outputs" / "milestones" / "model_facing_benchmark_sensitivity_check"
FULL_OUT = ROOT / "outputs" / "milestones" / "materials_label_discordance_full_mp_alex_43984"
SCORES_IN = OUT / "candidate_scores_chgnet_5000.csv"
FORM_E_CACHE = FULL_OUT / "mp_formation_energy_cache.jsonl"  # reuse existing cache
CHGNET_FORM_E_CACHE = OUT / "mp_formation_energy_chgnet_5000.jsonl"
SCORES_OUT = OUT / "candidate_scores_chgnet_5000_v2_ehull.csv"
N_BOOTSTRAP = 2000
BOOTSTRAP_SEED = 20260606


def main() -> None:
    # ---- Load existing CHGNet scores ----
    scores = pd.read_csv(SCORES_IN)
    print(f"Loaded {len(scores)} CHGNet-scored structures", flush=True)

    # ---- Load MP formation_energy_per_atom ----
    # First, try to get from existing cache + new query
    existing: dict[str, dict] = {}
    for cache_path in [FORM_E_CACHE, CHGNET_FORM_E_CACHE]:
        if cache_path.exists():
            with cache_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    existing[str(row["material_id"])] = row

    ids_needed = set(scores["material_id"].tolist())
    have = set(existing) & ids_needed
    todo = sorted(ids_needed - have)
    print(f"Already have formation_energy: {len(have)}, need to query: {len(todo)}", flush=True)

    if todo:
        api_key = os.environ.get("MP_API_KEY")
        if not api_key:
            raise RuntimeError("MP_API_KEY required")

        chunk_size = 200
        with MPRester(api_key) as mpr, CHGNET_FORM_E_CACHE.open("a", encoding="utf-8") as out:
            for start in range(0, len(todo), chunk_size):
                chunk = todo[start : start + chunk_size]
                docs = mpr.materials.summary.search(
                    material_ids=chunk,
                    fields=["material_id", "formation_energy_per_atom", "energy_above_hull"],
                )
                returned = set()
                for doc in docs:
                    mid = str(doc.material_id)
                    returned.add(mid)
                    out.write(json.dumps({
                        "material_id": mid,
                        "formation_energy_per_atom": float(getattr(doc, "formation_energy_per_atom", None) or 0),
                        "energy_above_hull": float(getattr(doc, "energy_above_hull", None) or 0),
                    }) + "\n")
                    existing[mid] = {
                        "material_id": mid,
                        "formation_energy_per_atom": float(getattr(doc, "formation_energy_per_atom", None) or 0),
                        "energy_above_hull": float(getattr(doc, "energy_above_hull", None) or 0),
                    }
                for missing in sorted(set(chunk) - returned):
                    existing[missing] = {
                        "material_id": missing,
                        "formation_energy_per_atom": None,
                        "energy_above_hull": None,
                    }
                out.flush()
                print(f"Queried {min(start + chunk_size, len(todo))}/{len(todo)}", flush=True)
                time.sleep(0.1)

    # ---- Merge and compute new scores ----
    rows = []
    for _, row in scores.iterrows():
        mid = str(row["material_id"])
        mp_data = existing.get(mid, {})
        mp_e_form = mp_data.get("formation_energy_per_atom")
        mp_e_hull = mp_data.get("energy_above_hull")

        if mp_e_form is None or mp_e_hull is None:
            print(f"WARNING: missing MP data for {mid}, skipping", flush=True)
            continue

        mp_hull_ref = mp_e_form - mp_e_hull  # MP's hull reference for this composition
        chgnet_form = row["formation_energy_proxy"]
        pred_e_hull = chgnet_form - mp_hull_ref  # predicted e_above_hull
        score = -pred_e_hull  # higher = more stable

        rows.append({
            "material_id": mid,
            "formula": row["formula"],
            "chemical_system": row["chemical_system"],
            "model": "CHGNet",
            "model_version": "CHGNet.load()",
            "energy_per_atom": row["energy_per_atom"],
            "formation_energy_proxy": chgnet_form,
            "mp_formation_energy_per_atom": mp_e_form,
            "mp_energy_above_hull": mp_e_hull,
            "mp_hull_reference": mp_hull_ref,
            "predicted_e_above_hull": pred_e_hull,
            "score": score,
            "score_type": "negative_predicted_e_above_hull_higher_is_more_stable",
            "mp_stable": row["mp_stable"],
            "alex_stable": row["alex_stable"],
            "source_agreement": row["source_agreement"],
            "mp_e_above_hull": row["mp_e_above_hull"],
            "alex_e_above_hull": row["alex_e_above_hull"],
        })

    df = pd.DataFrame(rows)
    df.to_csv(SCORES_OUT, index=False)
    print(f"\nWrote {len(df)} rows to {SCORES_OUT}", flush=True)

    # ---- Compute metrics ----
    y_mp = df["mp_stable"].astype(bool)
    y_alex = df["alex_stable"].astype(bool)
    score = df["score"].astype(float)

    auroc_mp = roc_auc_score(y_mp, score)
    auroc_alex = roc_auc_score(y_alex, score)
    auprc_mp = average_precision_score(y_mp, score)
    auprc_alex = average_precision_score(y_alex, score)

    base_rate_mp = y_mp.mean()
    base_rate_alex = y_alex.mean()
    base_rate_gap = base_rate_mp - base_rate_alex

    print(f"\n=== NEW Model Metrics (e_above_hull predictor) ===")
    print(f"AUROC: MP={auroc_mp:.4f}, Alex={auroc_alex:.4f}, delta={auroc_mp - auroc_alex:+.4f}")
    print(f"AUPRC: MP={auprc_mp:.4f}, Alex={auprc_alex:.4f}")
    print(f"Base rate: MP={base_rate_mp:.4f}, Alex={base_rate_alex:.4f}, gap={base_rate_gap*100:.2f} pp")

    # ---- Precision@K ----
    ranked = df.sort_values(["score", "material_id"], ascending=[False, True])
    print(f"\n=== Precision@K ===")
    print(f"{'K':>6s}  {'MP_prec':>8s}  {'Alex_prec':>9s}  {'shift':>8s}  {'shift-baserate':>14s}  {'verdict':>20s}")
    informative = False
    for k in [100, 300, 500, 1000, 2000]:
        top = ranked.head(k)
        mp_p = top["mp_stable"].astype(bool).mean()
        alex_p = top["alex_stable"].astype(bool).mean()
        shift = mp_p - alex_p
        excess = shift - base_rate_gap
        verdict = "INFORMATIVE" if excess > 0 else "NOT informative"
        if excess > 0:
            informative = True
        print(f"{k:6d}  {mp_p:8.4f}  {alex_p:9.4f}  {shift:8.4f}  {excess*100:14.2f} pp  {verdict:>20s}")

    # ---- Bootstrap CI for K=300 shift ----
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    for k in [100, 300, 500]:
        top = ranked.head(k).reset_index(drop=True)
        obs = float(top["mp_stable"].astype(bool).mean() - top["alex_stable"].astype(bool).mean())
        shifts = []
        idx = np.arange(k)
        for _ in range(N_BOOTSTRAP):
            boot = top.iloc[rng.choice(idx, size=k, replace=True)]
            shifts.append(float(boot["mp_stable"].astype(bool).mean() - boot["alex_stable"].astype(bool).mean()))
        lo, hi = np.quantile(shifts, [0.025, 0.975])
        print(f"\nK={k} bootstrap: shift={obs:.4f}, 95% CI=[{lo:.4f}, {hi:.4f}]")

    print(f"\n=== CONCLUSION ===")
    if informative:
        print(f"Precision@K shift EXCEEDS base-rate gap at some K → C2 analysis INFORMATIVE, keep in paper.")
    else:
        print(f"Precision@K shift DOES NOT exceed base-rate gap → C2 analysis should be DROPPED from paper.")


if __name__ == "__main__":
    main()
