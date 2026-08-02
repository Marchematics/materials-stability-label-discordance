#!/usr/bin/env python3
"""Build batch-relative signed reference-hull rankings for one declared model.

The estimand is fixed before evaluation:

* candidate universe: the frozen D5 four-model score intersection;
* reference phase pool: the same frozen D5 batch plus zero-formation elemental
  anchors for each target chemical system;
* target exclusion: every member of the target's precomputed tolerance-based
  structural-equivalence class is removed before its reference hull is built;
* score: negative signed reference-hull margin, so larger is ranked earlier.

Other candidates remain eligible as competing phases. The resulting score is
therefore batch-relative and transductive. It is not a frozen-known-reference
discovery score and is never described as conventional energy above hull.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.core import Composition, Structure
from pymatgen.entries.computed_entries import ComputedEntry

from sourceaware.ranking import analytic_tie_aware_topk, score_tie_audit


ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "outputs" / "phase1_v2"
SCORE_DIR = ROOT / "outputs" / "repaired_model_evaluation_v1"
DEFAULT_STRUCTURE_CACHE = Path(
    "/home/waas/paper_experiments/github/discordance-/outputs/milestones/"
    "materials_label_discordance_full_mp_alex_43984/mp_records_summary_structures.jsonl"
)
DEFAULT_OUT = ROOT / "outputs" / "referee_revision_v3"
REFERENCE_POOL_VERSION = "D5-batch-relative-reference-pool-v1"
CANDIDATE_POOL_VERSION = "D5-batch-candidate-pool-v1"
EQUIVALENCE_VERSION = "D5-StructureMatcher-ltol0.2-stol0.3-angle5-v1"
K_VALUES = (100, 300, 500, 1000, 5000)
PHYSICAL_ENDPOINTS = (
    "mp_native",
    "alexmp20_native",
    "alex_pbe_native",
    "mp_common_pool",
    "alex_pbe_common_pool",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="MACE-MP")
    parser.add_argument("--score-dir", type=Path, default=SCORE_DIR)
    parser.add_argument("--structure-cache", type=Path, default=DEFAULT_STRUCTURE_CACHE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--equivalence-only", action="store_true")
    parser.add_argument("--force-equivalence", action="store_true")
    parser.add_argument("--skip-pool-manifests", action="store_true")
    parser.add_argument("--max-systems", type=int)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class UnionFind:
    def __init__(self, values: list[str]):
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        root = value
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[value] != value:
            parent = self.parent[value]
            self.parent[value] = root
            value = parent
        return root

    def union(self, left: str, right: str) -> None:
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parent[max(a, b)] = min(a, b)


def load_d5() -> pd.DataFrame:
    path = PHASE1 / "denominator_d5_model_complete.parquet"
    frame = pd.read_parquet(path).copy()
    frame["elements"] = frame["formula"].map(
        lambda formula: tuple(sorted(element.symbol for element in Composition(formula).elements))
    )
    frame["element_count"] = frame["elements"].map(len)
    if frame["row_id"].duplicated().any():
        raise RuntimeError("D5 row identifiers are not unique")
    return frame.sort_values("row_id").reset_index(drop=True)


def load_structure_dicts(d5: pd.DataFrame, cache: Path) -> dict[str, dict]:
    required = set(d5["mp_id"].astype(str))
    structures: dict[str, dict] = {}
    with cache.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            material_id = str(record["material_id"])
            if material_id in required:
                structures[material_id] = record["structure"]
    missing = sorted(required - set(structures))
    if missing:
        raise RuntimeError(f"Structure cache lacks {len(missing)} D5 MP structures: {missing[:10]}")
    return structures


def build_equivalence_classes(
    d5: pd.DataFrame,
    structure_dicts: dict[str, dict],
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Build connected components of all predeclared duplicate relations."""
    matcher = StructureMatcher(
        ltol=0.2,
        stol=0.3,
        angle_tol=5.0,
        primitive_cell=True,
        scale=True,
        attempt_supercell=True,
        allow_subset=False,
    )
    union = UnionFind(d5["row_id"].astype(str).tolist())
    edge_rows: list[dict] = []

    def add_relation(left: str, right: str, relation: str) -> None:
        union.union(left, right)
        edge_rows.append({"row_id_a": left, "row_id_b": right, "relation": relation})

    for column, relation in [
        ("structure_hash", "same_canonical_hash"),
        ("mp_id", "same_mp_identifier"),
        ("mattergen_id", "same_mattergen_identifier"),
        ("official_alexandria_id", "same_alexandria_identifier"),
    ]:
        usable = d5[column].notna() & d5[column].astype(str).str.strip().ne("")
        for _, group in d5.loc[usable].groupby(column, sort=False):
            ids = sorted(group["row_id"].astype(str))
            for left, right in zip(ids, ids[1:]):
                add_relation(left, right, relation)

    failed_pairs = 0
    pair_n = 0
    for _, group in d5.groupby("reduced_formula", sort=True):
        records = group[["row_id", "mp_id"]].sort_values("row_id").to_dict("records")
        if len(records) < 2:
            continue
        structures = {
            record["row_id"]: Structure.from_dict(structure_dicts[str(record["mp_id"])])
            for record in records
        }
        for left, right in itertools.combinations(records, 2):
            pair_n += 1
            try:
                if matcher.fit(structures[left["row_id"]], structures[right["row_id"]]):
                    add_relation(left["row_id"], right["row_id"], "structure_matcher_equivalent")
            except Exception:
                failed_pairs += 1

    components: dict[str, list[str]] = defaultdict(list)
    for row_id in d5["row_id"].astype(str):
        components[union.find(row_id)].append(row_id)
    ordered = sorted((sorted(members) for members in components.values()), key=lambda x: x[0])
    class_by_row = {
        row_id: f"TEQ-{index:06d}"
        for index, members in enumerate(ordered, start=1)
        for row_id in members
    }
    classes = d5.copy()
    classes["equivalence_class_id"] = classes["row_id"].map(class_by_row)
    sizes = classes.groupby("equivalence_class_id")["row_id"].transform("size")
    classes["equivalence_class_size"] = sizes.astype(int)
    classes["equivalence_version"] = EQUIVALENCE_VERSION
    classes["matcher_ltol"] = 0.2
    classes["matcher_stol"] = 0.3
    classes["matcher_angle_tol"] = 5.0
    classes["matcher_primitive_cell"] = True
    classes["matcher_scale"] = True
    classes["matcher_attempt_supercell"] = True
    classes["matcher_allow_subset"] = False
    edges = pd.DataFrame(edge_rows).drop_duplicates().sort_values(
        ["row_id_a", "row_id_b", "relation"]
    ) if edge_rows else pd.DataFrame(columns=["row_id_a", "row_id_b", "relation"])
    metadata = {
        "equivalence_version": EQUIVALENCE_VERSION,
        "row_n": int(len(classes)),
        "equivalence_class_n": int(classes["equivalence_class_id"].nunique()),
        "non_singleton_class_n": int(
            (classes.groupby("equivalence_class_id").size() > 1).sum()
        ),
        "largest_class_n": int(classes["equivalence_class_size"].max()),
        "candidate_pair_comparisons": int(pair_n),
        "failed_pair_comparisons": int(failed_pairs),
        "recorded_relation_edges": int(len(edges)),
        "component_rule": "connected components over identifier, canonical-hash, and StructureMatcher relations",
    }
    return classes, edges, metadata


def load_or_build_equivalence(
    d5: pd.DataFrame,
    structure_cache: Path,
    out: Path,
    force: bool,
) -> pd.DataFrame:
    class_path = out / "structural_equivalence_classes.parquet"
    if class_path.exists() and not force:
        classes = pd.read_parquet(class_path)
        if set(classes["row_id"]) != set(d5["row_id"]):
            raise RuntimeError("Cached structural equivalence classes do not match frozen D5")
        return classes
    structures = load_structure_dicts(d5, structure_cache)
    classes, edges, metadata = build_equivalence_classes(d5, structures)
    classes.to_parquet(class_path, index=False)
    edges.to_parquet(out / "structural_equivalence_edges.parquet", index=False)
    (out / "structural_equivalence_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return classes


def file_slug(model: str) -> str:
    return model.lower().replace("-", "_")


def write_pool_manifests(classes: pd.DataFrame, out: Path) -> None:
    candidate = classes[
        [
            "row_id", "mp_id", "mattergen_id", "official_alexandria_id", "formula",
            "reduced_formula", "chemical_system", "structure_hash", "elements",
            "element_count", "equivalence_class_id", "equivalence_class_size",
        ]
    ].copy()
    candidate["candidate_pool_version"] = CANDIDATE_POOL_VERSION
    candidate["ranking_estimand"] = "batch_relative_transductive_signed_reference_hull_margin"
    candidate["all_four_archived_raw_scores_available"] = True
    candidate["ranking_eligible"] = candidate["element_count"].ge(2)
    candidate["ranking_ineligible_reason"] = np.where(
        candidate["element_count"].lt(2), "elemental_target_not_ranked", ""
    )
    candidate["elements_json"] = candidate["elements"].map(
        lambda values: json.dumps(list(values))
    )
    candidate.drop(columns="elements").to_parquet(out / "candidate_pool_manifest.parquet", index=False)

    reference = candidate.copy()
    reference["reference_pool_version"] = REFERENCE_POOL_VERSION
    reference["phase_id"] = reference["row_id"]
    reference["phase_kind"] = "D5_batch_phase"
    reference["reference_role"] = "eligible_competing_phase_when_score_available_and_not_excluded"
    elements = sorted({element for values in classes["elements"] for element in values})
    anchors = pd.DataFrame(
        {
            "row_id": [None] * len(elements),
            "formula": elements,
            "reduced_formula": elements,
            "chemical_system": elements,
            "structure_hash": [None] * len(elements),
            "element_count": [1] * len(elements),
            "equivalence_class_id": [None] * len(elements),
            "equivalence_class_size": [0] * len(elements),
            "candidate_pool_version": [CANDIDATE_POOL_VERSION] * len(elements),
            "ranking_estimand": ["batch_relative_transductive_signed_reference_hull_margin"] * len(elements),
            "all_four_archived_raw_scores_available": [True] * len(elements),
            "ranking_eligible": [False] * len(elements),
            "ranking_ineligible_reason": ["elemental_zero_formation_anchor"] * len(elements),
            "elements_json": [json.dumps([element]) for element in elements],
            "reference_pool_version": [REFERENCE_POOL_VERSION] * len(elements),
            "phase_id": [f"element_anchor::{element}" for element in elements],
            "phase_kind": ["elemental_zero_formation_anchor"] * len(elements),
            "reference_role": ["fixed_zero_formation_endpoint"] * len(elements),
        }
    )
    reference = pd.concat([reference, anchors.reindex(columns=reference.columns)], ignore_index=True)
    reference.to_parquet(out / "reference_phase_pool_manifest.parquet", index=False)


def load_model_energies(model: str, score_dir: Path, classes: pd.DataFrame) -> pd.DataFrame:
    path = score_dir / f"predicted_hull_scores_{model}.parquet"
    score = pd.read_parquet(path)[
        [
            "row_id", "predicted_raw_energy_per_atom",
            "predicted_formation_energy_per_atom",
        ]
    ].drop_duplicates("row_id")
    frame = classes.merge(score, on="row_id", how="left", validate="one_to_one")
    return frame


def subsystem_pool_indices(frame: pd.DataFrame) -> dict[tuple[str, ...], np.ndarray]:
    groups: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for index, elements in enumerate(frame["elements"]):
        groups[tuple(elements)].append(index)
    return {key: np.asarray(value, dtype=int) for key, value in groups.items()}


def phase_pool_for_system(
    system_elements: tuple[str, ...],
    groups: dict[tuple[str, ...], np.ndarray],
) -> np.ndarray:
    indices: list[int] = []
    for size in range(1, len(system_elements) + 1):
        for subset in itertools.combinations(system_elements, size):
            if subset in groups:
                indices.extend(groups[subset].tolist())
    return np.asarray(sorted(set(indices)), dtype=int)


def build_signed_margins(
    frame: pd.DataFrame,
    model: str,
    max_systems: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build class-excluded hulls; endpoint labels are never read here."""
    entries = frame.reset_index(drop=True).copy()
    equivalence_versions = entries["equivalence_version"].dropna().astype(str).unique()
    if len(equivalence_versions) != 1:
        raise RuntimeError("Ranking input must declare one structural-equivalence version")
    equivalence_version = str(equivalence_versions[0])
    entries["composition"] = entries["formula"].map(Composition)
    groups = subsystem_pool_indices(entries)
    systems = sorted(entries.loc[entries["element_count"].ge(2), "chemical_system"].unique())
    if max_systems is not None:
        systems = systems[: int(max_systems)]

    score_rows: list[dict] = []
    audit_rows: list[dict] = []
    for system_number, system in enumerate(systems, start=1):
        system_elements = tuple(sorted(system.split("-")))
        target_indices = entries.index[entries["chemical_system"].eq(system)].to_numpy(dtype=int)
        pool_indices = phase_pool_for_system(system_elements, groups)
        for class_id, class_targets in entries.loc[target_indices].groupby("equivalence_class_id", sort=True):
            target_idx = class_targets.index.to_numpy(dtype=int)
            expected_class_rows = sorted(
                entries.loc[entries["equivalence_class_id"].eq(class_id), "row_id"].astype(str)
            )
            excluded = entries.loc[pool_indices, "equivalence_class_id"].eq(class_id).to_numpy()
            retained_indices = pool_indices[~excluded]
            excluded_rows = sorted(entries.loc[pool_indices[excluded], "row_id"].astype(str))
            excluded_hashes = sorted(entries.loc[pool_indices[excluded], "structure_hash"].dropna().astype(str))
            pool_entries: list[ComputedEntry] = []
            for index in retained_indices:
                energy = entries.at[index, "predicted_formation_energy_per_atom"]
                if pd.isna(energy):
                    continue
                composition = entries.at[index, "composition"]
                pool_entries.append(
                    ComputedEntry(
                        composition,
                        float(energy * composition.num_atoms),
                        entry_id=str(entries.at[index, "row_id"]),
                    )
                )
            pool_entries.extend(
                ComputedEntry(Composition(element), 0.0, entry_id=f"element_anchor::{element}")
                for element in system_elements
            )
            try:
                hull = PhaseDiagram(pool_entries)
                hull_error = ""
            except Exception as exc:
                hull = None
                hull_error = f"{type(exc).__name__}: {exc}"

            for index in target_idx:
                row_id = str(entries.at[index, "row_id"])
                base_audit = {
                    "candidate_row_id": row_id,
                    "model_name": model,
                    "candidate_pool_version": CANDIDATE_POOL_VERSION,
                    "reference_pool_version": REFERENCE_POOL_VERSION,
                    "equivalence_version": equivalence_version,
                    "excluded_equivalence_class_id": str(class_id),
                    "expected_equivalence_class_row_ids_json": json.dumps(expected_class_rows),
                    "excluded_row_ids_json": json.dumps(excluded_rows),
                    "excluded_structure_hashes_json": json.dumps(excluded_hashes),
                    "excluded_phase_n": int(len(excluded_rows)),
                    "all_equivalence_class_members_excluded": bool(
                        excluded_rows == expected_class_rows
                    ),
                    "reference_hull_phase_n_before_exclusion": int(len(pool_indices) + len(system_elements)),
                    "reference_hull_phase_n_after_exclusion": int(len(pool_entries)),
                }
                if hull is None:
                    score_rows.append(
                        {
                            "row_id": row_id,
                            "model_name": model,
                            "signed_reference_hull_margin_eV_per_atom": np.nan,
                            "score_for_batch_relative_ranking": np.nan,
                            "score_status": "failed_reference_hull",
                            "incomplete_reason": hull_error,
                            "decomposition_simplex_json": "[]",
                        }
                    )
                    audit_rows.append(
                        {
                            **base_audit,
                            "decomposition_simplex_json": "[]",
                            "decomposition_simplex_phase_ids_json": "[]",
                            "excluded_rows_in_decomposition_simplex_json": "[]",
                            "decomposition_simplex_excludes_equivalence_class": False,
                            "score_status": "failed_reference_hull",
                            "exclusion_verified": False,
                            "audit_reason": hull_error,
                        }
                    )
                    continue
                composition = entries.at[index, "composition"]
                target = ComputedEntry(
                    composition,
                    float(entries.at[index, "predicted_formation_energy_per_atom"] * composition.num_atoms),
                    entry_id=row_id,
                )
                try:
                    decomposition, margin = hull.get_decomp_and_e_above_hull(
                        target, allow_negative=True, check_stable=False
                    )
                    simplex = sorted(
                        (
                            {"phase_id": str(phase.entry_id), "fraction": float(fraction)}
                            for phase, fraction in decomposition.items()
                        ),
                        key=lambda value: value["phase_id"],
                    )
                    simplex_ids = {value["phase_id"] for value in simplex}
                    overlap = sorted(simplex_ids.intersection(excluded_rows))
                    verified = (
                        row_id in excluded_rows
                        and excluded_rows == expected_class_rows
                        and not overlap
                    )
                    status = "ok" if verified else "failed_exclusion_audit"
                    reason = "" if verified else f"excluded phases found in simplex: {overlap}"
                    score_rows.append(
                        {
                            "row_id": row_id,
                            "model_name": model,
                            "signed_reference_hull_margin_eV_per_atom": float(margin),
                            "score_for_batch_relative_ranking": float(-margin),
                            "score_status": status,
                            "incomplete_reason": reason,
                            "decomposition_simplex_json": json.dumps(simplex, sort_keys=True),
                        }
                    )
                    audit_rows.append(
                        {
                            **base_audit,
                            "decomposition_simplex_json": json.dumps(simplex, sort_keys=True),
                            "decomposition_simplex_phase_ids_json": json.dumps(sorted(simplex_ids)),
                            "excluded_rows_in_decomposition_simplex_json": json.dumps(overlap),
                            "decomposition_simplex_excludes_equivalence_class": bool(not overlap),
                            "score_status": status,
                            "exclusion_verified": bool(verified),
                            "audit_reason": reason,
                        }
                    )
                except Exception as exc:
                    reason = f"{type(exc).__name__}: {exc}"
                    score_rows.append(
                        {
                            "row_id": row_id,
                            "model_name": model,
                            "signed_reference_hull_margin_eV_per_atom": np.nan,
                            "score_for_batch_relative_ranking": np.nan,
                            "score_status": "failed_target_decomposition",
                            "incomplete_reason": reason,
                            "decomposition_simplex_json": "[]",
                        }
                    )
                    audit_rows.append(
                        {
                            **base_audit,
                            "decomposition_simplex_json": "[]",
                            "decomposition_simplex_phase_ids_json": "[]",
                            "excluded_rows_in_decomposition_simplex_json": "[]",
                            "decomposition_simplex_excludes_equivalence_class": False,
                            "score_status": "failed_target_decomposition",
                            "exclusion_verified": False,
                            "audit_reason": reason,
                        }
                    )
        if system_number % 1000 == 0 or system_number == len(systems):
            print(f"{system_number}/{len(systems)} chemical systems", flush=True)
    scores = pd.DataFrame(score_rows)
    scores = entries.drop(columns="composition").merge(scores, on="row_id", how="inner")
    audit = pd.DataFrame(audit_rows)
    return scores, audit


def physical_endpoint_frame() -> pd.DataFrame:
    labels = pd.read_parquet(PHASE1 / "labels_by_view.parquet")
    frames = []
    for endpoint in PHYSICAL_ENDPOINTS:
        frame = labels[
            labels["label_view"].eq(endpoint) & labels["is_evaluable"].astype(bool)
        ][["row_id", "label"]].drop_duplicates("row_id")
        frames.append(frame.rename(columns={"label": endpoint}).set_index("row_id"))
    return pd.concat(frames, axis=1, join="inner").reset_index()


def evaluate_prototype(scores: pd.DataFrame, model: str, out: Path) -> dict:
    slug = file_slug(model)
    ok = scores[scores["score_status"].eq("ok")].copy()
    physical = physical_endpoint_frame()
    support = ok.merge(physical, on="row_id", how="inner", validate="one_to_one")
    support.to_parquet(out / f"physical_evaluation_support_{slug}.parquet", index=False)

    tie_audit = score_tie_audit(support["score_for_batch_relative_ranking"], K_VALUES)
    tie_audit.insert(0, "model_name", model)
    tie_audit["support_n"] = len(support)
    tie_audit.to_csv(out / f"ranking_tie_audit_{slug}.csv", index=False)

    topk_rows = []
    for endpoint in PHYSICAL_ENDPOINTS:
        for k in K_VALUES:
            result = analytic_tie_aware_topk(
                support["score_for_batch_relative_ranking"], support[endpoint].astype(int), k
            )
            topk_rows.append(
                {
                    "model_name": model,
                    "endpoint": endpoint,
                    "support_n": len(support),
                    "positive_n": int(support[endpoint].sum()),
                    "positive_rate": float(support[endpoint].mean()),
                    **result,
                }
            )
    pd.DataFrame(topk_rows).to_csv(out / f"tie_aware_topk_{slug}.csv", index=False)
    top1000 = tie_audit[tie_audit["K"].eq(1000)].iloc[0]
    return {
        "prototype_physical_support_n": int(len(support)),
        "score_ok_n": int(len(ok)),
        "top1000_boundary_tie_n": int(top1000["boundary_tie_n"]),
        "top1000_strictly_before_boundary_n": int(top1000["strictly_before_boundary_n"]),
        "largest_tie_block_n": int(top1000["largest_tie_block_n"]),
    }


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    d5 = load_d5()
    classes = load_or_build_equivalence(
        d5, args.structure_cache, args.out, args.force_equivalence
    )
    if args.equivalence_only:
        return

    energies = load_model_energies(args.model, args.score_dir, classes)
    if not args.skip_pool_manifests:
        write_pool_manifests(classes, args.out)
    scored_reference_pool = energies[
        energies["predicted_formation_energy_per_atom"].notna()
    ].copy()
    scores, exclusion = build_signed_margins(
        scored_reference_pool, args.model, args.max_systems
    )
    scores.to_parquet(args.out / f"batch_relative_signed_reference_hull_scores_{args.model}.parquet", index=False)
    slug = file_slug(args.model)
    exclusion.to_parquet(args.out / f"loso_exclusion_audit_{slug}.parquet", index=False)

    summary = {
        "model_name": args.model,
        "estimand": "leave-one-structural-equivalence-class-out batch-relative signed reference-hull margin",
        "transductive": True,
        "candidate_pool_version": CANDIDATE_POOL_VERSION,
        "reference_pool_version": REFERENCE_POOL_VERSION,
        "equivalence_version": str(classes["equivalence_version"].iloc[0]),
        "d5_row_n": int(len(d5)),
        "compound_candidate_n": int(d5["element_count"].ge(2).sum()),
        "elemental_target_n_not_ranked": int(d5["element_count"].lt(2).sum()),
        "score_status_counts": {str(k): int(v) for k, v in scores["score_status"].value_counts().items()},
        "exclusion_verified_n": int(exclusion["exclusion_verified"].sum()),
        "exclusion_failed_n": int((~exclusion["exclusion_verified"]).sum()),
        "inputs": {
            "d5": {
                "path": str((PHASE1 / "denominator_d5_model_complete.parquet").relative_to(ROOT)),
                "sha256": sha256(PHASE1 / "denominator_d5_model_complete.parquet"),
            },
            "structure_cache": {"path": str(args.structure_cache), "sha256": sha256(args.structure_cache)},
            "model_energy_table": {
                "path": str(args.score_dir / f"predicted_hull_scores_{args.model}.parquet"),
                "sha256": sha256(args.score_dir / f"predicted_hull_scores_{args.model}.parquet"),
            },
        },
    }
    if args.max_systems is None:
        summary.update(evaluate_prototype(scores, args.model, args.out))
    else:
        summary["prototype_limited_to_first_n_systems"] = int(args.max_systems)
    (args.out / f"ranking_summary_{slug}.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
