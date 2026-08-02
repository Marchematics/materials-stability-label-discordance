#!/usr/bin/env python3
"""Build tight/default/loose matching-sensitivity cohorts and equivalence classes.

The cross-source part is a survival audit of the frozen D1 and D2 mappings:
it re-evaluates each already-declared matched pair and does not search for new
loose-tolerance matches outside those cohorts.  The D5 equivalence-class part
rebuilds the full graph at each tolerance so the ranking exclusion boundary can
also be re-evaluated.
"""

from __future__ import annotations

import argparse
import bz2
import gzip
import itertools
import json
import zipfile
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import ijson
import pandas as pd
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.core import Composition, Structure


ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "outputs" / "phase1_v2"
OUT = ROOT / "outputs" / "referee_revision_v3" / "matching_sensitivity"
MP_CACHE = Path(
    "/home/waas/paper_experiments/github/discordance-/outputs/milestones/"
    "materials_label_discordance_full_mp_alex_43984/mp_records_summary_structures.jsonl"
)
ALEXMP_ZIP = Path(
    "/home/waas/paper_experiments/private/mattergen_repo/data-release/"
    "alex-mp/alex_mp_20.zip"
)
OFFICIAL_RAW = Path("/root/sourceaware_alexandria_pbe_2025_07_02")
OFFICIAL_MATCHES = Path(
    "/home/waas/paper_experiments/github/materials-stability-label-discordance/"
    "outputs/milestones/official_alexandria_pbe_feasibility/"
    "table_official_alexandria_pbe_exact_matches.csv"
)

TOLERANCES = {
    "tight": {"ltol": 0.1, "stol": 0.2, "angle_tol": 3.0},
    "default": {"ltol": 0.2, "stol": 0.3, "angle_tol": 5.0},
    "loose": {"ltol": 0.3, "stol": 0.4, "angle_tol": 7.0},
}

_PAIR_MP: dict[str, Structure] = {}
_PAIR_ALEXMP: dict[str, Structure] = {}
_PAIR_OFFICIAL: dict[str, Structure] = {}
_D1_MATCH_BY_MP: dict[str, dict[str, bool]] = {}
_WORKER_MATCHERS: dict[str, StructureMatcher] | None = None


class NonFiniteJSONFilter:
    """Binary reader that maps non-standard JSON floats to finite placeholders."""

    def __init__(self, raw):
        self.raw = raw
        self.buffer = bytearray()
        self.carry = b""
        self.eof = False

    @staticmethod
    def clean(value: bytes) -> bytes:
        return value.replace(b"Infinity", b"0.000000").replace(b"NaN", b"0.0")

    def read(self, size: int = -1) -> bytes:
        if size == 0:
            return b""
        if size < 0:
            chunks = [bytes(self.buffer), self.carry, self.raw.read()]
            self.buffer.clear()
            self.carry = b""
            self.eof = True
            return self.clean(b"".join(chunks))
        while len(self.buffer) < size and not self.eof:
            chunk = self.raw.read(max(65536, size))
            if chunk:
                data = self.carry + chunk
                if len(data) > 8:
                    self.buffer.extend(self.clean(data[:-8]))
                    self.carry = data[-8:]
                else:
                    self.carry = data
            else:
                self.buffer.extend(self.clean(self.carry))
                self.carry = b""
                self.eof = True
        result = bytes(self.buffer[:size])
        del self.buffer[:size]
        return result


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
    frame = pd.read_parquet(PHASE1 / "denominator_d5_model_complete.parquet").copy()
    frame["elements"] = frame["formula"].map(
        lambda value: tuple(sorted(element.symbol for element in Composition(value).elements))
    )
    frame["element_count"] = frame["elements"].map(len)
    return frame.sort_values("row_id").reset_index(drop=True)


def load_structure_dicts(frame: pd.DataFrame, cache: Path) -> dict[str, dict]:
    required = set(frame["mp_id"].astype(str))
    structures: dict[str, dict] = {}
    with cache.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            material_id = str(record["material_id"])
            if material_id in required and record.get("structure"):
                structures[material_id] = record["structure"]
    missing = required - set(structures)
    if missing:
        raise RuntimeError(f"MP structure cache lacks {len(missing)} required structures")
    return structures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--mp-cache", type=Path, default=MP_CACHE)
    parser.add_argument("--alexmp-zip", type=Path, default=ALEXMP_ZIP)
    parser.add_argument("--official-raw", type=Path, default=OFFICIAL_RAW)
    parser.add_argument("--official-matches", type=Path, default=OFFICIAL_MATCHES)
    parser.add_argument("--force-source-caches", action="store_true")
    return parser.parse_args()


def write_jsonl_gz(path: Path, rows: list[dict]) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(",", ":")) + "\n")


def load_jsonl_gz_structures(path: Path, id_column: str) -> dict[str, Structure]:
    out: dict[str, Structure] = {}
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            out[str(row[id_column])] = Structure.from_dict(row["structure"])
    return out


def prepare_alexmp_cache(zip_path: Path, required: set[str], cache: Path, force: bool) -> None:
    if cache.exists() and not force:
        return
    rows = []
    seen: set[str] = set()
    with zipfile.ZipFile(zip_path) as archive:
        for csv_name in ("alex_mp_20/train.csv", "alex_mp_20/val.csv"):
            frame = pd.read_csv(archive.open(csv_name), usecols=["material_id", "cif"])
            for record in frame.itertuples(index=False):
                material_id = str(record.material_id)
                if material_id not in required or material_id in seen:
                    continue
                try:
                    structure = Structure.from_str(str(record.cif), fmt="cif")
                except Exception:
                    continue
                rows.append(
                    {
                        "material_id": material_id,
                        "source_file": csv_name,
                        "structure": structure.as_dict(),
                    }
                )
                seen.add(material_id)
    write_jsonl_gz(cache, rows)


def prepare_official_cache(
    raw_root: Path,
    d2: pd.DataFrame,
    matches_path: Path,
    cache: Path,
    force: bool,
) -> None:
    if cache.exists() and not force:
        return
    mapping = pd.read_csv(
        matches_path,
        usecols=["official_alexandria_id", "official_alexandria_source_file"],
    ).drop_duplicates("official_alexandria_id")
    mapping = d2[["official_alexandria_id"]].merge(
        mapping, on="official_alexandria_id", how="left", validate="many_to_one"
    )
    if mapping["official_alexandria_source_file"].isna().any():
        raise RuntimeError("Official Alexandria source-file mapping is incomplete for D2")
    targets = {
        source_file: set(group["official_alexandria_id"].astype(str))
        for source_file, group in mapping.groupby("official_alexandria_source_file")
    }
    cache.parent.mkdir(parents=True, exist_ok=True)
    temporary = cache.with_suffix(cache.suffix + ".tmp")
    found: set[str] = set()
    tasks = [(raw_root / source_file, source_file, wanted) for source_file, wanted in targets.items()]
    extracted: dict[str, list[dict]] = {}
    with ProcessPoolExecutor(max_workers=min(8, len(tasks))) as executor:
        futures = {
            executor.submit(extract_official_shard, path, source_file, wanted): source_file
            for path, source_file, wanted in tasks
        }
        for completed_n, future in enumerate(as_completed(futures), start=1):
            source_file = futures[future]
            records = future.result()
            extracted[source_file] = records
            found.update(record["official_alexandria_id"] for record in records)
            print(
                f"official structures {completed_n}/{len(tasks)}: "
                f"{len(records)}/{len(targets[source_file])} from {source_file}",
                flush=True,
            )
    with gzip.open(temporary, "wt", encoding="utf-8") as output:
        for source_file in sorted(extracted):
            for record in extracted[source_file]:
                output.write(json.dumps(record, separators=(",", ":")) + "\n")
    missing = set(d2["official_alexandria_id"].astype(str)) - found
    if missing:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"Missing {len(missing)} official Alexandria D2 structures")
    temporary.replace(cache)


def extract_official_shard(path: Path, source_file: str, wanted: set[str]) -> list[dict]:
    records = []
    with bz2.open(path, "rb") as raw_handle:
        handle = NonFiniteJSONFilter(raw_handle)
        for record in ijson.items(handle, "entries.item", use_float=True):
            data = record.get("data") or {}
            identifier = str(data.get("mat_id") or record.get("entry_id") or "")
            if identifier not in wanted:
                continue
            structure = record.get("structure")
            if structure is not None:
                records.append(
                    {
                        "official_alexandria_id": identifier,
                        "source_file": source_file,
                        "structure": structure,
                    }
                )
            if len(records) == len(wanted):
                break
    return records


def match_pair_all_tolerances(left: Structure, right: Structure) -> dict[str, bool]:
    global _WORKER_MATCHERS
    if _WORKER_MATCHERS is None:
        _WORKER_MATCHERS = {
            name: StructureMatcher(
                **parameters,
                primitive_cell=True,
                scale=True,
                attempt_supercell=True,
                allow_subset=False,
            )
            for name, parameters in TOLERANCES.items()
        }
    result = {}
    for name, matcher in _WORKER_MATCHERS.items():
        try:
            result[name] = bool(matcher.fit(left, right))
        except Exception:
            result[name] = False
    return result


def chunks(records: list[tuple], size: int = 1000):
    for start in range(0, len(records), size):
        yield records[start : start + size]


def audit_d1_chunk(records: list[tuple]) -> list[dict]:
    rows = []
    for row_id, material_id, chemical_system in records:
        available = material_id in _PAIR_MP and material_id in _PAIR_ALEXMP
        matched = (
            match_pair_all_tolerances(_PAIR_MP[material_id], _PAIR_ALEXMP[material_id])
            if available
            else {name: False for name in TOLERANCES}
        )
        rows.append(
            {
                "row_id": row_id,
                "mp_id": material_id,
                "chemical_system": chemical_system,
                "source_pair": "MP--alex-mp-20",
                "structures_available": available,
                **{f"matched_{name}": value for name, value in matched.items()},
            }
        )
    return rows


def audit_d2_chunk(records: list[tuple]) -> list[dict]:
    rows = []
    for row_id, material_id, official_id, chemical_system in records:
        available = material_id in _PAIR_MP and official_id in _PAIR_OFFICIAL
        official_matched = (
            match_pair_all_tolerances(_PAIR_MP[material_id], _PAIR_OFFICIAL[official_id])
            if available
            else {name: False for name in TOLERANCES}
        )
        record = {
            "row_id": row_id,
            "mp_id": material_id,
            "official_alexandria_id": official_id,
            "chemical_system": chemical_system,
            "official_structures_available": available,
        }
        d1_match = _D1_MATCH_BY_MP[material_id]
        for name in TOLERANCES:
            record[f"mp_alexmp20_matched_{name}"] = d1_match[name]
            record[f"mp_official_alexandria_matched_{name}"] = official_matched[name]
            record[f"d2_retained_{name}"] = d1_match[name] and official_matched[name]
        rows.append(record)
    return rows


def source_pair_survival(
    d1: pd.DataFrame,
    d2: pd.DataFrame,
    mp: dict[str, Structure],
    alexmp: dict[str, Structure],
    official: dict[str, Structure],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    global _PAIR_MP, _PAIR_ALEXMP, _PAIR_OFFICIAL, _D1_MATCH_BY_MP, _WORKER_MATCHERS
    _PAIR_MP, _PAIR_ALEXMP, _PAIR_OFFICIAL = mp, alexmp, official
    _WORKER_MATCHERS = None
    d1_records = [
        (row.row_id, str(row.mp_id), row.chemical_system)
        for row in d1.itertuples(index=False)
    ]
    d1_rows = []
    d1_chunks = list(chunks(d1_records))
    with ProcessPoolExecutor(max_workers=min(8, len(d1_chunks))) as executor:
        for completed, rows in enumerate(executor.map(audit_d1_chunk, d1_chunks), start=1):
            d1_rows.extend(rows)
            if completed % 5 == 0 or completed == len(d1_chunks):
                print(f"D1 pair audit {min(completed * 1000, len(d1))}/{len(d1)}", flush=True)
    d1_status = pd.DataFrame(d1_rows).sort_values("row_id").reset_index(drop=True)
    _D1_MATCH_BY_MP = {
        str(record.mp_id): {
            name: bool(getattr(record, f"matched_{name}")) for name in TOLERANCES
        }
        for record in d1_status.itertuples(index=False)
    }

    _WORKER_MATCHERS = None
    d2_records = [
        (row.row_id, str(row.mp_id), str(row.official_alexandria_id), row.chemical_system)
        for row in d2.itertuples(index=False)
    ]
    d2_rows = []
    d2_chunks = list(chunks(d2_records))
    with ProcessPoolExecutor(max_workers=min(8, len(d2_chunks))) as executor:
        for completed, rows in enumerate(executor.map(audit_d2_chunk, d2_chunks), start=1):
            d2_rows.extend(rows)
            if completed % 5 == 0 or completed == len(d2_chunks):
                print(f"D2 pair audit {min(completed * 1000, len(d2))}/{len(d2)}", flush=True)
    d2_status = pd.DataFrame(d2_rows).sort_values("row_id").reset_index(drop=True)
    return d1_status, d2_status


def build_equivalence_at_tolerance(
    d5: pd.DataFrame,
    structure_dicts: dict[str, dict],
    tolerance_name: str,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    parameters = TOLERANCES[tolerance_name]
    matcher = StructureMatcher(
        **parameters,
        primitive_cell=True,
        scale=True,
        attempt_supercell=True,
        allow_subset=False,
    )
    union = UnionFind(d5["row_id"].astype(str).tolist())
    edge_rows: list[dict] = []

    def add(left: str, right: str, relation: str) -> None:
        union.union(left, right)
        edge_rows.append({"row_id_a": left, "row_id_b": right, "relation": relation})

    for column, relation in (
        ("structure_hash", "same_canonical_hash"),
        ("mp_id", "same_mp_identifier"),
        ("mattergen_id", "same_mattergen_identifier"),
        ("official_alexandria_id", "same_alexandria_identifier"),
    ):
        usable = d5[column].notna() & d5[column].astype(str).str.strip().ne("")
        for _, group in d5.loc[usable].groupby(column, sort=False):
            ids = sorted(group["row_id"].astype(str))
            for left, right in zip(ids, ids[1:]):
                add(left, right, relation)

    pair_n = 0
    failed_n = 0
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
                equivalent = matcher.fit(
                    structures[left["row_id"]], structures[right["row_id"]]
                )
            except Exception:
                equivalent = False
                failed_n += 1
            if equivalent:
                add(left["row_id"], right["row_id"], "structure_matcher_equivalent")

    components: dict[str, list[str]] = defaultdict(list)
    for row_id in d5["row_id"].astype(str):
        components[union.find(row_id)].append(row_id)
    ordered = sorted((sorted(value) for value in components.values()), key=lambda x: x[0])
    class_by_row = {
        row_id: f"TEQ-{tolerance_name}-{index:06d}"
        for index, members in enumerate(ordered, start=1)
        for row_id in members
    }
    classes = d5.copy()
    classes["equivalence_class_id"] = classes["row_id"].map(class_by_row)
    classes["equivalence_class_size"] = (
        classes.groupby("equivalence_class_id")["row_id"].transform("size").astype(int)
    )
    classes["equivalence_version"] = (
        f"D5-StructureMatcher-{tolerance_name}-ltol{parameters['ltol']}-"
        f"stol{parameters['stol']}-angle{parameters['angle_tol']}-v1"
    )
    classes["matcher_ltol"] = parameters["ltol"]
    classes["matcher_stol"] = parameters["stol"]
    classes["matcher_angle_tol"] = parameters["angle_tol"]
    classes["matcher_primitive_cell"] = True
    classes["matcher_scale"] = True
    classes["matcher_attempt_supercell"] = True
    classes["matcher_allow_subset"] = False
    edges = pd.DataFrame(edge_rows).drop_duplicates()
    metadata = {
        "tolerance": tolerance_name,
        **parameters,
        "row_n": int(len(classes)),
        "equivalence_class_n": int(classes["equivalence_class_id"].nunique()),
        "non_singleton_class_n": int(
            (classes.groupby("equivalence_class_id").size() > 1).sum()
        ),
        "largest_class_n": int(classes["equivalence_class_size"].max()),
        "candidate_pair_comparisons": int(pair_n),
        "failed_pair_comparisons": int(failed_n),
        "recorded_relation_edges": int(len(edges)),
    }
    return classes, edges, metadata


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    cache_dir = args.out / "cache"
    cache_dir.mkdir(exist_ok=True)
    d1 = pd.read_parquet(PHASE1 / "denominator_d1_mp_alexmp20_exact.parquet")
    d2 = pd.read_parquet(PHASE1 / "denominator_d2_triple_single_match.parquet")
    d5 = load_d5()

    alexmp_cache = cache_dir / "alexmp20_d1_structures.jsonl.gz"
    official_cache = cache_dir / "official_alexandria_d2_structures.jsonl.gz"
    prepare_alexmp_cache(
        args.alexmp_zip, set(d1["mp_id"].astype(str)), alexmp_cache,
        args.force_source_caches,
    )
    prepare_official_cache(
        args.official_raw, d2, args.official_matches, official_cache,
        args.force_source_caches,
    )

    mp_dicts = load_structure_dicts(d1.rename(columns={"row_id": "_row_id"}), args.mp_cache)
    mp = {identifier: Structure.from_dict(value) for identifier, value in mp_dicts.items()}
    alexmp = load_jsonl_gz_structures(alexmp_cache, "material_id")
    official = load_jsonl_gz_structures(official_cache, "official_alexandria_id")
    d1_status, d2_status = source_pair_survival(d1, d2, mp, alexmp, official)
    d1_status.to_parquet(args.out / "d1_pair_survival_by_tolerance.parquet", index=False)
    d2_status.to_parquet(args.out / "d2_pair_survival_by_tolerance.parquet", index=False)

    # Build full D5 equivalence graphs independently at all three tolerances.
    d5_structure_dicts = load_structure_dicts(d5, args.mp_cache)
    summaries = []
    for tolerance_name in TOLERANCES:
        tolerance_out = args.out / tolerance_name
        tolerance_out.mkdir(exist_ok=True)
        classes, edges, metadata = build_equivalence_at_tolerance(
            d5, d5_structure_dicts, tolerance_name
        )
        classes.to_parquet(tolerance_out / "structural_equivalence_classes.parquet", index=False)
        edges.to_parquet(tolerance_out / "structural_equivalence_edges.parquet", index=False)
        (tolerance_out / "structural_equivalence_metadata.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        summaries.append(metadata)
        print(json.dumps(metadata, sort_keys=True), flush=True)
    pd.DataFrame(summaries).to_csv(args.out / "equivalence_class_sensitivity.csv", index=False)

    metadata = {
        "analysis_type": "survival audit of frozen D1/D2 mappings plus full D5 equivalence-graph rebuild",
        "does_not_search_new_cross_source_matches": True,
        "d1_frozen_n": int(len(d1)),
        "d2_frozen_n": int(len(d2)),
        "d5_frozen_n": int(len(d5)),
        "alexmp_structure_n": int(len(alexmp)),
        "official_alexandria_structure_n": int(len(official)),
        "tolerances": TOLERANCES,
    }
    (args.out / "matching_sensitivity_build_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
