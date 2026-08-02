#!/usr/bin/env python3
"""Rebuild source-specific complete-pool hull distances for referee targets."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import pandas as pd
from pymatgen.analysis.phase_diagram import PDEntry, PhaseDiagram
from pymatgen.core import Composition


ROOT = Path(__file__).resolve().parents[1]
REFEREE = ROOT / "outputs" / "evidence_strengthening_v1" / "unified_referee_subset_1200" / "unified_referee_subset_1200.parquet"
POOL = ROOT / "outputs" / "evidence_strengthening_v1" / "full_phase_pool_referee_1200"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=POOL)
    return p.parse_args()


def load_entries(path: Path, source: str) -> tuple[dict[str, tuple[PDEntry, set[str]]], dict[str, PDEntry]]:
    by_system: dict[str, list[tuple[PDEntry, set[str]]]] = defaultdict(list)
    by_id: dict[str, PDEntry] = {}
    seen_ids: set[str] = set()
    with path.open() as handle:
        for line in handle:
            d = json.loads(line)
            formula = d.get("formula")
            energy = d.get("formation_energy_per_atom")
            identifier = str(d.get("mp_id") if source == "mp" else d.get("alexandria_id"))
            if not formula or energy is None or identifier == "None":
                continue
            if identifier in seen_ids:
                continue
            try:
                comp = Composition(formula)
                entry = PDEntry(comp, float(energy) * comp.num_atoms, name=identifier)
                elements = {str(e) for e in comp.elements}
            except Exception:
                continue
            by_system["-".join(sorted(elements))].append((entry, elements))
            by_id[identifier] = entry
            seen_ids.add(identifier)
    return by_system, by_id


def source_hulls(targets: pd.DataFrame, by_system: dict, by_id: dict, source: str) -> pd.DataFrame:
    rows = []
    id_col = "mp_id" if source == "mp" else "official_alexandria_id"
    for target in targets.itertuples(index=False):
        elements = set(str(target.chemical_system).split("-"))
        subsystem_keys = ["-".join(c) for r in range(1, len(elements) + 1) for c in combinations(sorted(elements), r)]
        phases = [entry for key in subsystem_keys for entry, _ in by_system.get(key, [])]
        target_entry = by_id.get(str(getattr(target, id_col)))
        state, e_hull, reason = "available", None, ""
        if target_entry is None:
            state, reason = "target_absent_from_source_pool", "source identifier absent"
        elif not phases:
            state, reason = "phase_pool_empty", "no source phases"
        else:
            try:
                pdgm = PhaseDiagram(phases)
                e_hull = float(pdgm.get_e_above_hull(target_entry))
            except Exception as exc:
                state, reason = "hull_reconstruction_error", type(exc).__name__
        rows.append({"referee_subset_id": target.referee_subset_id, "row_id": target.row_id, "source": source,
                     "phase_pool_n": len(phases), "pool_status": state, "failure_reason": reason,
                     "full_pool_e_above_hull_eV_per_atom": e_hull,
                     "full_pool_stable": (e_hull <= 1e-8) if e_hull is not None else pd.NA})
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    mp_path = args.out / "mp_relevant_phase_entries.jsonl"
    alex_path = args.out / "alexandria_pbe_2025_07_02_relevant_phase_entries.jsonl"
    if not mp_path.exists() or not alex_path.exists():
        raise FileNotFoundError("MP and Alexandria extracted phase-entry JSONL files are required")
    targets = pd.read_parquet(REFEREE)
    mp_by_system, mp_ids = load_entries(mp_path, "mp")
    ax_by_system, ax_ids = load_entries(alex_path, "alex")
    result = pd.concat([source_hulls(targets, mp_by_system, mp_ids, "mp"), source_hulls(targets, ax_by_system, ax_ids, "alexandria_pbe")], ignore_index=True)
    result.to_parquet(args.out / "referee_full_phase_pool_hull_labels.parquet", index=False)
    result.to_csv(args.out / "referee_full_phase_pool_hull_labels.csv", index=False)
    summary = result.groupby(["source", "pool_status"], dropna=False).agg(row_n=("row_id", "size"), median_phase_pool_n=("phase_pool_n", "median")).reset_index()
    summary.to_csv(args.out / "referee_full_phase_pool_hull_summary.csv", index=False)
    print(f"wrote {len(result)} source-specific full-pool hull rows to {args.out}")


if __name__ == "__main__":
    main()
