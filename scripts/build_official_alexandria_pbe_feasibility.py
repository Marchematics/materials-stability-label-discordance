from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.core import Composition, Structure


ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "outputs" / "milestones" / "materials_label_discordance_full_mp_alex_43984"
OUT = ROOT / "outputs" / "milestones" / "official_alexandria_pbe_feasibility"
RAW = ROOT / "raw" / "official_alexandria_pbe"

STRICT_MATCHES = FULL / "table_full_mp_alex_structure_matches.csv"
DEFAULT_MP_CACHE_CANDIDATES = [
    FULL / "mp_records_summary_structures.jsonl",
    Path(
        "/home/waas/paper_experiments/github/discordance-/outputs/milestones/"
        "materials_label_discordance_full_mp_alex_43984/mp_records_summary_structures.jsonl"
    ),
]

ALEXANDRIA_PBE_SNAPSHOT = "2025.07.02"
ALEXANDRIA_PBE_INDEX_URL = "https://alexandria.icams.rub.de/data/pbe/2025.07.02/"
RETRIEVAL_DATE = date.today().isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest() -> None:
    rows = []
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name != "MANIFEST_SHA256.txt":
            rows.append(f"{sha256_file(path)}  {path.relative_to(OUT).as_posix()}")
    (OUT / "MANIFEST_SHA256.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")


def reduced_formula(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    try:
        return Composition(str(value)).reduced_formula
    except Exception:
        return str(value)


def stable(ehull: float | int | None) -> bool | None:
    if ehull is None or pd.isna(ehull):
        return None
    return float(ehull) <= 0.0


def resolve_mp_cache(path_arg: str | None) -> Path:
    candidates = []
    if path_arg:
        candidates.append(Path(path_arg))
    candidates.extend(DEFAULT_MP_CACHE_CANDIDATES)
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("MP structure cache is required. Pass --mp-cache.")


def load_denominator() -> pd.DataFrame:
    df = pd.read_csv(STRICT_MATCHES)
    strict = df[df["match_status"].eq("strict_structure_match")].copy()
    strict["reduced_formula"] = strict["formula"].map(reduced_formula)
    strict["mp_e_above_hull"] = pd.to_numeric(strict["mp_e_above_hull"], errors="coerce")
    strict["alex_mp20_e_above_hull"] = pd.to_numeric(strict["alex_e_above_hull"], errors="coerce")
    strict["mp_stable_exact"] = strict["mp_e_above_hull"].map(stable)
    strict["alex_mp20_stable_exact"] = strict["alex_mp20_e_above_hull"].map(stable)
    return strict.reset_index(drop=True)


def load_mp_structures(mp_cache: Path) -> dict[str, Structure]:
    structures: dict[str, Structure] = {}
    with mp_cache.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("structure") and not row.get("missing_mp_record"):
                try:
                    structures[str(row["material_id"])] = Structure.from_dict(row["structure"])
                except Exception:
                    continue
    print(f"Loaded MP structures: {len(structures)} from {mp_cache}", flush=True)
    return structures


def alexandria_record_to_candidate(record: dict[str, Any], source_file: str) -> dict[str, Any] | None:
    data = record.get("data") or {}
    ehull = data.get("e_above_hull")
    formula = data.get("formula")
    structure = record.get("structure")
    if ehull is None or formula is None or structure is None:
        return None
    try:
        ehull_f = float(ehull)
        struct = Structure.from_dict(structure)
    except Exception:
        return None
    mat_id = data.get("mat_id") or record.get("entry_id") or ""
    return {
        "official_alexandria_id": str(mat_id),
        "official_alexandria_formula": str(formula),
        "official_alexandria_reduced_formula": reduced_formula(formula),
        "official_alexandria_e_above_hull": ehull_f,
        "official_alexandria_stable_exact": bool(ehull_f <= 0.0),
        "official_alexandria_nsites": int(data.get("nsites") or len(struct)),
        "official_alexandria_prototype_id": data.get("prototype_id"),
        "official_alexandria_run_timestamp": data.get("run_timestamp"),
        "official_alexandria_source_file": source_file,
        "structure": struct,
    }


def load_alexandria_candidates(
    formula_set: set[str], max_shards: int | None = None
) -> tuple[dict[str, list[dict[str, Any]]], pd.DataFrame, pd.DataFrame]:
    shards = sorted(RAW.glob("alexandria_*.json.bz2"))
    if max_shards is not None:
        shards = shards[:max_shards]
    if not shards:
        raise FileNotFoundError(f"No Alexandria shards found in {RAW}")

    candidates_by_formula: dict[str, list[dict[str, Any]]] = defaultdict(list)
    schema_rows = []
    formula_counts: Counter[str] = Counter()

    for shard_i, path in enumerate(shards, start=1):
        with bz2.open(path, "rt", encoding="utf-8") as f:
            payload = json.load(f)
        records = payload.get("entries", [])
        counts = Counter()
        for record in records:
            counts["records_total"] += 1
            data = record.get("data") or {}
            if data:
                counts["records_with_data"] += 1
            if data.get("e_above_hull") is not None:
                counts["records_with_e_above_hull"] += 1
            if data.get("formula") is not None:
                counts["records_with_formula"] += 1
            if record.get("structure") is not None:
                counts["records_with_structure"] += 1

            formula = reduced_formula(data.get("formula"))
            if formula in formula_set:
                counts["records_with_denominator_formula"] += 1
                cand = alexandria_record_to_candidate(record, path.name)
                if cand is not None:
                    counts["usable_formula_prefilter_candidates"] += 1
                    candidates_by_formula[formula].append(cand)
                    formula_counts[formula] += 1
        schema_rows.append(
            {
                "source_file": path.name,
                "snapshot": ALEXANDRIA_PBE_SNAPSHOT,
                "retrieval_date": RETRIEVAL_DATE,
                **{k: int(v) for k, v in sorted(counts.items())},
                "field_path": "entries[].data.e_above_hull",
                "field_units": "eV/atom",
                "scope": "complete_PBE_3D_json_schema_audit",
            }
        )
        print(
            f"Parsed shard {shard_i}/{len(shards)}: formula-prefilter usable so far="
            f"{sum(len(v) for v in candidates_by_formula.values())}",
            flush=True,
        )

    formula_rows = [
        {"reduced_formula": formula, "official_alexandria_formula_prefilter_candidates": int(n)}
        for formula, n in sorted(formula_counts.items())
    ]
    return candidates_by_formula, pd.DataFrame(schema_rows), pd.DataFrame(formula_rows)


def run_matching(
    denom: pd.DataFrame,
    mp_structures: dict[str, Structure],
    candidates_by_formula: dict[str, list[dict[str, Any]]],
    max_rows: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    matcher = StructureMatcher(
        ltol=0.2,
        stol=0.3,
        angle_tol=5,
        primitive_cell=True,
        scale=True,
        attempt_supercell=True,
    )
    rows = []
    denom_rows = []
    work = denom.head(max_rows).copy() if max_rows is not None else denom

    for idx, drow in enumerate(work.itertuples(index=False), start=1):
        mid = str(drow.material_id)
        formula = str(drow.reduced_formula)
        candidates = candidates_by_formula.get(formula, [])
        mp_struct = mp_structures.get(mid)
        exact_count = 0
        if mp_struct is not None and candidates:
            for cand in candidates:
                try:
                    matched = matcher.fit(mp_struct, cand["structure"])
                except Exception:
                    matched = False
                if not matched:
                    continue
                exact_count += 1
                rows.append(
                    {
                        "material_id": mid,
                        "formula": drow.formula,
                        "reduced_formula": formula,
                        "chemical_system": drow.chemical_system,
                        "mp_num_sites": int(drow.num_sites),
                        "mp_e_above_hull": float(drow.mp_e_above_hull),
                        "alex_mp20_e_above_hull": float(drow.alex_mp20_e_above_hull),
                        "mp_stable_exact": bool(drow.mp_stable_exact),
                        "alex_mp20_stable_exact": bool(drow.alex_mp20_stable_exact),
                        "official_alexandria_id": cand["official_alexandria_id"],
                        "official_alexandria_formula": cand["official_alexandria_formula"],
                        "official_alexandria_reduced_formula": cand["official_alexandria_reduced_formula"],
                        "official_alexandria_nsites": cand["official_alexandria_nsites"],
                        "official_alexandria_e_above_hull": cand["official_alexandria_e_above_hull"],
                        "official_alexandria_stable_exact": cand["official_alexandria_stable_exact"],
                        "official_alexandria_prototype_id": cand["official_alexandria_prototype_id"],
                        "official_alexandria_run_timestamp": cand["official_alexandria_run_timestamp"],
                        "official_alexandria_source_file": cand["official_alexandria_source_file"],
                        "match_status": "default_exact_structure_match",
                    }
                )
        denom_rows.append(
            {
                "material_id": mid,
                "reduced_formula": formula,
                "has_mp_structure": bool(mp_struct is not None),
                "official_alexandria_formula_prefilter_candidates": int(len(candidates)),
                "official_alexandria_exact_matches": int(exact_count),
                "match_class": "single_exact_match"
                if exact_count == 1
                else "multiple_exact_matches"
                if exact_count > 1
                else "no_exact_match",
            }
        )
        if idx % 1000 == 0:
            print(f"Matched {idx}/{len(work)} denominator rows; exact row matches={len(rows)}", flush=True)

    return pd.DataFrame(rows), pd.DataFrame(denom_rows)


def pairwise_rate(df: pd.DataFrame, a: str, b: str) -> dict[str, Any]:
    if df.empty:
        return {"n": 0, "conflict_n": 0, "conflict_fraction": math.nan}
    av = df[a].astype(bool)
    bv = df[b].astype(bool)
    k = int(av.ne(bv).sum())
    n = int(len(df))
    return {"n": n, "conflict_n": k, "conflict_fraction": k / n if n else math.nan}


def write_multiple_match_tie_break_sensitivity(matches: pd.DataFrame) -> None:
    if matches.empty:
        pd.DataFrame(
            columns=["sensitivity_rule", "pair", "n", "conflict_n", "conflict_fraction", "evidence_scope"]
        ).to_csv(OUT / "table_official_alexandria_pbe_multiple_match_tie_break_sensitivity.csv", index=False)
        return

    match_counts = matches.groupby("material_id").size()
    rules = {
        "single_match_primary": matches[matches["material_id"].astype(str).isin(match_counts[match_counts.eq(1)].index.astype(str))].copy(),
        "include_multiple_lowest_official_alexandria_ehull": matches.sort_values(
            ["material_id", "official_alexandria_e_above_hull", "official_alexandria_id"]
        ).drop_duplicates("material_id", keep="first"),
        "include_multiple_first_official_alexandria_identifier": matches.sort_values(
            ["material_id", "official_alexandria_id"]
        ).drop_duplicates("material_id", keep="first"),
    }
    pair_defs = [
        ("MP-official Alexandria PBE", "mp_stable_exact", "official_alexandria_stable_exact"),
        ("alex-mp-20-official Alexandria PBE", "alex_mp20_stable_exact", "official_alexandria_stable_exact"),
        ("MP-alex-mp-20", "mp_stable_exact", "alex_mp20_stable_exact"),
    ]
    rows = []
    for rule, df in rules.items():
        for pair, a, b in pair_defs:
            stats = pairwise_rate(df, a, b)
            rows.append(
                {
                    "sensitivity_rule": rule,
                    "pair": pair,
                    **stats,
                    "evidence_scope": "multiple_match_tie_break_sensitivity_not_common_hull",
                }
            )
    pd.DataFrame(rows).to_csv(OUT / "table_official_alexandria_pbe_multiple_match_tie_break_sensitivity.csv", index=False)


def write_summaries(denom: pd.DataFrame, matches: pd.DataFrame, denom_audit: pd.DataFrame, schema: pd.DataFrame) -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    single_ids = set()
    multiple_ids = set()
    if not matches.empty:
        counts = matches.groupby("material_id").size()
        single_ids = set(counts[counts.eq(1)].index.astype(str))
        multiple_ids = set(counts[counts.gt(1)].index.astype(str))
    single = matches[matches["material_id"].astype(str).isin(single_ids)].copy() if not matches.empty else matches

    flow_rows = [
        {
            "step": "official_alexandria_pbe_complete_3d_shards_downloaded",
            "n": int(schema["source_file"].nunique()) if not schema.empty else 0,
            "scope": "complete_PBE_3D_json_not_convex_hull_only",
        },
        {
            "step": "official_alexandria_pbe_complete_3d_records_parsed",
            "n": int(schema["records_total"].sum()) if "records_total" in schema else 0,
            "scope": "complete_PBE_3D_json_not_convex_hull_only",
        },
        {
            "step": "official_alexandria_records_with_e_above_hull_formula_structure",
            "n": int(schema["usable_formula_prefilter_candidates"].sum())
            if "usable_formula_prefilter_candidates" in schema
            else 0,
            "scope": "after_MP_alex_mp20_formula_prefilter",
        },
        {
            "step": "primary_MP_alex_mp20_strict_denominator_rows",
            "n": int(len(denom)),
            "scope": "existing_primary_denominator",
        },
        {
            "step": "denominator_rows_with_official_alexandria_formula_candidate",
            "n": int((denom_audit["official_alexandria_formula_prefilter_candidates"] > 0).sum()),
            "scope": "formula_prefilter_only_not_structure_match",
        },
        {
            "step": "official_alexandria_exact_structure_match_rows",
            "n": int(len(matches)),
            "scope": "StructureMatcher_formula_prefilter_result",
        },
        {
            "step": "official_alexandria_unique_matched_denominator_rows",
            "n": int(denom_audit["official_alexandria_exact_matches"].gt(0).sum()),
            "scope": "MP_alex_mp20_official_Alexandria_triple_overlap",
        },
        {
            "step": "official_alexandria_single_match_denominator_rows",
            "n": int(len(single_ids)),
            "scope": "primary_single_match_triple_denominator_if_used_for_rates",
        },
        {
            "step": "official_alexandria_multiple_match_denominator_rows",
            "n": int(len(multiple_ids)),
            "scope": "duplicate_match_boundary_requires_sensitivity_if_claimed",
        },
    ]
    pd.DataFrame(flow_rows).to_csv(OUT / "table_official_alexandria_pbe_denominator_flow.csv", index=False)

    rate_rows = []
    pair_defs = [
        ("MP-official Alexandria PBE", "mp_stable_exact", "official_alexandria_stable_exact"),
        ("alex-mp-20-official Alexandria PBE", "alex_mp20_stable_exact", "official_alexandria_stable_exact"),
        ("MP-alex-mp-20", "mp_stable_exact", "alex_mp20_stable_exact"),
    ]
    for pair, a, b in pair_defs:
        stats = pairwise_rate(single, a, b)
        rate_rows.append(
            {
                "pair": pair,
                **stats,
                "denominator_rule": "single_official_Alexandria_exact_structure_match_within_existing_43139_MP_alex_mp20_denominator",
                "evidence_scope": "feasibility_rate_not_manuscript_claim",
            }
        )
    pd.DataFrame(rate_rows).to_csv(OUT / "table_official_alexandria_pbe_triple_overlap_summary.csv", index=False)
    write_multiple_match_tie_break_sensitivity(matches)

    decision = "coverage_boundary"
    unique_n = int(denom_audit["official_alexandria_exact_matches"].gt(0).sum())
    single_n = int(len(single_ids))
    if unique_n > 20000:
        decision = "main_text_candidate"
    elif single_n >= 5000:
        decision = "main_table_or_extended_data_candidate"

    closeout = [
        "# Official Alexandria-PBE feasibility closeout",
        "",
        "Scope: feasibility audit only. This is a source-native public-label portability check, not a common-hull reconstruction and not a mechanism attribution.",
        "",
        f"- Alexandria source: complete PBE 3D JSON snapshot `{ALEXANDRIA_PBE_SNAPSHOT}`.",
        f"- Retrieval date: `{RETRIEVAL_DATE}`.",
        "- Stability field found in complete JSON: `entries[].data.e_above_hull` in eV/atom.",
        "- Matching rule: reduced-formula prefilter followed by pymatgen `StructureMatcher` exact-structure matching.",
        "- MP identifiers are used only as MP row identifiers; official Alexandria rows are not joined by MP-ID.",
        "",
        "## Denominator flow",
        "",
        pd.DataFrame(flow_rows).to_markdown(index=False),
        "",
        "## Feasibility decision",
        "",
        f"`{decision}`",
        "",
        "Decision thresholds used: >20,000 unique MP--official Alexandria matches supports main-text consideration; 5,000--10,000 single-match triple rows supports a main table/figure or extended-data result; smaller or ambiguous coverage remains a Supplementary coverage boundary.",
    ]
    (OUT / "OFFICIAL_ALEXANDRIA_PBE_FEASIBILITY_CLOSEOUT.md").write_text("\n".join(closeout) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mp-cache", default=None)
    parser.add_argument("--max-shards", type=int, default=None, help="Debug only: parse first N shards.")
    parser.add_argument("--max-denominator-rows", type=int, default=None, help="Debug only: match first N denominator rows.")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    denom = load_denominator()
    mp_cache = resolve_mp_cache(args.mp_cache)
    mp_structures = load_mp_structures(mp_cache)
    formula_set = set(denom["reduced_formula"].astype(str))

    candidates_by_formula, schema, formula_prefilter = load_alexandria_candidates(formula_set, args.max_shards)
    schema.to_csv(OUT / "table_official_alexandria_pbe_schema_audit.csv", index=False)
    formula_prefilter.to_csv(OUT / "table_official_alexandria_pbe_formula_prefilter.csv", index=False)

    download_scope = pd.DataFrame(
        [
            {
                "source": "official_Alexandria_PBE_complete_3D_json",
                "snapshot": ALEXANDRIA_PBE_SNAPSHOT,
                "retrieval_date": RETRIEVAL_DATE,
                "index_url": ALEXANDRIA_PBE_INDEX_URL,
                "downloaded_shards": int(len(list(RAW.glob("alexandria_*.json.bz2")))),
                "parsed_shards": int(schema["source_file"].nunique()),
                "field_path": "entries[].data.e_above_hull",
                "field_units": "eV/atom",
                "guardrail": "complete_database_used; convex_hull_only_file_not_used_as_denominator",
            }
        ]
    )
    download_scope.to_csv(OUT / "table_official_alexandria_pbe_download_scope.csv", index=False)

    matches, denom_audit = run_matching(denom, mp_structures, candidates_by_formula, args.max_denominator_rows)
    matches.to_csv(OUT / "table_official_alexandria_pbe_exact_matches.csv", index=False)
    denom_audit.to_csv(OUT / "table_official_alexandria_pbe_denominator_row_audit.csv", index=False)
    write_summaries(denom, matches, denom_audit, schema)
    write_manifest()
    print(f"Wrote official Alexandria feasibility artifacts to {OUT}", flush=True)


if __name__ == "__main__":
    main()
