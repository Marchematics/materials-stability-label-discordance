#!/usr/bin/env python3
"""Construct a 1,200-structure unified-workflow referee subset and job inputs.

The subset draws equal-sized strata from the D2 exact-structure denominator:
phase-pool-sensitive conflicts, persistent conflicts, hidden common-pool
conflicts and source-consistent rows.  MP structures are exported as POSCAR
inputs when the local MP structure cache is available.  The resulting manifest
also enumerates each target chemical system and all elemental subsystems needed
to assemble its competing-phase pool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from pymatgen.core import Structure


ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "outputs" / "phase1_v2"
DEFAULT_CACHE = Path("/home/waas/paper_experiments/github/discordance-/outputs/milestones/materials_label_discordance_full_mp_alex_43984/mp_records_summary_structures.jsonl")
SEED = 20260717
TARGET_PER_STRATUM = 300
NUMERICAL_TOLERANCE = 1e-8


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=ROOT / "outputs" / "evidence_strengthening_v1" / "unified_referee_subset_1200")
    p.add_argument("--structure-cache", type=Path, default=DEFAULT_CACHE)
    p.add_argument("--seed", type=int, default=SEED)
    return p.parse_args()


def _label_wide() -> pd.DataFrame:
    labels = pd.read_parquet(PHASE1 / "labels_by_view.parquet")
    views = ("mp_native", "alex_pbe_native", "mp_common_pool", "alex_pbe_common_pool")
    blocks = []
    for view in views:
        block = labels.loc[labels["label_view"].eq(view), ["row_id", "label", "is_evaluable"]].drop_duplicates("row_id")
        blocks.append(block.rename(columns={"label": view, "is_evaluable": f"{view}_evaluable"}).set_index("row_id"))
    return pd.concat(blocks, axis=1)


def _classify() -> pd.DataFrame:
    d2 = pd.read_parquet(PHASE1 / "denominator_d2_triple_single_match.parquet")
    x = d2[["row_id", "mp_id", "mattergen_id", "official_alexandria_id", "formula", "reduced_formula", "chemical_system", "structure_hash"]].set_index("row_id").join(_label_wide())
    native_valid = x[["mp_native", "alex_pbe_native"]].notna().all(axis=1)
    pool_valid = x[["mp_common_pool", "alex_pbe_common_pool"]].notna().all(axis=1)
    x["native_switch"] = x["mp_native"].ne(x["alex_pbe_native"]) & native_valid
    x["common_pool_switch"] = x["mp_common_pool"].ne(x["alex_pbe_common_pool"]) & pool_valid
    x["phase_pool_sensitive"] = x["native_switch"] & pool_valid & ~x["common_pool_switch"]
    x["persistent"] = x["native_switch"] & x["common_pool_switch"]
    x["hidden_common_pool"] = native_valid & ~x["native_switch"] & x["common_pool_switch"]
    x["source_consistent"] = native_valid & pool_valid & ~x["native_switch"] & ~x["common_pool_switch"] & x["mp_native"].eq(x["mp_common_pool"]) & x["mp_native"].eq(x["alex_pbe_common_pool"])
    x["source_consistent_state"] = np.where(
        x["source_consistent"] & x["mp_native"].fillna(False).astype(bool),
        "stable", np.where(x["source_consistent"], "unstable", ""),
    )
    return x.reset_index()


def _sample_balanced(x: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    definitions = {
        "phase_pool_sensitive": x["phase_pool_sensitive"],
        "persistent": x["persistent"],
        "hidden_common_pool": x["hidden_common_pool"],
        "source_consistent": x["source_consistent"],
    }
    selected: list[pd.DataFrame] = []
    used: set[str] = set()
    for stratum, mask in definitions.items():
        candidates = x.loc[mask & ~x["row_id"].isin(used)].copy()
        if len(candidates) < TARGET_PER_STRATUM:
            raise RuntimeError(f"{stratum} has {len(candidates)} eligible rows; requires {TARGET_PER_STRATUM}")
        # Equal stable/unstable representation only applies to the consistent stratum.
        if stratum == "source_consistent":
            halves = []
            for state in ("stable", "unstable"):
                group = candidates.loc[candidates["source_consistent_state"].eq(state)]
                if len(group) < TARGET_PER_STRATUM // 2:
                    raise RuntimeError(f"source_consistent {state} has {len(group)} eligible rows")
                halves.append(group.iloc[rng.permutation(len(group))[: TARGET_PER_STRATUM // 2]])
            take = pd.concat(halves, ignore_index=True)
        else:
            take = candidates.iloc[rng.permutation(len(candidates))[:TARGET_PER_STRATUM]].copy()
        take["referee_stratum"] = stratum
        used.update(take["row_id"].astype(str))
        selected.append(take)
    out = pd.concat(selected, ignore_index=True)
    out = out.sort_values(["referee_stratum", "chemical_system", "row_id"], kind="mergesort").reset_index(drop=True)
    out.insert(0, "referee_subset_id", [f"USR1200-{i:05d}" for i in range(1, len(out) + 1)])
    return out


def _load_structures(cache: Path, ids: set[str]) -> dict[str, Structure]:
    if not cache.exists():
        return {}
    structures: dict[str, Structure] = {}
    with cache.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            mp_id = str(row.get("material_id", ""))
            if mp_id not in ids or not row.get("structure"):
                continue
            try:
                structures[mp_id] = Structure.from_dict(row["structure"])
            except Exception:
                continue
    return structures


def _write_structure_exports(selected: pd.DataFrame, cache: Path, out: Path) -> pd.DataFrame:
    structure_dir = out / "target_poscars"
    structure_dir.mkdir(parents=True, exist_ok=True)
    structures = _load_structures(cache, set(selected["mp_id"].astype(str)))
    rows = []
    for row in selected.itertuples(index=False):
        structure = structures.get(str(row.mp_id))
        path = structure_dir / f"{row.referee_subset_id}.vasp"
        if structure is None:
            rows.append({"referee_subset_id": row.referee_subset_id, "mp_id": row.mp_id, "coordinate_status": "missing_from_cache", "poscar_path": "", "sha256": ""})
            continue
        structure.to(filename=str(path), fmt="poscar")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append({"referee_subset_id": row.referee_subset_id, "mp_id": row.mp_id, "coordinate_status": "exported_from_mp_cache", "poscar_path": str(path.relative_to(out)), "sha256": digest})
    return pd.DataFrame(rows)


def _subsystems(chemical_system: str) -> list[str]:
    elements = sorted(str(chemical_system).split("-"))
    return ["-".join(combo) for r in range(1, len(elements) + 1) for combo in combinations(elements, r)]


def _phase_pool_requests(selected: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for system, group in selected.groupby("chemical_system", sort=True):
        rows.append({
            "chemical_system": system,
            "selected_target_n": int(len(group)),
            "required_subsystems": ";".join(_subsystems(system)),
            "required_subsystem_n": len(_subsystems(system)),
            "mp_query": f"chemsys={system}; include all subsystem phases",
            "alexandria_pbe_query": f"chemsys={system}; include all subsystem phases",
            "phase_pool_status": "awaiting_complete_source_phase_records",
        })
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    classified = _classify()
    selected = _sample_balanced(classified, args.seed)
    coordinates = _write_structure_exports(selected, args.structure_cache, args.out)
    selected = selected.merge(coordinates, on=["referee_subset_id", "mp_id"], how="left", validate="one_to_one")
    selected.to_parquet(args.out / "unified_referee_subset_1200.parquet", index=False)
    selected.to_csv(args.out / "unified_referee_subset_1200.csv", index=False)
    selected.groupby("referee_stratum", sort=True).agg(
        target_n=("row_id", "size"), chemical_system_n=("chemical_system", "nunique"),
        coordinate_export_n=("coordinate_status", lambda s: int(s.eq("exported_from_mp_cache").sum())),
    ).reset_index().to_csv(args.out / "unified_referee_subset_1200_strata.csv", index=False)
    _phase_pool_requests(selected).to_csv(args.out / "unified_referee_phase_pool_requests.csv", index=False)
    metadata = {
        "seed": args.seed,
        "target_n": int(len(selected)),
        "target_per_stratum": TARGET_PER_STRATUM,
        "strata": ["phase_pool_sensitive", "persistent", "hidden_common_pool", "source_consistent"],
        "structure_cache": str(args.structure_cache),
        "coordinate_export_n": int(selected["coordinate_status"].eq("exported_from_mp_cache").sum()),
        "numerical_tolerance_eV_per_atom": NUMERICAL_TOLERANCE,
    }
    (args.out / "unified_referee_subset_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"wrote {len(selected)} selected referee structures to {args.out}")


if __name__ == "__main__":
    main()
