#!/usr/bin/env python3
"""Build source-coverage and formula-union inventories for the referee phase pool."""
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

import pandas as pd
from pymatgen.core import Composition


ROOT = Path(__file__).resolve().parents[1]
POOL = ROOT / "outputs" / "evidence_strengthening_v1" / "full_phase_pool_referee_1200"
REFEREE = ROOT / "outputs" / "evidence_strengthening_v1" / "unified_referee_subset_1200" / "unified_referee_subset_1200.parquet"


def _entries(path: Path, source: str) -> pd.DataFrame:
    rows = []
    with path.open() as handle:
        for line in handle:
            d = json.loads(line)
            formula = d.get("formula")
            if not formula:
                continue
            try:
                comp = Composition(formula)
                elements = "-".join(sorted(str(e) for e in comp.elements))
                reduced = comp.reduced_formula
            except Exception:
                continue
            rows.append({"source": source, "source_id": d.get("mp_id") if source == "mp" else d.get("alexandria_id"), "formula": formula, "reduced_formula": reduced, "phase_chemical_system": elements})
    return pd.DataFrame(rows).drop_duplicates(["source", "source_id"])


def _subsystems(system: str) -> set[str]:
    elements = sorted(system.split("-"))
    return {"-".join(c) for r in range(1, len(elements) + 1) for c in combinations(elements, r)}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pool", type=Path, default=POOL)
    args = p.parse_args()
    mp = _entries(args.pool / "mp_relevant_phase_entries.jsonl", "mp")
    alex = _entries(args.pool / "alexandria_pbe_2025_07_02_relevant_phase_entries.jsonl", "alexandria_pbe")
    union = pd.concat([mp, alex], ignore_index=True)
    union.to_parquet(args.pool / "referee_source_union_phase_inventory.parquet", index=False)
    union.to_csv(args.pool / "referee_source_union_phase_inventory.csv", index=False)
    targets = pd.read_parquet(REFEREE, columns=["referee_subset_id", "chemical_system"])
    by_system = {key: group for key, group in union.groupby("phase_chemical_system", sort=False)}
    rows = []
    for row in targets.itertuples(index=False):
        allowed = _subsystems(row.chemical_system)
        local = pd.concat([by_system[key] for key in allowed if key in by_system], ignore_index=True)
        mp_local = local.loc[local.source.eq("mp")]
        alex_local = local.loc[local.source.eq("alexandria_pbe")]
        union_formula = local.reduced_formula.nunique()
        rows.append({"referee_subset_id": row.referee_subset_id, "chemical_system": row.chemical_system,
                     "mp_phase_n": len(mp_local), "alexandria_phase_n": len(alex_local), "source_union_phase_n": len(local),
                     "mp_formula_n": mp_local.reduced_formula.nunique(), "alexandria_formula_n": alex_local.reduced_formula.nunique(),
                     "source_union_formula_n": union_formula,
                     "shared_formula_n": len(set(mp_local.reduced_formula) & set(alex_local.reduced_formula))})
    coverage = pd.DataFrame(rows)
    coverage.to_csv(args.pool / "referee_source_union_phase_coverage.csv", index=False)
    summary = {"mp_phase_entry_n": int(len(mp)), "alexandria_phase_entry_n": int(len(alex)), "union_phase_entry_n": int(len(union)),
               "mp_reduced_formula_n": int(mp.reduced_formula.nunique()), "alexandria_reduced_formula_n": int(alex.reduced_formula.nunique()),
               "union_reduced_formula_n": int(union.reduced_formula.nunique()), "referee_target_n": int(len(coverage)),
               "median_source_union_phase_n_per_target": float(coverage.source_union_phase_n.median()),
               "median_source_union_formula_n_per_target": float(coverage.source_union_formula_n.median())}
    pd.DataFrame([summary]).to_csv(args.pool / "referee_source_union_inventory_summary.csv", index=False)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
