"""
Query MP API for formation_energy_per_atom for discordant pairs.

Purpose: Disambiguate mechanism (a) genuine DFT disagreement vs (b) hull-reference-only.
If MP.formation_energy_per_atom differs from Alexandria's implicit formation energy,
the discordance reflects cross-workflow energy differences (mechanism a).
If formation energies agree and only e_above_hull differs, it's reference-set (mechanism b).

Since Alexandria's mp-tagged rows are source-linked to MP by construction,
Alex.e_form == MP.e_form under mechanism (b). We query MP.e_form and analyze.

Output: table_mp_formation_energy_discordant.csv
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
from mp_api.client import MPRester

ROOT = Path("")
OUT = ROOT / "outputs" / "milestones" / "materials_label_discordance_full_mp_alex_43984"
MATCHES_CSV = OUT / "table_full_mp_alex_structure_matches.csv"
CACHE_JSONL = OUT / "mp_formation_energy_cache.jsonl"
RESULT_CSV = OUT / "table_mp_formation_energy_discordant.csv"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    api_key = os.environ.get("MP_API_KEY")
    if not api_key:
        raise RuntimeError("MP_API_KEY is required; source /root/.mp_api_env before running.")

    # Load discordant material_ids
    df = pd.read_csv(MATCHES_CSV)
    strict = df[df["match_status"] == "strict_structure_match"]
    disc = strict[strict["mp_stable_exact"] != strict["alex_stable_exact"]]
    disc_ids = sorted(disc["material_id"].unique().tolist())
    print(f"Discordant material_ids to query: {len(disc_ids)}", flush=True)

    # Read already-fetched cache
    done: set[str] = set()
    if CACHE_JSONL.exists():
        with CACHE_JSONL.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    done.add(str(json.loads(line)["material_id"]))
                except Exception:
                    continue
    print(f"Already cached: {len(done)}", flush=True)

    todo = [mid for mid in disc_ids if mid not in done]
    print(f"To fetch: {len(todo)}", flush=True)
    if not todo:
        print("All records already cached.", flush=True)
    else:
        chunk_size = 200
        with MPRester(api_key) as mpr, CACHE_JSONL.open("a", encoding="utf-8") as out:
            for start in range(0, len(todo), chunk_size):
                chunk = todo[start : start + chunk_size]
                try:
                    docs = mpr.materials.summary.search(
                        material_ids=chunk,
                        fields=[
                            "material_id",
                            "formula_pretty",
                            "energy_above_hull",
                            "formation_energy_per_atom",
                            "energy_per_atom",
                            "uncorrected_energy_per_atom",
                            "composition",
                            "chemsys",
                        ],
                    )
                except Exception as e:
                    print(f"Error on chunk starting at {start}: {e}", flush=True)
                    time.sleep(2)
                    continue

                returned = set()
                for doc in docs:
                    mid = str(doc.material_id)
                    returned.add(mid)
                    out.write(
                        json.dumps({
                            "material_id": mid,
                            "formula_pretty": getattr(doc, "formula_pretty", None),
                            "energy_above_hull": float(doc.energy_above_hull)
                            if doc.energy_above_hull is not None else None,
                            "formation_energy_per_atom": float(doc.formation_energy_per_atom)
                            if getattr(doc, "formation_energy_per_atom", None) is not None else None,
                            "energy_per_atom": float(doc.energy_per_atom)
                            if getattr(doc, "energy_per_atom", None) is not None else None,
                            "uncorrected_energy_per_atom": float(doc.uncorrected_energy_per_atom)
                            if getattr(doc, "uncorrected_energy_per_atom", None) is not None else None,
                            "chemsys": getattr(doc, "chemsys", None),
                        }) + "\n"
                    )

                for missing in sorted(set(chunk) - returned):
                    out.write(
                        json.dumps({
                            "material_id": missing,
                            "formula_pretty": None,
                            "energy_above_hull": None,
                            "formation_energy_per_atom": None,
                            "energy_per_atom": None,
                            "uncorrected_energy_per_atom": None,
                            "chemsys": None,
                            "missing_mp_record": True,
                        }) + "\n"
                    )
                out.flush()
                fetched = len(done) + min(start + chunk_size, len(todo))
                print(f"Fetched ~{fetched}/{len(todo) + len(done)}", flush=True)
                time.sleep(0.15)

    # Build result CSV: join MP formation energy with existing match data
    cache: dict[str, dict] = {}
    with CACHE_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            cache[str(row["material_id"])] = row

    rows = []
    for _, row in disc.iterrows():
        mid = str(row["material_id"])
        mp_data = cache.get(mid, {})
        rows.append({
            "material_id": mid,
            "formula": row["formula"],
            "chemical_system": row["chemical_system"],
            "num_sites": row["num_sites"],
            "mp_e_above_hull_original": row["mp_e_above_hull"],
            "mp_e_above_hull_requeried": mp_data.get("energy_above_hull"),
            "alex_e_above_hull": row["alex_e_above_hull"],
            "mp_stable_exact": row["mp_stable_exact"],
            "alex_stable_exact": row["alex_stable_exact"],
            "mp_formation_energy_per_atom": mp_data.get("formation_energy_per_atom"),
            "mp_energy_per_atom": mp_data.get("energy_per_atom"),
            "mp_uncorrected_energy_per_atom": mp_data.get("uncorrected_energy_per_atom"),
        })

    result_df = pd.DataFrame(rows)
    result_df.to_csv(RESULT_CSV, index=False)
    print(f"\nWrote {len(result_df)} rows to {RESULT_CSV}", flush=True)

    # Summary
    n_with_form_e = result_df["mp_formation_energy_per_atom"].notna().sum()
    n_missing = result_df["mp_formation_energy_per_atom"].isna().sum()
    print(f"Formation energy available: {n_with_form_e}/{len(result_df)}", flush=True)
    print(f"Missing: {n_missing}", flush=True)
    print(f"Cache SHA256: {sha256_file(CACHE_JSONL)}", flush=True)


if __name__ == "__main__":
    main()
