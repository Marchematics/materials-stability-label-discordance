"""
Structure-matching tolerance sweep (Sec. 4.3 robustness check).

Re-run StructureMatcher on the MP-Alex pairs with three tolerance settings:
- tight:  ltol=0.1, stol=0.2, angle_tol=3
- default: ltol=0.2, stol=0.3, angle_tol=5  (current)
- loose:  ltol=0.3, stol=0.4, angle_tol=7

Report discordance rate under each setting to show robustness.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.core import Structure


ROOT = Path("")
FULL = ROOT / "outputs" / "milestones" / "materials_label_discordance_full_mp_alex_43984"
OUT = ROOT / "outputs" / "milestones" / "benchmark_reliability_enhancement"
MP_CACHE = Path(
    "outputs/milestones/"
    "materials_label_discordance_full_mp_alex_43984/mp_records_summary_structures.jsonl"
)
ALEX_ZIP = Path("data/alex-mp/alex_mp_20.zip")
MATCHES_CSV = FULL / "table_full_mp_alex_structure_matches.csv"

TOLERANCES = {
    "tight": {"ltol": 0.1, "stol": 0.2, "angle_tol": 3},
    "default": {"ltol": 0.2, "stol": 0.3, "angle_tol": 5},
    "loose": {"ltol": 0.3, "stol": 0.4, "angle_tol": 7},
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # Load MP structures
    print("Loading MP structure cache...", flush=True)
    mp_structures: dict[str, Structure] = {}
    with MP_CACHE.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("structure") and not row.get("missing_mp_record"):
                try:
                    mp_structures[str(row["material_id"])] = Structure.from_dict(row["structure"])
                except Exception:
                    continue
    print(f"Loaded {len(mp_structures)} MP structures", flush=True)

    # Load Alexandria structures from ZIP
    print("Loading Alexandria structures...", flush=True)
    alex_structures: dict[str, Structure] = {}
    alex_labels: dict[str, tuple[float, str]] = {}
    with zipfile.ZipFile(ALEX_ZIP) as zf:
        for csv_name in ["alex_mp_20/train.csv", "alex_mp_20/val.csv"]:
            df = pd.read_csv(zf.open(csv_name))
            for _, row in df.iterrows():
                mid = str(row["material_id"])
                if not mid.startswith("mp-"):
                    continue
                try:
                    struct = Structure.from_str(str(row["cif"]), fmt="cif")
                    alex_structures[mid] = struct
                    alex_labels[mid] = (
                        float(row["energy_above_hull"]),
                        str(csv_name),
                    )
                except Exception:
                    continue
    print(f"Loaded {len(alex_structures)} Alexandria structures", flush=True)

    # Common set of IDs
    common = sorted(set(mp_structures) & set(alex_structures))
    print(f"Common IDs: {len(common)}", flush=True)

    # Load existing match data for labels
    existing = pd.read_csv(MATCHES_CSV)
    existing = existing[existing["match_status"] == "strict_structure_match"]
    existing_ids = set(existing["material_id"])
    common = [mid for mid in common if mid in existing_ids]
    print(f"Common strict-match IDs: {len(common)}", flush=True)

    # Run sweep
    results = []
    for name, params in TOLERANCES.items():
        matcher = StructureMatcher(**params)
        n_checked = 0
        n_matched = 0
        n_discordant = 0
        n_mp_stable = 0
        n_alex_stable = 0

        for mid in common:
            n_checked += 1
            mp_struct = mp_structures[mid]
            alex_struct = alex_structures[mid]

            try:
                matched = matcher.fit(mp_struct, alex_struct)
            except Exception:
                matched = False

            if matched:
                n_matched += 1
                mp_ehull = float(existing[existing["material_id"] == mid]["mp_e_above_hull"].iloc[0])
                alex_ehull = alex_labels[mid][0]
                mp_stable = mp_ehull <= 0
                alex_stable = alex_ehull <= 0
                if mp_stable:
                    n_mp_stable += 1
                if alex_stable:
                    n_alex_stable += 1
                if mp_stable != alex_stable:
                    n_discordant += 1

            if n_checked % 10000 == 0:
                print(f"  {name}: checked {n_checked}/{len(common)}", flush=True)

        disc_rate = n_discordant / n_matched if n_matched > 0 else 0
        results.append({
            "tolerance": name,
            "ltol": params["ltol"],
            "stol": params["stol"],
            "angle_tol": params["angle_tol"],
            "n_checked": n_checked,
            "n_matched": n_matched,
            "match_fraction": n_matched / n_checked if n_checked > 0 else 0,
            "n_discordant": n_discordant,
            "discordance_rate": disc_rate,
            "n_mp_stable": n_mp_stable,
            "mp_stable_rate": n_mp_stable / n_matched if n_matched > 0 else 0,
            "n_alex_stable": n_alex_stable,
            "alex_stable_rate": n_alex_stable / n_matched if n_matched > 0 else 0,
        })
        print(f"  {name}: n_matched={n_matched}, discordant={n_discordant}, rate={disc_rate:.4f}", flush=True)

    result_df = pd.DataFrame(results)
    result_df.to_csv(OUT / "table_structure_matching_tolerance_sweep.csv", index=False)
    print(f"\nWrote results to {OUT / 'table_structure_matching_tolerance_sweep.csv'}")
    print(result_df.to_string(index=False))


if __name__ == "__main__":
    main()
