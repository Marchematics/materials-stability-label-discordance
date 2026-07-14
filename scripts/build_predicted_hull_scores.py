#!/usr/bin/env python3
"""Construct model rankings from predicted formation energies and D2 subsystem hulls.

The earlier Phase 2 score panel stored negative raw energies per atom.  Raw
energies are not composition-comparable stability ranks.  This script derives
per-model formation energies using predicted elemental references and then
computes energy above a predicted convex hull over the fixed D2 subsystem
phase pool.  It writes one explicit, auditable ranking per model.

The resulting quantity is a D2-subsystem predicted-hull ranking with a fixed
phase pool across label views.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import hashlib
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from mp_api.client import MPRester
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.core import Composition, Structure
from pymatgen.entries.computed_entries import ComputedEntry

ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "outputs" / "phase1_v2"
RAW_SCORES = ROOT / "inputs" / "phase2_v1" / "sourceaware_model_scores_public_safe.parquet"
STRUCTURE_CACHE = Path(
    "/home/waas/paper_experiments/github/discordance-/outputs/milestones/"
    "materials_label_discordance_full_mp_alex_43984/mp_records_summary_structures.jsonl"
)
OUT = ROOT / "outputs" / "repaired_model_evaluation_v1"
MODELS = ("ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=[*MODELS, "all"], default="all")
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--structure-cache", type=Path, default=STRUCTURE_CACHE)
    p.add_argument("--force-references", action="store_true")
    return p.parse_args()


def load_base() -> pd.DataFrame:
    labels = pd.read_parquet(PHASE1 / "labels_by_view.parquet")
    base = labels[labels["label_view"].eq("mp_native")][
        ["row_id", "mp_id", "formula", "chemical_system", "label"]
    ].drop_duplicates("row_id")
    base["elements"] = base["chemical_system"].str.split("-").map(lambda x: tuple(sorted(x)))
    return base


def load_raw(model: str, base: pd.DataFrame) -> pd.DataFrame:
    raw = pd.read_parquet(RAW_SCORES)
    raw = raw[raw["model"].eq(model)][["row_id", "score"]].copy()
    raw["score"] = pd.to_numeric(raw["score"], errors="coerce")
    raw = raw.dropna().drop_duplicates("row_id")
    frame = base.merge(raw, on="row_id", how="inner")
    # Original stored score = - predicted raw energy per atom.
    frame["predicted_raw_energy_per_atom"] = -frame["score"].astype(float)
    return frame


def reference_candidates(frame: pd.DataFrame) -> dict[str, float]:
    """Use the lowest predicted energy among elemental entries in the fixed D2 pool."""
    pure = frame[frame["elements"].map(len).eq(1)].copy()
    choices = pure.copy()
    choices["element"] = choices["elements"].map(lambda x: x[0])
    return choices.groupby("element")["predicted_raw_energy_per_atom"].min().to_dict()


def fetch_missing_element_structures(missing: set[str], path: Path) -> dict[str, dict]:
    """Fetch one MP-stable elemental structure for each missing element."""
    saved: dict[str, dict] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                saved[row["element"]] = row
    todo = sorted(set(missing) - set(saved))
    if todo:
        api_key = os.environ.get("MP_API_KEY")
        if not api_key:
            raise RuntimeError("MP_API_KEY is required to retrieve missing elemental references")
        with MPRester(api_key) as mpr:
            for element in todo:
                docs = mpr.materials.summary.search(
                    chemsys=element,
                    fields=["material_id", "formula_pretty", "energy_above_hull", "is_stable", "structure"],
                )
                stable = [d for d in docs if bool(d.is_stable) or float(d.energy_above_hull or np.inf) <= 1e-8]
                if not stable:
                    raise RuntimeError(f"No MP-stable elemental structure returned for {element}")
                doc = sorted(stable, key=lambda d: (float(d.energy_above_hull or 0.0), str(d.material_id)))[0]
                saved[element] = {
                    "element": element,
                    "mp_id": str(doc.material_id),
                    "formula": str(doc.formula_pretty),
                    "energy_above_hull": float(doc.energy_above_hull or 0.0),
                    "structure": doc.structure.as_dict(),
                    "query_date": str(date.today()),
                }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(saved[e], sort_keys=True) + "\n" for e in sorted(saved)), encoding="utf-8")
    return saved


def energy_predictor(model: str):
    """Return a function yielding the stored convention: negative eV per atom."""
    if model == "CHGNet":
        from chgnet.model.model import CHGNet

        calculator = CHGNet.load()

        def predict(structure: Structure) -> float:
            return -float(np.asarray(calculator.predict_structure(structure)["e"]))

        return predict
    if model == "MACE-MP":
        from mace.calculators import mace_mp
        from pymatgen.io.ase import AseAtomsAdaptor

        calculator = mace_mp(model="small", device="cuda")

        def predict(structure: Structure) -> float:
            atoms = AseAtomsAdaptor.get_atoms(structure)
            atoms.calc = calculator
            return -float(atoms.get_potential_energy() / len(atoms))

        return predict
    if model == "M3GNet":
        import matgl
        from matgl.ext.ase import PESCalculator
        from pymatgen.io.ase import AseAtomsAdaptor

        potential = matgl.load_model("M3GNet-PES-MatPES-PBE-2025.2")
        calculator = PESCalculator(potential)

        def predict(structure: Structure) -> float:
            atoms = AseAtomsAdaptor.get_atoms(structure)
            atoms.calc = calculator
            return -float(atoms.get_potential_energy() / len(atoms))

        return predict
    if model == "ALIGNN-FF":
        from alignn.ff.calculators import AlignnAtomwiseCalculator
        from pymatgen.io.ase import AseAtomsAdaptor

        calculator = AlignnAtomwiseCalculator(
            path="/root/alignn_ff_models/v12.2.2024_dft_3d_307k", device="cuda"
        )

        def predict(structure: Structure) -> float:
            atoms = AseAtomsAdaptor.get_atoms(structure)
            atoms.calc = calculator
            return -float(atoms.get_potential_energy() / len(atoms))

        return predict
    raise ValueError(model)


def elemental_references(model: str, frame: pd.DataFrame, out: Path, force: bool) -> dict[str, float]:
    out.mkdir(parents=True, exist_ok=True)
    cache = out / "elemental_reference_structures.jsonl"
    candidate = reference_candidates(frame)
    all_elements = set(e for els in frame["elements"] for e in els)
    missing = all_elements - set(candidate)
    fetched = fetch_missing_element_structures(missing, cache)
    scores_path = out / f"elemental_reference_scores_{model}.csv"
    if scores_path.exists() and not force:
        scored = pd.read_csv(scores_path)
    else:
        predictor = energy_predictor(model)
        rows = []
        for element in sorted(missing):
            rec = fetched[element]
            score = predictor(Structure.from_dict(rec["structure"]))
            rows.append(
                {
                    "element": element,
                    "mp_id": rec["mp_id"],
                    "reference_source": "MP_stable_elemental_structure_retrieved_for_missing_D2_reference",
                    "predicted_raw_energy_per_atom": -score,
                    "stored_score_convention": score,
                }
            )
        scored = pd.DataFrame(rows)
        scored.to_csv(scores_path, index=False)
    if len(scored):
        candidate.update(scored.set_index("element")["predicted_raw_energy_per_atom"].astype(float).to_dict())
    unresolved = all_elements - set(candidate)
    if unresolved:
        raise RuntimeError(f"Missing elemental references for {sorted(unresolved)}")
    # Record all selected references, including D2-derived ones.
    d2_rows = [
        {
            "element": e,
            "predicted_raw_energy_per_atom": energy,
            "reference_source": "minimum_predicted_energy_among_D2_elemental_entries",
        }
        for e, energy in sorted(reference_candidates(frame).items())
    ]
    d2_rows.extend(scored.to_dict("records"))
    pd.DataFrame(d2_rows).to_csv(out / f"elemental_reference_summary_{model}.csv", index=False)
    return candidate


def formation_energies(frame: pd.DataFrame, refs: dict[str, float]) -> pd.DataFrame:
    out = frame.copy()

    def formation(row: pd.Series) -> float:
        comp = Composition(row["formula"])
        return float(
            row["predicted_raw_energy_per_atom"]
            - sum(comp.get_atomic_fraction(el) * refs[el.symbol] for el in comp.elements)
        )

    out["predicted_formation_energy_per_atom"] = out.apply(formation, axis=1)
    return out


def subsystem_pool_indices(frame: pd.DataFrame) -> dict[tuple[str, ...], np.ndarray]:
    groups: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for idx, els in enumerate(frame["elements"]):
        groups[tuple(els)].append(idx)
    return {k: np.asarray(v, dtype=int) for k, v in groups.items()}


def predicted_hulls(frame: pd.DataFrame) -> pd.DataFrame:
    """Evaluate every D2 entry against a model-predicted D2 subsystem hull."""
    entries = frame.reset_index(drop=True).copy()
    entries["composition"] = entries["formula"].map(Composition)
    groups = subsystem_pool_indices(entries)
    by_system = entries.groupby("chemical_system", sort=True).indices
    predicted = np.full(len(entries), np.nan, dtype=float)
    phase_count = np.zeros(len(entries), dtype=int)
    status = np.full(len(entries), "not_started", dtype=object)
    for done, (system, targets) in enumerate(sorted(by_system.items()), start=1):
        system_elements = tuple(sorted(system.split("-")))
        pool_idx = []
        for n in range(1, len(system_elements) + 1):
            for subset in itertools.combinations(system_elements, n):
                if subset in groups:
                    pool_idx.extend(groups[subset].tolist())
        pool_idx = np.asarray(sorted(set(pool_idx)), dtype=int)
        phase_count[targets] = len(pool_idx)
        try:
            pool_entries = [
                ComputedEntry(
                    entries.at[i, "composition"],
                    float(entries.at[i, "predicted_formation_energy_per_atom"] * entries.at[i, "composition"].num_atoms),
                )
                for i in pool_idx
            ]
            # Elemental references define zero formation energy for every
            # component.  Some elements have no pure-entry structure in D2;
            # their retrieved model reference is therefore represented here as
            # a zero-formation endpoint rather than omitted from the hull.
            pool_entries.extend(ComputedEntry(Composition(element), 0.0) for element in system_elements)
            hull = PhaseDiagram(pool_entries)
            for i in targets:
                entry = ComputedEntry(
                    entries.at[i, "composition"],
                    float(entries.at[i, "predicted_formation_energy_per_atom"] * entries.at[i, "composition"].num_atoms),
                )
                predicted[i] = float(hull.get_e_above_hull(entry))
                status[i] = "ok"
        except Exception as exc:  # Keep failure status explicit and row-level.
            status[targets] = f"failed_{type(exc).__name__}"
        if done % 1000 == 0 or done == len(by_system):
            print(f"{done}/{len(by_system)} chemical systems", flush=True)
    out = entries.drop(columns=["composition"])
    out["predicted_e_above_hull_d2_subsystem"] = predicted
    out["phase_pool_n"] = phase_count
    out["hull_status"] = status
    out["score_for_stability_ranking"] = -out["predicted_e_above_hull_d2_subsystem"]
    out["score_semantics"] = "negative_predicted_eabove_hull_d2_subsystem_higher_is_more_stable"
    return out


def write_phase_pool_manifest(base: pd.DataFrame, out: Path) -> None:
    """Record the fixed D2 subsystem pool used by every model ranking."""
    system_sizes = base["elements"].map(len)
    payload = {
        "name": "fixed_D2_subsystem_phase_pool",
        "version": "M1_repaired_model_evaluation_v1",
        "construction": {
            "target_rows": int(len(base)),
            "target_chemical_systems": int(base["chemical_system"].nunique()),
            "target_element_count_distribution": {
                str(int(k)): int(v) for k, v in system_sizes.value_counts().sort_index().items()
            },
            "rule": (
                "For each target chemical system, include all D2 entries whose element set is a "
                "non-empty subset of that system, then add one zero-formation-energy elemental "
                "endpoint for each constituent element."
            ),
            "formation_energy": "model-specific predicted formation energy per atom",
            "ranking_score": "negative predicted energy above hull",
        },
        "source_inputs": [
            {
                "path": str((PHASE1 / "labels_by_view.parquet").relative_to(ROOT)),
                "sha256": sha256(PHASE1 / "labels_by_view.parquet"),
                "selection": "mp_native rows provide D2 row identifiers, formulae and chemical systems",
            },
            {
                "path": str(RAW_SCORES.relative_to(ROOT)),
                "sha256": sha256(RAW_SCORES),
                "selection": "four archived model energy tables",
            },
        ],
        "elemental_reference_records": "elemental_reference_structures.jsonl and elemental_reference_summary_<model>.csv",
    }
    (out / "fixed_subsystem_phase_pool_manifest.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    args = parse_args()
    models = MODELS if args.model == "all" else (args.model,)
    args.out.mkdir(parents=True, exist_ok=True)
    base = load_base()
    write_phase_pool_manifest(base, args.out)
    for model in models:
        print(f"Building predicted-hull scores for {model}", flush=True)
        frame = load_raw(model, base)
        refs = elemental_references(model, frame, args.out, args.force_references)
        formed = formation_energies(frame, refs)
        result = predicted_hulls(formed)
        result.to_parquet(args.out / f"predicted_hull_scores_{model}.parquet", index=False)
        summary = {
            "model": model,
            "rows_input": int(len(frame)),
            "rows_hull_ok": int(result["hull_status"].eq("ok").sum()),
            "rows_hull_failed": int((~result["hull_status"].eq("ok")).sum()),
            "phase_pool": "fixed D2 subsystem pool",
            "score_semantics": "negative predicted e_above_hull over fixed D2 subsystem phase pool",
            "ranking_construction": "model-specific predicted formation energies evaluated on the fixed D2 subsystem phase pool",
        }
        (args.out / f"predicted_hull_scores_{model}.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
