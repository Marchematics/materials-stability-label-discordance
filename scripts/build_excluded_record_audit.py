#!/usr/bin/env python3
"""Build an excluded-record audit for the MP--alex-mp-20 strict-match denominator.

The audit uses only the committed full-denominator table. It compares retained
strict structure matches with MP-query gaps and strict structure mismatches
using descriptors already present in that table.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "outputs/milestones/materials_label_discordance_full_mp_alex_43984/table_full_mp_alex_structure_matches.csv"
OUT_DIR = ROOT / "outputs/milestones/benchmark_reliability_enhancement"
OUT = OUT_DIR / "table_excluded_record_audit.csv"

HALOGENS = {"F", "Cl", "Br", "I"}
LANTHANIDES = {"La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"}
TRANSITION_METALS = {
    "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
    "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
    "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
}
ALKALI = {"Li", "Na", "K", "Rb", "Cs", "Fr"}
ALKALINE_EARTH = {"Be", "Mg", "Ca", "Sr", "Ba", "Ra"}
CHALCOGENS = {"O", "S", "Se", "Te", "Po"}


def elements(chemical_system: str) -> set[str]:
    if not isinstance(chemical_system, str) or not chemical_system:
        return set()
    return set(chemical_system.split("-"))


def family_flags(elts: set[str]) -> dict[str, bool]:
    return {
        "contains_oxygen": "O" in elts,
        "contains_halogen": bool(elts & HALOGENS),
        "contains_lanthanide": bool(elts & LANTHANIDES),
        "contains_transition_metal": bool(elts & TRANSITION_METALS),
        "contains_alkali": bool(elts & ALKALI),
        "contains_alkaline_earth": bool(elts & ALKALINE_EARTH),
        "contains_chalcogen": bool(elts & CHALCOGENS),
    }


def main() -> None:
    df = pd.read_csv(IN)
    df["alex_stable_exact_bool"] = df["alex_stable_exact"].astype(str).str.lower().eq("true")
    df["element_set"] = df["chemical_system"].map(elements)
    df["n_elements"] = df["element_set"].map(len)
    for key in family_flags(set()):
        df[key] = df["element_set"].map(lambda xs, key=key: family_flags(xs)[key])

    rows: list[dict[str, object]] = []
    for status, group in df.groupby("match_status", sort=False):
        row: dict[str, object] = {
            "match_status": status,
            "n": int(len(group)),
            "fraction_of_alex_mp_id_rows": float(len(group) / len(df)),
            "alex_stable_rate": float(group["alex_stable_exact_bool"].mean()),
            "median_num_sites": float(group["num_sites"].median()),
            "median_n_elements": float(group["n_elements"].median()),
            "top_chemical_systems": ";".join(group["chemical_system"].value_counts().head(5).index.tolist()),
        }
        for key in family_flags(set()):
            row[f"{key}_fraction"] = float(group[key].mean())
        rows.append(row)

    out = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
