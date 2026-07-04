from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import requests
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.core import Composition, Lattice, Structure


ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "outputs" / "milestones" / "materials_label_discordance_full_mp_alex_43984"
OUT = ROOT / "outputs" / "milestones" / "jarvis_multisource_extension"
FIG_DIR = ROOT / "manuscript" / "figures"
RAW = ROOT / "raw" / "jarvis_optimade"

STRICT_MATCHES = FULL / "table_full_mp_alex_structure_matches.csv"
DEFAULT_MP_CACHE_CANDIDATES = [
    FULL / "mp_records_summary_structures.jsonl",
    Path("/home/waas/paper_experiments/github/discordance-/outputs/milestones/materials_label_discordance_full_mp_alex_43984/mp_records_summary_structures.jsonl"),
]

OPTIMADE_BASE = "https://jarvis.nist.gov/optimade/jarvisdft/v1/structures"
JARVIS_QUERY_DATE = "2026-07-04"
JARVIS_CACHE = RAW / "jarvis_optimade_structures.jsonl"
DOWNLOAD_STATUS = RAW / "jarvis_optimade_download_status.json"

TOLERANCES = {
    "tight": {"ltol": 0.1, "stol": 0.2, "angle_tol": 3},
    "default": {"ltol": 0.2, "stol": 0.3, "angle_tol": 5},
    "loose": {"ltol": 0.3, "stol": 0.4, "angle_tol": 7},
}
CUTOFFS_MEV = [0, 1, 5, 10, 25]

COLORS = {
    "mp": "#4C78A8",
    "alex": "#8E63A9",
    "jarvis": "#5A9C70",
    "conflict": "#E56B2E",
    "gray": "#68717D",
    "light_gray": "#EEF1F5",
    "ink": "#252A32",
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
        if path.is_file() and path.name != "MANIFEST_SHA256.txt":
            rows.append(f"{sha256_file(path)}  {path.relative_to(OUT).as_posix()}")
    (OUT / "MANIFEST_SHA256.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")


def reduced_formula(value: str | None) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    try:
        return Composition(str(value)).reduced_formula
    except Exception:
        return str(value)


def stable(ehull: float | int | None, cutoff_mev: int) -> bool | None:
    if ehull is None or pd.isna(ehull):
        return None
    return float(ehull) <= cutoff_mev / 1000.0


def exact_binomial_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if n == 0:
        return math.nan, math.nan
    try:
        from scipy.stats import beta

        lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
        hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
        return lo, hi
    except Exception:
        p = k / n
        se = math.sqrt(max(p * (1 - p), 0) / n)
        return max(0.0, p - 1.96 * se), min(1.0, p + 1.96 * se)


def resolve_mp_cache(path_arg: str | None) -> Path:
    candidates = []
    if path_arg:
        candidates.append(Path(path_arg))
    candidates.extend(DEFAULT_MP_CACHE_CANDIDATES)
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "MP structure cache is required for exact StructureMatcher matching. "
        "Pass --mp-cache or set up outputs/.../mp_records_summary_structures.jsonl."
    )


def optimade_record_to_public(row: dict[str, Any]) -> dict[str, Any] | None:
    attrs = row.get("attributes", {})
    rid = str(row.get("id", ""))
    if not rid.startswith("dft_3d_"):
        return None
    if attrs.get("_jarvis_ehull") is None:
        return None
    if not attrs.get("lattice_vectors") or not attrs.get("species_at_sites") or not attrs.get("cartesian_site_positions"):
        return None
    species_at_sites = attrs["species_at_sites"]
    positions = attrs["cartesian_site_positions"]
    if len(species_at_sites) != len(positions):
        return None
    formula = attrs.get("chemical_formula_reduced") or attrs.get("_jarvis_formula") or ""
    return {
        "optimade_id": rid,
        "jid": attrs.get("_jarvis_jid"),
        "formula": formula,
        "reduced_formula": reduced_formula(formula),
        "ehull": float(attrs["_jarvis_ehull"]),
        "n_sites": int(len(species_at_sites)),
        "jarvis_typ": attrs.get("_jarvis_typ"),
        "jarvis_dimensionality": attrs.get("_jarvis_dimensionality"),
        "source": attrs.get("_jarvis_source"),
        "spg_number": attrs.get("_jarvis_spg_number"),
    }


def optimade_record_to_structure(row: dict[str, Any]) -> Structure | None:
    attrs = row.get("attributes", {})
    try:
        return Structure(
            Lattice(attrs["lattice_vectors"]),
            attrs["species_at_sites"],
            attrs["cartesian_site_positions"],
            coords_are_cartesian=True,
        )
    except Exception:
        return None


def load_downloaded_ids() -> set[str]:
    if not JARVIS_CACHE.exists():
        return set()
    ids: set[str] = set()
    with JARVIS_CACHE.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                ids.add(json.loads(line)["id"])
            except Exception:
                continue
    return ids


def load_download_status() -> dict[str, Any]:
    if DOWNLOAD_STATUS.exists():
        return json.loads(DOWNLOAD_STATUS.read_text(encoding="utf-8"))
    return {"completed_queries": []}


def save_download_status(status: dict[str, Any]) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_STATUS.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_download_scope() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    status = load_download_status()
    bucket_counts = status.get("bucket_counts", {})
    completed_queries = set(status.get("completed_queries", []))
    queried_buckets = sorted(int(k) for k in bucket_counts)
    nonempty_buckets = sorted(int(k) for k, v in bucket_counts.items() if int(v.get("data_returned", 0)) > 0)
    max_bucket = max(queried_buckets) if queried_buckets else 0
    last_nonempty = max(nonempty_buckets) if nonempty_buckets else 0
    consecutive_empty_tail = 0
    for bucket in range(max_bucket, 0, -1):
        if int(bucket_counts.get(str(bucket), {}).get("data_returned", 0)) == 0:
            consecutive_empty_tail += 1
        else:
            break
    rows = [
        {
            "source_endpoint": OPTIMADE_BASE,
            "query_date": JARVIS_QUERY_DATE,
            "filter_template": "nelements={bucket}",
            "queried_bucket_min": min(queried_buckets) if queried_buckets else 0,
            "queried_bucket_max": max_bucket,
            "last_nonempty_bucket": last_nonempty,
            "consecutive_empty_tail": consecutive_empty_tail,
            "completed_page_queries": len(completed_queries),
            "cached_raw_records": sum(1 for _ in JARVIS_CACHE.open("r", encoding="utf-8")) if JARVIS_CACHE.exists() else 0,
            "scope_note": (
                "OPTIMADE site/count buckets were queried until the archived run observed a 20-bucket empty tail; "
                "scientific fields are taken from parsed structure records, not from the OPTIMADE bucket filter name."
            ),
        }
    ]
    pd.DataFrame(rows).to_csv(OUT / "table_jarvis_download_scope.csv", index=False)


def fetch_query(n_sites: int, page: int, retries: int = 5) -> dict[str, Any]:
    params = {"filter": f"nelements={n_sites}", "page": page, "page_limit": 20}
    headers = {"User-Agent": "materials-stability-label-discordance/1.0"}
    last_error = None
    for attempt in range(retries):
        try:
            r = requests.get(OPTIMADE_BASE, params=params, headers=headers, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception as exc:  # pragma: no cover - network robustness
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed OPTIMADE query n_sites={n_sites} page={page}: {last_error}")


def download_jarvis_optimade(max_sites: int, stop_after_consecutive_empty: int, workers: int) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    status = load_download_status()
    completed = set(status.get("completed_queries", []))
    downloaded_ids = load_downloaded_ids()

    consecutive_empty = 0
    with JARVIS_CACHE.open("a", encoding="utf-8") as out:
        for n_sites in range(1, max_sites + 1):
            first_key = f"{n_sites}:1"
            if first_key in completed:
                # We still need to know if this bucket was empty for stopping,
                # but status has already recorded it.
                bucket_status = status.get("bucket_counts", {}).get(str(n_sites), {})
                total = int(bucket_status.get("data_returned", 0))
            else:
                js = fetch_query(n_sites, 1)
                total = int(js.get("meta", {}).get("data_returned") or 0)
                status.setdefault("bucket_counts", {})[str(n_sites)] = {"data_returned": total}
                data = js.get("data", [])
                for row in data:
                    rid = str(row.get("id"))
                    if rid not in downloaded_ids:
                        out.write(json.dumps(row) + "\n")
                        downloaded_ids.add(rid)
                completed.add(first_key)
                status["completed_queries"] = sorted(completed)
                save_download_status(status)
                print(f"n_sites={n_sites} page=1 total={total} rows={len(data)}", flush=True)

            if total == 0:
                consecutive_empty += 1
                if consecutive_empty >= stop_after_consecutive_empty:
                    print(f"Stopping after {consecutive_empty} consecutive empty buckets at n_sites={n_sites}", flush=True)
                    write_download_scope()
                    break
                continue
            consecutive_empty = 0
            n_pages = math.ceil(total / 20)
            missing_pages = [page for page in range(2, n_pages + 1) if f"{n_sites}:{page}" not in completed]
            if missing_pages:
                print(f"n_sites={n_sites}: fetching {len(missing_pages)} missing pages with workers={workers}", flush=True)
            fetched: dict[int, list[dict[str, Any]]] = {}
            with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
                futs = {ex.submit(fetch_query, n_sites, page): page for page in missing_pages}
                for fut in as_completed(futs):
                    page = futs[fut]
                    js = fut.result()
                    fetched[page] = js.get("data", [])
                    if len(fetched) % 25 == 0 or len(fetched) == len(missing_pages):
                        print(
                            f"n_sites={n_sites}: fetched {len(fetched)}/{len(missing_pages)} missing pages",
                            flush=True,
                        )
            for page in sorted(fetched):
                key = f"{n_sites}:{page}"
                for row in fetched[page]:
                    rid = str(row.get("id"))
                    if rid not in downloaded_ids:
                        out.write(json.dumps(row) + "\n")
                        downloaded_ids.add(rid)
                completed.add(key)
                status["completed_queries"] = sorted(completed)
            status.setdefault("bucket_counts", {})[str(n_sites)]["pages_done"] = n_pages
            save_download_status(status)
            print(f"n_sites={n_sites} complete pages={n_pages} total_downloaded={len(downloaded_ids)}", flush=True)
    write_download_scope()
    print(f"Downloaded/cache records: {len(downloaded_ids)}", flush=True)


def load_jarvis_records() -> tuple[pd.DataFrame, dict[str, Structure]]:
    if not JARVIS_CACHE.exists():
        raise FileNotFoundError(f"Missing JARVIS cache: {JARVIS_CACHE}. Run with --download first.")
    public_rows = []
    structures = {}
    raw_n = 0
    with JARVIS_CACHE.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            raw_n += 1
            row = json.loads(line)
            public = optimade_record_to_public(row)
            if public is None:
                continue
            struct = optimade_record_to_structure(row)
            if struct is None:
                continue
            key = str(public["optimade_id"])
            public_rows.append(public)
            structures[key] = struct
    df = pd.DataFrame(public_rows).drop_duplicates("optimade_id")
    if not df.empty:
        df["jarvis_stable_exact"] = df["ehull"].le(0)
    print(f"JARVIS cache rows={raw_n}; parsed dft_3d usable={len(df)}", flush=True)
    return df, structures


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


def load_denominator() -> pd.DataFrame:
    df = pd.read_csv(STRICT_MATCHES)
    strict = df[df["match_status"].eq("strict_structure_match")].copy()
    strict["reduced_formula"] = strict["formula"].map(reduced_formula)
    strict["mp_e_above_hull"] = pd.to_numeric(strict["mp_e_above_hull"])
    strict["alex_e_above_hull"] = pd.to_numeric(strict["alex_e_above_hull"])
    return strict


def run_matching(mp_cache: Path) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    denom = load_denominator()
    mp_structures = load_mp_structures(mp_cache)
    jarvis, jarvis_structures = load_jarvis_records()
    jarvis_by_formula: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in jarvis.to_dict("records"):
        jarvis_by_formula[str(row["reduced_formula"])].append(row)

    summary_rows = [
        {"step": "archived_MP_alex_mp20_strict_denominator", "n": int(len(denom)), "scope": "primary_MP_alex_mp20_result"},
        {"step": "jarvis_optimade_cached_records", "n": int(sum(1 for _ in JARVIS_CACHE.open("r", encoding="utf-8"))) if JARVIS_CACHE.exists() else 0, "scope": "raw_cache_not_public_output"},
        {"step": "jarvis_dft_3d_records_with_structure_and_ehull", "n": int(len(jarvis)), "scope": "candidate_third_source_pool"},
        {"step": "denominator_rows_with_formula_candidate_in_jarvis", "n": int(denom["reduced_formula"].isin(jarvis_by_formula).sum()), "scope": "prefilter_only_not_match_result"},
    ]

    match_rows: list[dict[str, Any]] = []
    tolerance_rows = []
    default_matcher = StructureMatcher(**TOLERANCES["default"], primitive_cell=True, scale=True, attempt_supercell=True)

    for idx, drow in enumerate(denom.itertuples(index=False), start=1):
        mid = str(drow.material_id)
        mp_struct = mp_structures.get(mid)
        candidates = jarvis_by_formula.get(str(drow.reduced_formula), [])
        if mp_struct is None:
            continue
        exact_matches = []
        for cand in candidates:
            jid = str(cand["optimade_id"])
            jstruct = jarvis_structures.get(jid)
            if jstruct is None:
                continue
            try:
                matched = default_matcher.fit(mp_struct, jstruct)
            except Exception:
                matched = False
            if matched:
                exact_matches.append(cand)
        for cand in exact_matches:
            match_rows.append(
                {
                    "material_id": mid,
                    "formula": drow.formula,
                    "reduced_formula": drow.reduced_formula,
                    "chemical_system": drow.chemical_system,
                    "mp_num_sites": int(drow.num_sites),
                    "mp_e_above_hull": float(drow.mp_e_above_hull),
                    "alex_e_above_hull": float(drow.alex_e_above_hull),
                    "mp_stable_exact": bool(drow.mp_stable_exact),
                    "alex_stable_exact": bool(drow.alex_stable_exact),
                    "jarvis_optimade_id": cand["optimade_id"],
                    "jarvis_jid": cand["jid"],
                    "jarvis_formula": cand["formula"],
                    "jarvis_reduced_formula": cand["reduced_formula"],
                    "jarvis_n_sites": int(cand["n_sites"]),
                    "jarvis_ehull": float(cand["ehull"]),
                    "jarvis_stable_exact": bool(cand["jarvis_stable_exact"]),
                    "jarvis_typ": cand.get("jarvis_typ"),
                    "jarvis_dimensionality": cand.get("jarvis_dimensionality"),
                    "jarvis_source": cand.get("source"),
                    "match_status": "default_exact_structure_match",
                }
            )
        if idx % 5000 == 0:
            print(f"Matched {idx}/{len(denom)} denominator rows; exact row matches so far={len(match_rows)}", flush=True)

    matches = pd.DataFrame(match_rows)
    if matches.empty:
        matches.to_csv(OUT / "table_jarvis_default_exact_matches.csv", index=False)
        summary_rows.extend(
            [
                {"step": "jarvis_default_exact_structure_match_rows", "n": 0, "scope": "coverage_boundary"},
                {"step": "jarvis_unique_matched_denominator_rows", "n": 0, "scope": "coverage_boundary"},
            ]
        )
    else:
        matches = matches.sort_values(["material_id", "jarvis_optimade_id"])
        matches.to_csv(OUT / "table_jarvis_default_exact_matches.csv", index=False)
        match_counts = matches.groupby("material_id").size()
        summary_rows.extend(
            [
                {"step": "jarvis_default_exact_structure_match_rows", "n": int(len(matches)), "scope": "third_source_exact_match_rows"},
                {"step": "jarvis_unique_matched_denominator_rows", "n": int(match_counts.shape[0]), "scope": "third_source_exact_match_denominator"},
                {"step": "jarvis_single_match_denominator_rows", "n": int((match_counts == 1).sum()), "scope": "primary_triple_denominator_for_rates"},
                {"step": "jarvis_multiple_match_denominator_rows", "n": int((match_counts > 1).sum()), "scope": "duplicate_match_boundary"},
            ]
        )

    # Tolerance sweep on the formula-candidate universe.
    for tname, params in TOLERANCES.items():
        matcher = StructureMatcher(**params, primitive_cell=True, scale=True, attempt_supercell=True)
        matched_material_ids = set()
        match_row_n = 0
        for drow in denom.itertuples(index=False):
            mid = str(drow.material_id)
            mp_struct = mp_structures.get(mid)
            if mp_struct is None:
                continue
            for cand in jarvis_by_formula.get(str(drow.reduced_formula), []):
                jstruct = jarvis_structures.get(str(cand["optimade_id"]))
                if jstruct is None:
                    continue
                try:
                    matched = matcher.fit(mp_struct, jstruct)
                except Exception:
                    matched = False
                if matched:
                    matched_material_ids.add(mid)
                    match_row_n += 1
        tolerance_rows.append(
            {
                "tolerance": tname,
                "ltol": params["ltol"],
                "stol": params["stol"],
                "angle_tol": params["angle_tol"],
                "matched_row_pairs": int(match_row_n),
                "matched_denominator_rows": int(len(matched_material_ids)),
                "matched_fraction_of_43139": float(len(matched_material_ids) / len(denom)),
                "claim_scope": "coverage_sensitivity_not_formula_only_match",
            }
        )
        print(f"tolerance={tname} matched rows={match_row_n} denominator IDs={len(matched_material_ids)}", flush=True)

    pd.DataFrame(summary_rows).to_csv(OUT / "table_multisource_denominator_flow.csv", index=False)
    pd.DataFrame(tolerance_rows).to_csv(OUT / "table_jarvis_structure_matching_tolerance_sweep.csv", index=False)
    build_rate_outputs(denom)
    write_closeout()
    build_fig5()
    write_manifest()


def primary_triple_df() -> pd.DataFrame:
    matches_path = OUT / "table_jarvis_default_exact_matches.csv"
    if not matches_path.exists():
        return pd.DataFrame()
    matches = pd.read_csv(matches_path)
    if matches.empty:
        return matches
    counts = matches.groupby("material_id").size()
    single_ids = set(counts[counts.eq(1)].index.astype(str))
    triple = matches[matches["material_id"].astype(str).isin(single_ids)].copy()
    return triple.reset_index(drop=True)


def pairwise_rate_rows(df: pd.DataFrame, cutoff: int, evidence_scope: str, sensitivity_rule: str = "single_match_primary") -> list[dict[str, Any]]:
    rows = []
    pair_defs = [
        ("MP-JARVIS", "mp", "jarvis"),
        ("alex-mp-20-JARVIS", "alex_mp20", "jarvis"),
        ("MP-alex-mp-20", "mp", "alex_mp20"),
    ]
    if df.empty:
        for pair, _a, _b in pair_defs:
            rows.append(
                {
                    "cutoff_mev_atom": cutoff,
                    "pair": pair,
                    "n": 0,
                    "conflict_n": 0,
                    "conflict_fraction": math.nan,
                    "ci_low_95": math.nan,
                    "ci_high_95": math.nan,
                    "evidence_scope": evidence_scope,
                    "sensitivity_rule": sensitivity_rule,
                }
            )
        return rows
    labels = pd.DataFrame(
        {
            "mp": df["mp_e_above_hull"].map(lambda x: stable(x, cutoff)),
            "alex_mp20": df["alex_e_above_hull"].map(lambda x: stable(x, cutoff)),
            "jarvis": df["jarvis_ehull"].map(lambda x: stable(x, cutoff)),
        }
    )
    for pair, a, b in pair_defs:
        valid = labels[a].notna() & labels[b].notna()
        n = int(valid.sum())
        k = int(labels.loc[valid, a].ne(labels.loc[valid, b]).sum())
        lo, hi = exact_binomial_ci(k, n)
        rows.append(
            {
                "cutoff_mev_atom": cutoff,
                "pair": pair,
                "n": n,
                "conflict_n": k,
                "conflict_fraction": k / n if n else math.nan,
                "ci_low_95": lo,
                "ci_high_95": hi,
                "evidence_scope": evidence_scope,
                "sensitivity_rule": sensitivity_rule,
            }
        )
    return rows


def multiple_match_tie_break_sensitivity() -> pd.DataFrame:
    matches_path = OUT / "table_jarvis_default_exact_matches.csv"
    if not matches_path.exists():
        return pd.DataFrame()
    matches = pd.read_csv(matches_path)
    if matches.empty:
        return pd.DataFrame()

    rules = {
        "single_match_primary": primary_triple_df(),
        "include_multiple_lowest_jarvis_ehull": matches.sort_values(
            ["material_id", "jarvis_ehull", "jarvis_optimade_id"]
        ).drop_duplicates("material_id", keep="first"),
        "include_multiple_first_jarvis_identifier": matches.sort_values(
            ["material_id", "jarvis_optimade_id"]
        ).drop_duplicates("material_id", keep="first"),
    }
    rows = []
    for rule, df in rules.items():
        for cutoff in CUTOFFS_MEV:
            rows.extend(
                pairwise_rate_rows(
                    df,
                    cutoff,
                    evidence_scope="multiple_match_tie_break_sensitivity",
                    sensitivity_rule=rule,
                )
            )
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "table_jarvis_multiple_match_tie_break_sensitivity.csv", index=False)
    return out


def build_rate_outputs(denom: pd.DataFrame) -> None:
    write_download_scope()
    triple = primary_triple_df()
    evidence_scope = "coverage_boundary_result" if len(triple) < 100 else "triple_exact_match_conflict_rate_result"

    pair_rows = []
    for cutoff in CUTOFFS_MEV:
        rows = pairwise_rate_rows(triple, cutoff, evidence_scope)
        for row in rows:
            row.pop("sensitivity_rule", None)
        pair_rows.extend(rows)
    pd.DataFrame(pair_rows).to_csv(OUT / "table_pairwise_source_conflict_rates.csv", index=False)
    multiple_match_tie_break_sensitivity()

    comp_rows = []
    for cutoff in CUTOFFS_MEV:
        if triple.empty:
            continue
        tmp = triple.copy()
        tmp["mp_stable"] = tmp["mp_e_above_hull"].map(lambda x: stable(x, cutoff))
        tmp["alex_mp20_stable"] = tmp["alex_e_above_hull"].map(lambda x: stable(x, cutoff))
        tmp["jarvis_stable"] = tmp["jarvis_ehull"].map(lambda x: stable(x, cutoff))
        tmp["label_tuple"] = tmp.apply(
            lambda r: f"MP={int(bool(r.mp_stable))};alex-mp-20={int(bool(r.alex_mp20_stable))};JARVIS={int(bool(r.jarvis_stable))}",
            axis=1,
        )
        for label_tuple, n in tmp["label_tuple"].value_counts().sort_index().items():
            comp_rows.append(
                {
                    "cutoff_mev_atom": cutoff,
                    "label_tuple": label_tuple,
                    "n": int(n),
                    "fraction": int(n) / len(tmp),
                    "evidence_scope": evidence_scope,
                }
            )
    pd.DataFrame(comp_rows).to_csv(OUT / "table_three_source_label_composition.csv", index=False)

    flow = pd.read_csv(OUT / "table_multisource_denominator_flow.csv")
    flow.to_csv(OUT / "figure5_panel_a_denominator_flow.csv", index=False)
    pd.DataFrame(pair_rows).query("cutoff_mev_atom == 0").to_csv(
        OUT / "figure5_panel_b_pairwise_conflicts.csv", index=False
    )
    pd.DataFrame(comp_rows).query("cutoff_mev_atom == 0").to_csv(
        OUT / "figure5_panel_c_label_composition.csv", index=False
    )


def write_closeout() -> None:
    triple = primary_triple_df()
    flow = pd.read_csv(OUT / "table_multisource_denominator_flow.csv")
    scope = "coverage-boundary result" if len(triple) < 100 else "triple exact-match source-conflict result"
    flow_text = flow.to_csv(index=False)
    text = f"""# JARVIS multi-source extension closeout

This milestone adds JARVIS-DFT as a third public source while preserving the MP--alex-mp-20 audit as the primary result.

## Scope

- JARVIS source: JARVIS OPTIMADE `jarvisdft` records queried on {JARVIS_QUERY_DATE}, with `dft_3d_` identifiers, structure fields and `_jarvis_ehull`.
- Matching rule: reduced-formula prefilter followed by `pymatgen` `StructureMatcher` exact matching with the same default settings as the MP--alex-mp-20 audit (`ltol=0.2`, `stol=0.3`, `angle_tol=5`, `primitive_cell=True`, `scale=True`, `attempt_supercell=True`).
- No formula-only match is used as a result.
- No common hull is reconstructed.
- Primary MP--alex-mp-20 result remains the 43,139-row strict denominator.

## Outcome

The primary triple denominator contains {len(triple)} single-JARVIS exact matched MP--alex-mp-20 rows, so the JARVIS extension is interpreted as a **{scope}**.

## Output tables

- `table_multisource_denominator_flow.csv`
- `table_jarvis_download_scope.csv`
- `table_jarvis_default_exact_matches.csv`
- `table_jarvis_structure_matching_tolerance_sweep.csv`
- `table_jarvis_multiple_match_tie_break_sensitivity.csv`
- `table_pairwise_source_conflict_rates.csv`
- `table_three_source_label_composition.csv`
- `figure5_panel_a_denominator_flow.csv`
- `figure5_panel_b_pairwise_conflicts.csv`
- `figure5_panel_c_label_composition.csv`

## Denominator flow

```csv
{flow_text}```
"""
    (OUT / "JARVIS_MULTISOURCE_EXTENSION_CLOSEOUT.md").write_text(text + "\n", encoding="utf-8")


def setup_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif", "serif"],
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "font.size": 6.5,
            "axes.linewidth": 0.7,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "figure.dpi": 160,
        }
    )


def build_fig5() -> None:
    setup_style()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    flow = pd.read_csv(OUT / "figure5_panel_a_denominator_flow.csv")
    pair = pd.read_csv(OUT / "figure5_panel_b_pairwise_conflicts.csv")
    comp = pd.read_csv(OUT / "figure5_panel_c_label_composition.csv")

    fig, axes = plt.subplots(1, 3, figsize=(7.45, 2.45), gridspec_kw={"width_ratios": [1.15, 0.95, 1.05]})

    ax = axes[0]
    show_steps = [
        "archived_MP_alex_mp20_strict_denominator",
        "jarvis_dft_3d_records_with_structure_and_ehull",
        "denominator_rows_with_formula_candidate_in_jarvis",
        "jarvis_unique_matched_denominator_rows",
        "jarvis_single_match_denominator_rows",
    ]
    f = flow[flow["step"].isin(show_steps)].copy()
    labels = [
        "MP--alex-mp-20\nstrict denominator",
        "JARVIS-DFT\nusable records",
        "Formula\nprefilter",
        "Any JARVIS\nexact match",
        "Single-match\ntriple denominator",
    ]
    values = [int(f[f["step"].eq(s)]["n"].iloc[0]) if s in set(f["step"]) else 0 for s in show_steps]
    y = range(len(labels))[::-1]
    ax.barh(list(y), values, color=[COLORS["mp"], COLORS["jarvis"], COLORS["gray"], COLORS["conflict"], COLORS["alex"]])
    ax.set_yticks(list(y), labels)
    ax.set_xlabel("Rows")
    ax.set_title("a  Denominator flow", loc="left", fontweight="bold")
    for yi, val in zip(y, values):
        ax.text(val, yi, f" {val:,}", va="center", fontsize=6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax = axes[1]
    if pair.empty or pair["n"].fillna(0).max() == 0:
        ax.text(0.5, 0.5, "JARVIS exact-match\ncoverage boundary", ha="center", va="center", fontsize=8)
        ax.set_axis_off()
    else:
        x = range(len(pair))
        ax.bar(list(x), pair["conflict_fraction"] * 100, color=[COLORS["mp"], COLORS["alex"], COLORS["jarvis"]])
        ax.errorbar(
            list(x),
            pair["conflict_fraction"] * 100,
            yerr=[
                (pair["conflict_fraction"] - pair["ci_low_95"]) * 100,
                (pair["ci_high_95"] - pair["conflict_fraction"]) * 100,
            ],
            fmt="none",
            ecolor=COLORS["ink"],
            elinewidth=0.8,
            capsize=2,
        )
        ax.set_xticks(list(x), pair["pair"], rotation=35, ha="right")
        ax.set_ylabel("Source-conflict burden (%)")
        ax.set_title("b  Pairwise conflicts", loc="left", fontweight="bold")
        for xi, frac in zip(x, pair["conflict_fraction"] * 100):
            ax.text(xi, frac + 1.0, f"{frac:.1f}%", ha="center", va="bottom", fontsize=6)
        ax.set_ylim(0, max(30, float((pair["conflict_fraction"] * 100).max()) + 4))
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    ax = axes[2]
    if comp.empty:
        ax.text(0.5, 0.5, "No three-source\ncomposition table", ha="center", va="center", fontsize=8)
        ax.set_axis_off()
    else:
        comp = comp.sort_values("n", ascending=True)
        ax.barh(range(len(comp)), comp["n"], color=COLORS["light_gray"], edgecolor=COLORS["gray"])
        short_labels = (
            comp["label_tuple"]
            .str.replace("MP=", "", regex=False)
            .str.replace("alex-mp-20=", "", regex=False)
            .str.replace("JARVIS=", "", regex=False)
            .str.replace(";", "", regex=False)
        )
        ax.set_yticks(range(len(comp)), short_labels)
        ax.set_xlabel("Rows")
        ax.set_title("c  Label composition", loc="left", fontweight="bold")
        for yi, val in enumerate(comp["n"]):
            ax.text(val, yi, f" {int(val):,}", va="center", fontsize=6)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.tight_layout(w_pad=1.6)
    for suffix, kwargs in [
        (".pdf", {}),
        (".svg", {}),
        (".png", {"dpi": 600}),
        (".tiff", {"dpi": 600}),
    ]:
        fig.savefig(FIG_DIR / f"fig5_jarvis_multisource{suffix}", bbox_inches="tight", **kwargs)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true", help="Download/resume JARVIS OPTIMADE cache")
    parser.add_argument("--max-sites", type=int, default=80, help="Maximum OPTIMADE nelements bucket to query")
    parser.add_argument("--stop-after-consecutive-empty", type=int, default=20)
    parser.add_argument("--workers", type=int, default=8, help="Concurrent OPTIMADE page requests per bucket")
    parser.add_argument("--mp-cache", type=str, default=None)
    parser.add_argument("--match", action="store_true", help="Run exact matching and build outputs")
    args = parser.parse_args()

    if args.download:
        download_jarvis_optimade(
            max_sites=args.max_sites,
            stop_after_consecutive_empty=args.stop_after_consecutive_empty,
            workers=args.workers,
        )
    if args.match:
        run_matching(resolve_mp_cache(args.mp_cache))
    if not args.download and not args.match:
        parser.error("Choose --download and/or --match")


if __name__ == "__main__":
    main()
