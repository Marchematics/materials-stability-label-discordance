from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import time
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.core import Composition, Structure


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "milestones" / "materials_label_discordance_full_mp_alex_43984"
ALEX_ZIP = Path("/home/waas/paper_experiments/private/mattergen_repo/data-release/alex-mp/alex_mp_20.zip")
MP_RECORDS_JSONL = OUT / "mp_records_summary_structures.jsonl"
MATCHES_CSV = OUT / "table_full_mp_alex_structure_matches.csv"
PUBLIC_MANIFEST_EXCLUDES = {
    "MANIFEST_SHA256.txt",
    # Public-safe outputs contain all strict-match labels needed for the
    # denominator analysis. The full MP structure cache is retained locally for
    # resumability but is intentionally not shipped in git because it is large.
    "mp_records_summary_structures.jsonl",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest() -> None:
    rows = []
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name not in PUBLIC_MANIFEST_EXCLUDES:
            rows.append(f"{sha256_file(path)}  {path.relative_to(OUT).as_posix()}")
    (OUT / "MANIFEST_SHA256.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")


def load_alex_mp_identifier_rows() -> pd.DataFrame:
    frames = []
    with zipfile.ZipFile(ALEX_ZIP) as zf:
        for name in ["alex_mp_20/val.csv", "alex_mp_20/train.csv"]:
            with zf.open(name) as f:
                df = pd.read_csv(
                    f,
                    usecols=[
                        "material_id",
                        "reduced_formula",
                        "chemical_system",
                        "num_sites",
                        "cif",
                        "energy_above_hull",
                    ],
                )
                df["alex_source_file"] = name
            frames.append(df)
    alex = pd.concat(frames, ignore_index=True)
    alex["material_id"] = alex["material_id"].astype(str)
    alex["is_mp_identifier"] = alex["material_id"].str.startswith("mp-")
    mp_rows = alex[alex["is_mp_identifier"]].drop_duplicates("material_id").sort_values("material_id").copy()
    mp_rows["alex_stable_exact"] = pd.to_numeric(mp_rows["energy_above_hull"], errors="coerce") <= 0
    return mp_rows.reset_index(drop=True)


def source_count_table(alex_mp: pd.DataFrame) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "source": "alex-mp v20 train+val",
                "count_type": "unique_MP_identifier_rows",
                "count": int(len(alex_mp)),
                "source_artifact": str(ALEX_ZIP),
            },
            {
                "source": "alex-mp v20 train+val",
                "count_type": "unique_chemical_systems",
                "count": int(alex_mp["chemical_system"].nunique()),
                "source_artifact": str(ALEX_ZIP),
            },
        ]
    ).to_csv(OUT / "table_full_denominator_source_counts.csv", index=False)


def read_done_mp_records() -> set[str]:
    if not MP_RECORDS_JSONL.exists():
        return set()
    done = set()
    with MP_RECORDS_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                done.add(str(json.loads(line)["material_id"]))
            except Exception:
                continue
    return done


def fetch_mp_records(material_ids: list[str], *, chunk_size: int = 100) -> None:
    from mp_api.client import MPRester

    api_key = os.environ.get("MP_API_KEY")
    if not api_key:
        raise RuntimeError("MP_API_KEY environment variable is required; source /root/.mp_api_env before running.")

    OUT.mkdir(parents=True, exist_ok=True)
    done = read_done_mp_records()
    todo = [mid for mid in material_ids if mid not in done]
    print(f"MP fetch checkpoint: done={len(done)} todo={len(todo)} total={len(material_ids)}", flush=True)
    if not todo:
        return

    with MPRester(api_key) as mpr, MP_RECORDS_JSONL.open("a", encoding="utf-8") as out:
        for start in range(0, len(todo), chunk_size):
            chunk = todo[start : start + chunk_size]
            docs = mpr.materials.summary.search(
                material_ids=chunk,
                fields=["material_id", "formula_pretty", "energy_above_hull", "structure"],
            )
            returned = set()
            for doc in docs:
                mid = str(doc.material_id)
                returned.add(mid)
                out.write(
                    json.dumps(
                        {
                            "material_id": mid,
                            "formula_pretty": getattr(doc, "formula_pretty", None),
                            "energy_above_hull": float(doc.energy_above_hull)
                            if doc.energy_above_hull is not None
                            else None,
                            "structure": doc.structure.as_dict() if doc.structure is not None else None,
                        }
                    )
                    + "\n"
                )
            for missing in sorted(set(chunk) - returned):
                out.write(
                    json.dumps(
                        {
                            "material_id": missing,
                            "formula_pretty": None,
                            "energy_above_hull": None,
                            "structure": None,
                            "missing_mp_record": True,
                        }
                    )
                    + "\n"
                )
            out.flush()
            done_count = len(read_done_mp_records())
            print(f"MP fetched {done_count}/{len(material_ids)}", flush=True)
            time.sleep(0.2)


def load_mp_record_map() -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    with MP_RECORDS_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            records[str(row["material_id"])] = row
    return records


def reduced_formula(value: str | None) -> str:
    if value is None:
        return ""
    try:
        return Composition(str(value)).reduced_formula
    except Exception:
        return str(value)


def existing_match_ids() -> set[str]:
    if not MATCHES_CSV.exists():
        return set()
    try:
        return set(pd.read_csv(MATCHES_CSV, usecols=["material_id"])["material_id"].astype(str))
    except Exception:
        return set()


def append_match_rows(rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "material_id",
        "match_status",
        "formula",
        "mp_formula",
        "reduced_formula_match",
        "chemical_system",
        "num_sites",
        "mp_e_above_hull",
        "alex_e_above_hull",
        "mp_stable_exact",
        "alex_stable_exact",
        "structure_match",
        "alex_source_file",
    ]
    write_header = not MATCHES_CSV.exists()
    with MATCHES_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def build_structure_matches(alex_mp: pd.DataFrame) -> None:
    matcher = StructureMatcher(
        ltol=0.2,
        stol=0.3,
        angle_tol=5,
        primitive_cell=True,
        scale=True,
        attempt_supercell=True,
    )
    records = load_mp_record_map()
    done = existing_match_ids()
    rows: list[dict[str, Any]] = []
    total = len(alex_mp)
    print(f"Structure matching checkpoint: done={len(done)} total={total}", flush=True)
    for i, row in enumerate(alex_mp.itertuples(index=False), start=1):
        mid = str(row.material_id)
        if mid in done:
            continue
        record = records.get(mid)
        alex_ehull = float(row.energy_above_hull)
        alex_stable = bool(alex_ehull <= 0.0)
        base = {
            "material_id": mid,
            "formula": row.reduced_formula,
            "chemical_system": row.chemical_system,
            "num_sites": int(row.num_sites),
            "alex_e_above_hull": alex_ehull,
            "alex_stable_exact": alex_stable,
            "alex_source_file": row.alex_source_file,
        }
        if record is None or record.get("missing_mp_record") or record.get("structure") is None:
            rows.append(
                {
                    **base,
                    "match_status": "missing_mp_record",
                    "mp_formula": record.get("formula_pretty") if record else "",
                    "reduced_formula_match": False,
                    "mp_e_above_hull": "",
                    "mp_stable_exact": "",
                    "structure_match": False,
                }
            )
        else:
            mp_ehull = record.get("energy_above_hull")
            formula_match = reduced_formula(row.reduced_formula) == reduced_formula(record.get("formula_pretty"))
            try:
                alex_structure = Structure.from_str(row.cif, fmt="cif")
                mp_structure = Structure.from_dict(record["structure"])
                matched = matcher.fit(mp_structure, alex_structure)
                status = "strict_structure_match" if matched else "structure_mismatch"
            except Exception as exc:  # noqa: BLE001
                matched = False
                status = f"match_error_{type(exc).__name__}"
            rows.append(
                {
                    **base,
                    "match_status": status,
                    "mp_formula": record.get("formula_pretty") or "",
                    "reduced_formula_match": bool(formula_match),
                    "mp_e_above_hull": float(mp_ehull) if mp_ehull is not None else "",
                    "mp_stable_exact": bool(mp_ehull <= 0.0) if mp_ehull is not None else "",
                    "structure_match": bool(matched),
                }
            )
        if len(rows) >= 200:
            append_match_rows(rows)
            rows.clear()
        if i % 1000 == 0:
            current_done = len(existing_match_ids()) + len(rows)
            print(f"Structure matched {current_done}/{total}", flush=True)
    if rows:
        append_match_rows(rows)


def write_summary() -> None:
    matches = pd.read_csv(MATCHES_CSV)
    strict = matches[matches["match_status"].eq("strict_structure_match")].copy()
    if not strict.empty:
        strict["mp_stable_exact_bool"] = strict["mp_stable_exact"].astype(str).str.lower().eq("true")
        strict["alex_stable_exact_bool"] = strict["alex_stable_exact"].astype(str).str.lower().eq("true")
        discordance = (strict["mp_stable_exact_bool"] != strict["alex_stable_exact_bool"]).mean()
        discordant_n = int((strict["mp_stable_exact_bool"] != strict["alex_stable_exact_bool"]).sum())
    else:
        discordance = math.nan
        discordant_n = 0
    pd.DataFrame(
        [
            {
                "alex_mp_identifier_rows": int(len(matches)),
                "mp_records_successfully_queried": int((~matches["match_status"].eq("missing_mp_record")).sum()),
                "reduced_formula_matches": int(matches["reduced_formula_match"].astype(str).str.lower().eq("true").sum()),
                "strict_structure_matches": int(len(strict)),
                "mp_alex_labels_available": int(strict[["mp_e_above_hull", "alex_e_above_hull"]].notna().all(axis=1).sum())
                if not strict.empty
                else 0,
                "discordant_n": discordant_n,
                "discordance_rate": float(discordance) if math.isfinite(discordance) else "",
                "claim_scope": "full_43984_MP_identifier_denominator",
            }
        ]
    ).to_csv(OUT / "table_full_mp_alex_denominator_summary.csv", index=False)
    counts = matches["match_status"].value_counts(dropna=False).rename_axis("match_status").reset_index(name="count")
    counts.to_csv(OUT / "table_full_mp_alex_match_status_counts.csv", index=False)
    (OUT / "FULL_MP_ALEX_DENOMINATOR_CLOSEOUT.md").write_text(
        "# Full MP-Alex Denominator Run\n\n"
        "This milestone processes all Alexandria v20 rows with MP identifiers. It is separate from the earlier 287-row scored diagnostic and does not overwrite those artifacts.\n\n"
        "The public-safe artifact set commits the strict-match CSV and summary tables. The full MP structure JSONL cache is retained locally for resumability and is excluded from git because it is a large raw API cache, not a paper-facing table.\n\n"
        f"{pd.read_csv(OUT / 'table_full_mp_alex_denominator_summary.csv').to_markdown(index=False)}\n",
        encoding="utf-8",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    alex_mp = load_alex_mp_identifier_rows()
    source_count_table(alex_mp)
    fetch_mp_records(alex_mp["material_id"].astype(str).tolist())
    build_structure_matches(alex_mp)
    write_summary()
    write_manifest()


if __name__ == "__main__":
    main()
