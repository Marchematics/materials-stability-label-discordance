#!/usr/bin/env python3
"""Clean MatterGen structures and assign exact SourceAware matches where present."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from ase.io import read as ase_read
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.core import Structure
from pymatgen.io.ase import AseAtomsAdaptor


ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "outputs" / "phase1_v2"
MP_CACHE = Path("/home/waas/paper_experiments/github/discordance-/outputs/milestones/materials_label_discordance_full_mp_alex_43984/mp_records_summary_structures.jsonl")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--extxyz", type=Path, required=True)
    p.add_argument("--out", type=Path, default=ROOT / "outputs" / "evidence_strengthening_v1" / "generated_candidate_cohort")
    return p.parse_args()


def sourceaware_labels() -> pd.DataFrame:
    labels = pd.read_parquet(PHASE1 / "labels_by_view.parquet")
    wanted = ("mp_native", "alexmp20_native", "alex_pbe_native", "common_pool", "audit_view", "consensus")
    blocks = []
    for view in wanted:
        x = labels.loc[labels.label_view.eq(view), ["row_id", "label", "is_evaluable"]].drop_duplicates("row_id")
        blocks.append(x.rename(columns={"label": f"{view}_label", "is_evaluable": f"{view}_evaluable"}).set_index("row_id"))
    d2 = pd.read_parquet(PHASE1 / "denominator_d2_triple_single_match.parquet", columns=["row_id", "mp_id", "reduced_formula"])
    return d2.set_index("row_id").join(pd.concat(blocks, axis=1)).reset_index()


def mp_structures(ids: set[str]) -> dict[str, Structure]:
    found = {}
    with MP_CACHE.open() as handle:
        for line in handle:
            d = json.loads(line)
            if d.get("material_id") in ids:
                found[d["material_id"]] = Structure.from_dict(d["structure"])
            if len(found) == len(ids):
                break
    return found


def main() -> None:
    args = parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    source = sourceaware_labels()
    by_formula = defaultdict(list)
    for row in source.itertuples(index=False): by_formula[row.reduced_formula].append(row)
    refs = mp_structures(set(source.mp_id.astype(str)))
    matcher = StructureMatcher(ltol=0.2, stol=0.3, angle_tol=5.0, primitive_cell=True, scale=True)
    candidates, accepted_by_formula = [], defaultdict(list)
    for index, atoms in enumerate(ase_read(str(args.extxyz), index=":")):
        identifier = f"MGEN-{index:06d}"
        try:
            structure = AseAtomsAdaptor.get_structure(atoms)
            volume_per_atom = structure.volume / len(structure)
            valid = np.isfinite(volume_per_atom) and 2.0 <= volume_per_atom <= 100.0 and 1 <= len(structure) <= 100
        except Exception:
            structure, volume_per_atom, valid = None, np.nan, False
        formula = structure.composition.reduced_formula if structure is not None else ""
        duplicate_id = ""
        if valid:
            for prior_id, prior in accepted_by_formula[formula]:
                if matcher.fit(structure, prior):
                    duplicate_id = prior_id; break
        state = "accepted" if valid and not duplicate_id else ("duplicate" if duplicate_id else "invalid_structure")
        match_row = None
        if state == "accepted":
            for ref in by_formula.get(formula, []):
                reference = refs.get(str(ref.mp_id))
                if reference is not None and matcher.fit(structure, reference):
                    match_row = ref; break
            accepted_by_formula[formula].append((identifier, structure))
            structure.to(filename=str(args.out / "structures" / f"{identifier}.cif"), fmt="cif") if (args.out / "structures").mkdir(exist_ok=True) is None else None
        row = {"candidate_id": identifier, "reduced_formula": formula, "site_n": len(structure) if structure is not None else pd.NA,
               "volume_per_atom_ang3": volume_per_atom, "cleaning_status": state, "duplicate_of_candidate_id": duplicate_id,
               "match_tier": "exact_structure" if match_row is not None else ("formula_only_or_unmatched" if state == "accepted" else "not_evaluable"),
               "sourceaware_row_id": getattr(match_row, "row_id", pd.NA), "matched_mp_id": getattr(match_row, "mp_id", pd.NA)}
        if match_row is not None:
            for view in ("mp_native", "alexmp20_native", "alex_pbe_native", "common_pool", "audit_view", "consensus"):
                row[f"{view}_label"] = getattr(match_row, f"{view}_label")
                row[f"{view}_evaluable"] = getattr(match_row, f"{view}_evaluable")
        candidates.append(row)
    table = pd.DataFrame(candidates)
    table.to_parquet(args.out / "generated_candidates_clean_and_matched.parquet", index=False)
    table.to_csv(args.out / "generated_candidates_clean_and_matched.csv", index=False)
    summary = pd.DataFrame([{"input_structure_n": len(table), "accepted_n": int(table.cleaning_status.eq("accepted").sum()),
                             "duplicate_n": int(table.cleaning_status.eq("duplicate").sum()), "invalid_n": int(table.cleaning_status.eq("invalid_structure").sum()),
                             "exact_sourceaware_match_n": int(table.match_tier.eq("exact_structure").sum()),
                             "formula_only_or_unmatched_n": int(table.match_tier.eq("formula_only_or_unmatched").sum())}])
    summary.to_csv(args.out / "generated_candidate_cohort_summary.csv", index=False)
    (args.out / "generated_candidate_processing_metadata.json").write_text(json.dumps({"input": str(args.extxyz), "structure_matcher": {"ltol": .2, "stol": .3, "angle_tol": 5.0}, "source_label_assignment": "exact_structure matches only"}, indent=2) + "\n")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
