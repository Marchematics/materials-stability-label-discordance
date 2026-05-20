from __future__ import annotations

import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import concurrent.futures
from pathlib import Path
from typing import Any

import pandas as pd
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.core import Composition, Lattice, Structure


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "milestones" / "materials_label_discordance_preregistration"
ALEX_ZIP = Path("/home/waas/paper_experiments/private/mattergen_repo/data-release/alex-mp/alex_mp_20.zip")
OQMD_CACHE = Path("/home/waas/paper_experiments/private/materials_independent_dft_validation/oqmd_route_b_cache")
OQMD_BASE = "http://oqmd.org/oqmdapi/formationenergy"
NEAR_HULL_EV = 0.025


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
            rows.append(f"{sha256_file(path)}  {path.relative_to(OUT)}")
    (OUT / "MANIFEST_SHA256.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")


def load_route_b_matches() -> pd.DataFrame:
    df = pd.read_csv(OUT / "table_route_b_full_snapshot_matches.csv")
    strict = df[df["match_status"].eq("strict_structure_match")].copy()
    strict["mp_e_above_hull"] = pd.to_numeric(strict["mp_e_above_hull"], errors="coerce")
    strict["alex_e_above_hull"] = pd.to_numeric(strict["alex_e_above_hull"], errors="coerce")
    strict["mp_stable_exact"] = strict["mp_stable_exact"].astype(str).str.lower().eq("true")
    strict["alex_stable_exact"] = strict["alex_stable_exact"].astype(str).str.lower().eq("true")
    strict["discordant"] = strict["mp_stable_exact"] != strict["alex_stable_exact"]
    return strict


def load_alex_rows(material_ids: set[str]) -> pd.DataFrame:
    frames = []
    with zipfile.ZipFile(ALEX_ZIP) as zf:
        for name in ["alex_mp_20/val.csv", "alex_mp_20/train.csv"]:
            with zf.open(name) as f:
                frames.append(
                    pd.read_csv(
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
                )
    df = pd.concat(frames, ignore_index=True)
    df = df[df["material_id"].astype(str).isin(material_ids)].drop_duplicates("material_id").copy()
    return df


def query_oqmd(chemical_system: str, *, limit: int = 1000, timeout: int = 30, retries: int = 2) -> dict[str, Any]:
    OQMD_CACHE.mkdir(parents=True, exist_ok=True)
    safe = chemical_system.replace("-", "_")
    cache_path = OQMD_CACHE / f"{safe}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    if os.environ.get("OQMD_NETWORK_QUERY") != "1":
        return {
            "data": [],
            "meta": {
                "query_error": "network_query_disabled_cache_miss",
                "query": f"{OQMD_BASE}?composition={chemical_system}",
            },
        }

    params = urllib.parse.urlencode({"composition": chemical_system, "limit": limit})
    url = f"{OQMD_BASE}?{params}"
    last_error = ""
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            cache_path.write_text(json.dumps(payload), encoding="utf-8")
            time.sleep(0.2)
            return payload
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            time.sleep(min(2 * (attempt + 1), 8))
    payload = {"data": [], "meta": {"query_error": last_error, "query": url}}
    cache_path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def parse_oqmd_structure(record: dict[str, Any]) -> Structure | None:
    try:
        unit_cell = record.get("unit_cell")
        sites = record.get("sites", [])
        if not unit_cell or not sites:
            return None
        lattice = Lattice(unit_cell)
        species: list[str] = []
        coords: list[list[float]] = []
        for site in sites:
            specie, rest = str(site).split("@", 1)
            xyz = [float(value) for value in rest.split()[:3]]
            if len(xyz) != 3:
                return None
            species.append(specie.strip())
            coords.append(xyz)
        return Structure(lattice, species, coords)
    except Exception:
        return None


def reduced_formula(value: str) -> str:
    try:
        return Composition(value).reduced_formula
    except Exception:
        return str(value)


def build_oqmd_matches(matches: pd.DataFrame, alex_rows: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    matcher = StructureMatcher(
        ltol=0.2,
        stol=0.3,
        angle_tol=5,
        primitive_cell=True,
        scale=True,
        attempt_supercell=True,
    )
    alex_by_id = alex_rows.set_index("material_id")
    query_rows: list[dict[str, Any]] = []
    match_rows: list[dict[str, Any]] = []
    systems = sorted(alex_rows["chemical_system"].dropna().astype(str).unique())
    payload_by_system: dict[str, dict[str, Any]] = {}
    print(f"OQMD querying {len(systems)} chemical systems", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        future_to_system = {pool.submit(query_oqmd, system): system for system in systems}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_system), start=1):
            system = future_to_system[future]
            try:
                payload = future.result()
            except Exception as exc:  # noqa: BLE001
                payload = {"data": [], "meta": {"query_error": f"{type(exc).__name__}: {exc}"}}
            payload_by_system[system] = payload
            data = payload.get("data", [])
            meta = payload.get("meta", {})
            query_rows.append(
                {
                    "chemical_system": system,
                    "data_returned": len(data),
                    "data_available": meta.get("data_available", ""),
                    "query_error": meta.get("query_error", ""),
                }
            )
            if i % 25 == 0 or i == len(systems):
                print(f"OQMD queried {i}/{len(systems)} chemical systems", flush=True)

    for row in matches.itertuples(index=False):
        mid = str(row.material_id)
        if mid not in alex_by_id.index:
            continue
        alex = alex_by_id.loc[mid]
        try:
            candidate_structure = Structure.from_str(alex.cif, fmt="cif")
        except Exception as exc:  # noqa: BLE001
            match_rows.append(
                {
                    "material_id": mid,
                    "chemical_system": alex.chemical_system,
                    "formula": row.formula,
                    "oqmd_match_status": f"candidate_parse_error_{type(exc).__name__}",
                    "oqmd_entry_id": "",
                    "oqmd_stability": "",
                    "oqmd_stable_exact": "",
                    "mp_stable_exact": bool(row.mp_stable_exact),
                    "alex_stable_exact": bool(row.alex_stable_exact),
                    "mp_vs_oqmd_discordant": "",
                    "alex_vs_oqmd_discordant": "",
                }
            )
            continue
        target_formula = reduced_formula(str(alex.reduced_formula))
        best: dict[str, Any] | None = None
        for record in payload_by_system.get(str(alex.chemical_system), {}).get("data", []):
            if reduced_formula(str(record.get("composition", ""))) != target_formula:
                continue
            oqmd_structure = parse_oqmd_structure(record)
            if oqmd_structure is None:
                continue
            try:
                if not matcher.fit(candidate_structure, oqmd_structure):
                    continue
            except Exception:
                continue
            stability = record.get("stability", None)
            if stability is None:
                continue
            best = record
            break
        if best is None:
            match_rows.append(
                {
                    "material_id": mid,
                    "chemical_system": alex.chemical_system,
                    "formula": row.formula,
                    "oqmd_match_status": "no_strict_structure_match",
                    "oqmd_entry_id": "",
                    "oqmd_stability": "",
                    "oqmd_stable_exact": "",
                    "mp_stable_exact": bool(row.mp_stable_exact),
                    "alex_stable_exact": bool(row.alex_stable_exact),
                    "mp_vs_oqmd_discordant": "",
                    "alex_vs_oqmd_discordant": "",
                }
            )
            continue
        oqmd_stability = float(best["stability"])
        oqmd_stable = oqmd_stability <= 0.0
        match_rows.append(
            {
                "material_id": mid,
                "chemical_system": alex.chemical_system,
                "formula": row.formula,
                "oqmd_match_status": "strict_structure_match",
                "oqmd_entry_id": best.get("entry_id", ""),
                "oqmd_stability": oqmd_stability,
                "oqmd_stable_exact": oqmd_stable,
                "mp_stable_exact": bool(row.mp_stable_exact),
                "alex_stable_exact": bool(row.alex_stable_exact),
                "mp_vs_oqmd_discordant": bool(row.mp_stable_exact) != oqmd_stable,
                "alex_vs_oqmd_discordant": bool(row.alex_stable_exact) != oqmd_stable,
            }
        )
    return pd.DataFrame(match_rows), pd.DataFrame(query_rows)


def third_source_summary(matches: pd.DataFrame, oqmd: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "comparison": "MP_vs_Alex",
            "n_common": int(len(matches)),
            "discordance_rate": float(matches["discordant"].mean()),
            "claim_scope": "completed_pairwise_baseline",
        }
    ]
    exact = oqmd[oqmd["oqmd_match_status"].eq("strict_structure_match")].copy()
    for comparison, col in [
        ("MP_vs_OQMD", "mp_vs_oqmd_discordant"),
        ("Alex_vs_OQMD", "alex_vs_oqmd_discordant"),
    ]:
        n = len(exact)
        rows.append(
            {
                "comparison": comparison,
                "n_common": int(n),
                "discordance_rate": float(exact[col].astype(bool).mean()) if n else math.nan,
                "claim_scope": "completed_third_source_pair" if n >= 200 else "blocked_or_undercovered_third_source",
            }
        )
    return pd.DataFrame(rows)


def add_decomposition_columns(matches: pd.DataFrame, alex_rows: pd.DataFrame) -> pd.DataFrame:
    df = matches.merge(
        alex_rows[["material_id", "chemical_system", "num_sites", "cif"]], on="material_id", how="left"
    )
    df["mp_near_hull_25meV"] = df["mp_e_above_hull"].abs() <= NEAR_HULL_EV
    df["alex_near_hull_25meV"] = df["alex_e_above_hull"].abs() <= NEAR_HULL_EV
    df["either_near_hull_25meV"] = df["mp_near_hull_25meV"] | df["alex_near_hull_25meV"]
    df["both_near_hull_25meV"] = df["mp_near_hull_25meV"] & df["alex_near_hull_25meV"]
    df["anonymous_formula"] = df["formula"].map(lambda x: Composition(str(x)).anonymized_formula)
    df["prototype_proxy"] = df["anonymous_formula"].astype(str) + "|n=" + df["num_sites"].astype(str)
    return df


def summarize_binary(df: pd.DataFrame, mask: pd.Series, label: str) -> dict[str, Any]:
    chunk = df[mask].copy()
    return {
        "band": label,
        "n": int(len(chunk)),
        "discordant_n": int(chunk["discordant"].sum()) if len(chunk) else 0,
        "discordance_rate": float(chunk["discordant"].mean()) if len(chunk) else math.nan,
    }


def near_hull_decomposition(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            summarize_binary(df, df["both_near_hull_25meV"], "both_near_hull_25meV"),
            summarize_binary(df, df["either_near_hull_25meV"], "either_near_hull_25meV"),
            summarize_binary(df, ~df["either_near_hull_25meV"], "neither_near_hull_25meV"),
            summarize_binary(df, df["mp_near_hull_25meV"], "mp_near_hull_25meV"),
            summarize_binary(df, df["alex_near_hull_25meV"], "alex_near_hull_25meV"),
        ]
    )


def chemical_system_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for system, sdf in df.groupby("chemical_system"):
        rows.append(
            {
                "chemical_system": system,
                "n": len(sdf),
                "discordant_n": int(sdf["discordant"].sum()),
                "discordance_rate": float(sdf["discordant"].mean()),
                "near_hull_fraction": float(sdf["either_near_hull_25meV"].mean()),
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["discordant_n", "discordance_rate", "n"], ascending=[False, False, False]).head(50)


def family_flags(formula: str) -> set[str]:
    transition = {
        "Sc",
        "Ti",
        "V",
        "Cr",
        "Mn",
        "Fe",
        "Co",
        "Ni",
        "Cu",
        "Zn",
        "Y",
        "Zr",
        "Nb",
        "Mo",
        "Tc",
        "Ru",
        "Rh",
        "Pd",
        "Ag",
        "Cd",
        "Hf",
        "Ta",
        "W",
        "Re",
        "Os",
        "Ir",
        "Pt",
        "Au",
        "Hg",
    }
    lan_act = {
        "La",
        "Ce",
        "Pr",
        "Nd",
        "Pm",
        "Sm",
        "Eu",
        "Gd",
        "Tb",
        "Dy",
        "Ho",
        "Er",
        "Tm",
        "Yb",
        "Lu",
        "Ac",
        "Th",
        "Pa",
        "U",
        "Np",
        "Pu",
    }
    alkali = {"Li", "Na", "K", "Rb", "Cs", "Fr"}
    alkaline = {"Be", "Mg", "Ca", "Sr", "Ba", "Ra"}
    halogen = {"F", "Cl", "Br", "I"}
    chalcogen = {"O", "S", "Se", "Te"}
    pnictogen = {"N", "P", "As", "Sb", "Bi"}
    elements = {str(el) for el in Composition(str(formula)).elements}
    flags: set[str] = set()
    groups = [
        ("transition_metal", transition),
        ("lanthanide_actinide", lan_act),
        ("alkali", alkali),
        ("alkaline_earth", alkaline),
        ("halogen", halogen),
        ("chalcogen", chalcogen),
        ("pnictogen", pnictogen),
    ]
    for name, group in groups:
        if elements & group:
            flags.add(name)
    if not flags:
        flags.add("other")
    return flags


def element_family_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for family in sorted({fam for formula in df["formula"] for fam in family_flags(str(formula))}):
        mask = df["formula"].map(lambda formula: family in family_flags(str(formula)))
        sdf = df[mask]
        rows.append(
            {
                "element_family": family,
                "n": len(sdf),
                "discordant_n": int(sdf["discordant"].sum()),
                "discordance_rate": float(sdf["discordant"].mean()),
                "near_hull_fraction": float(sdf["either_near_hull_25meV"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["discordant_n", "discordance_rate"], ascending=[False, False])


def prototype_proxy_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for proto, sdf in df.groupby("prototype_proxy"):
        rows.append(
            {
                "prototype_proxy": proto,
                "n": len(sdf),
                "discordant_n": int(sdf["discordant"].sum()),
                "discordance_rate": float(sdf["discordant"].mean()),
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values(["discordant_n", "discordance_rate", "n"], ascending=[False, False, False])
        .head(50)
    )


def wbm_alex_case_comparison(route_b: pd.DataFrame) -> pd.DataFrame:
    minimal = pd.read_csv(OUT / "table_minimal_discordance_probe.csv").iloc[0]
    select_top = pd.read_csv(OUT / "table_selection_conditional_top_decile_summary.csv")
    rows = [
        {
            "case": "WBM_vs_alex_existing_probe",
            "n_common": int(minimal["matched_n"]),
            "discordance_rate": float(minimal["discordance_rate"]),
            "role": "case_analysis_high_discordance_source_selection_specific",
        },
        {
            "case": "MP_vs_alex_route_b_full_snapshot",
            "n_common": int(len(route_b)),
            "discordance_rate": float(route_b["discordant"].mean()),
            "role": "full_snapshot_pairwise_baseline",
        },
    ]
    for row in select_top.itertuples(index=False):
        rows.append(
            {
                "case": f"MP_vs_alex_top_decile_{row.model}",
                "n_common": int(row.top_n),
                "discordance_rate": float(row.top_decile_discordance),
                "role": "selection_conditional_no_go_core_result",
            }
        )
    return pd.DataFrame(rows)


def write_closeout(third: pd.DataFrame, near: pd.DataFrame, case: pd.DataFrame) -> None:
    third_lines = third.to_csv(index=False).strip()
    near_lines = near.to_csv(index=False).strip()
    case_lines = case.to_csv(index=False).strip()
    text = f"""# Third-Source and Discordance-Decomposition Diagnostics

## Scope

This milestone extends the MP-vs-Alex full-snapshot diagnostic with two checks:

1. a third-source OQMD exact-structure attempt; and
2. decomposition of MP-vs-Alex discordance by hull proximity, chemistry family
   and prototype proxy.

No new DFT, training or model fitting is used. OQMD rows are never promoted to a
three-source conclusion unless exact-structure coverage reaches the predeclared
`n_common >= 200` scale.

## Third-Source Result

```csv
{third_lines}
```

If the OQMD common denominator is undercovered, the paper role is a data-access
or source-coverage boundary, not a completed third-source measurement.

## Near-Hull Decomposition

```csv
{near_lines}
```

This is the main completed decomposition result: MP-vs-Alex discordance is
higher near the hull than away from the hull. It refines the conclusion from a
single baseline discordance number into a localized label-boundary phenomenon.

## Case-Analysis Contrast

```csv
{case_lines}
```

The earlier WBM-vs-alex/PARC-style high-discordance probe is retained as a case
analysis. It is not used as the full-snapshot baseline.
"""
    (OUT / "THIRD_SOURCE_AND_DISCORDANCE_DECOMPOSITION_CLOSEOUT.md").write_text(text, encoding="utf-8")


def main() -> None:
    matches = load_route_b_matches()
    alex_rows = load_alex_rows(set(matches["material_id"].astype(str)))
    oqmd_matches, oqmd_queries = build_oqmd_matches(matches, alex_rows)
    decomposed = add_decomposition_columns(matches, alex_rows)

    third = third_source_summary(matches, oqmd_matches)
    near = near_hull_decomposition(decomposed)
    chem = chemical_system_summary(decomposed)
    families = element_family_summary(decomposed)
    prototypes = prototype_proxy_summary(decomposed)
    case = wbm_alex_case_comparison(matches)

    oqmd_matches.to_csv(OUT / "table_mp_alex_oqmd_exact_matches.csv", index=False)
    oqmd_queries.to_csv(OUT / "table_oqmd_query_coverage.csv", index=False)
    third.to_csv(OUT / "table_third_source_triangle_summary.csv", index=False)
    near.to_csv(OUT / "table_discordance_near_hull_decomposition.csv", index=False)
    chem.to_csv(OUT / "table_discordance_chemical_system_top.csv", index=False)
    families.to_csv(OUT / "table_discordance_element_family.csv", index=False)
    prototypes.to_csv(OUT / "table_discordance_prototype_proxy.csv", index=False)
    case.to_csv(OUT / "table_wbm_alex_case_comparison.csv", index=False)
    write_closeout(third, near, case)
    write_manifest()
    print("Wrote third-source/decomposition diagnostics", flush=True)


if __name__ == "__main__":
    main()
