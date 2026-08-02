#!/usr/bin/env python3
"""Audit selection from the frozen compound candidate batch into Mphys."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "referee_revision_v3" / "mphys_support_exclusion_audit"
V3 = ROOT / "outputs" / "referee_revision_v3"
OLD = ROOT / "outputs" / "evidence_strengthening_v1" / "complete_case_audit"

TRANSITION = {
    "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
    "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
    "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
}
LANTHANIDE = {
    "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy",
    "Ho", "Er", "Tm", "Yb", "Lu",
}
HALOGEN = {"F", "Cl", "Br", "I"}


def flag(elements: list[str], family: set[str]) -> bool:
    return bool(set(elements) & family)


def summarise(frame: pd.DataFrame, group: str) -> list[dict]:
    rows: list[dict] = []
    n = len(frame)
    for label, column in (
        ("MP source-coordinate stable fraction", "mp_native"),
        ("alex-mp-20 source-coordinate stable fraction", "alexmp20_native"),
        ("Alexandria-PBE source-coordinate stable fraction", "alex_pbe_native"),
        ("MP matched-pool stable fraction", "common_pool_mp_label"),
        ("Alexandria-PBE matched-pool stable fraction", "common_pool_alexandria_label"),
    ):
        observed = frame[column].dropna()
        rows.append({
            "group": group, "feature": label, "feature_kind": "stable_fraction",
            "n_group": n, "n_evaluable": int(observed.size),
            "value": float(observed.mean()) if observed.size else np.nan,
            "unit": "fraction", "statistic": "mean",
        })
    for label, column in (
        ("Formula element count", "formula_element_count"),
        ("Formula atom count", "formula_atom_count"),
        ("Structure site count", "num_sites"),
        ("Reference-hull phase count after target exclusion", "reference_hull_phase_n_after_exclusion"),
    ):
        observed = frame[column].dropna()
        rows.append({
            "group": group, "feature": label, "feature_kind": "numeric_mean",
            "n_group": n, "n_evaluable": int(observed.size),
            "value": float(observed.mean()) if observed.size else np.nan,
            "unit": "count", "statistic": "mean",
        })
    for label, column in (
        ("Transition-metal-containing", "has_transition_metal"),
        ("Lanthanide-containing", "has_lanthanide"),
        ("Oxygen-containing", "has_oxygen"),
        ("Halogen-containing", "has_halogen"),
    ):
        rows.append({
            "group": group, "feature": label, "feature_kind": "composition_fraction",
            "n_group": n, "n_evaluable": n, "value": float(frame[column].mean()),
            "unit": "fraction", "statistic": "mean",
        })
    return rows


def latex_pct(value: float) -> str:
    return "--" if pd.isna(value) else f"{100 * value:.1f}\\%"


def latex_mean(value: float) -> str:
    return "--" if pd.isna(value) else f"{value:.2f}"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    candidate = pd.read_parquet(V3 / "candidate_pool_manifest.parquet")
    candidate = candidate[candidate.ranking_eligible].copy()
    support = pd.read_parquet(V3 / "evaluation" / "mphys_fixed_support.parquet")
    historic = pd.read_parquet(OLD / "d5_to_m1_row_audit.parquet")
    historic = historic.drop_duplicates("row_id")
    loso = pd.read_parquet(V3 / "loso_exclusion_audit_mace_mp.parquet")
    loso = loso.rename(columns={"candidate_row_id": "row_id"})

    keep = [
        "row_id", "mp_native", "alexmp20_native", "alex_pbe_native", "num_sites",
        "formula_atom_count", "formula_element_count", "source_native_mp_ehull",
        "source_native_mattergen_ehull", "source_native_alexandria_ehull",
        "common_pool_mp_ehull", "common_pool_alexandria_ehull",
    ]
    labels = historic[keep].copy()
    labels["common_pool_mp_label"] = labels.common_pool_mp_ehull.le(1e-8).where(
        labels.common_pool_mp_ehull.notna()
    )
    labels["common_pool_alexandria_label"] = labels.common_pool_alexandria_ehull.le(1e-8).where(
        labels.common_pool_alexandria_ehull.notna()
    )
    audit = candidate.merge(labels, on="row_id", how="left", validate="one_to_one")
    audit = audit.merge(
        loso[["row_id", "reference_hull_phase_n_after_exclusion"]],
        on="row_id", how="left", validate="one_to_one",
    )
    audit["in_mphys"] = audit.row_id.isin(set(support.row_id))
    if int(audit.in_mphys.sum()) != len(support):
        raise RuntimeError("Mphys membership does not match fixed support")
    audit["elements"] = audit.elements_json.map(json.loads)
    audit["has_transition_metal"] = audit.elements.map(lambda x: flag(x, TRANSITION))
    audit["has_lanthanide"] = audit.elements.map(lambda x: flag(x, LANTHANIDE))
    audit["has_oxygen"] = audit.elements.map(lambda x: "O" in x)
    audit["has_halogen"] = audit.elements.map(lambda x: flag(x, HALOGEN))
    audit["group"] = np.where(audit.in_mphys, "Mphys retained", "candidate excluded")

    retained = audit[audit.in_mphys].copy()
    excluded = audit[~audit.in_mphys].copy()
    if (len(retained), len(excluded)) != (36_650, 31):
        raise RuntimeError((len(retained), len(excluded)))

    summary = pd.DataFrame(summarise(retained, "Mphys retained") + summarise(excluded, "candidate excluded"))

    system_rows = []
    all_systems = set(audit.chemical_system)
    retained_systems = set(retained.chemical_system)
    excluded_systems = set(excluded.chemical_system)
    for group, frame, systems in (
        ("Mphys retained", retained, retained_systems),
        ("candidate excluded", excluded, excluded_systems),
    ):
        system_rows.append({
            "group": group, "row_n": len(frame), "unique_chemical_system_n": len(systems),
            "chemical_system_coverage_of_candidate_universe": len(systems) / len(all_systems),
            "systems_shared_with_other_group_n": len(systems & (excluded_systems if group == "Mphys retained" else retained_systems)),
            "systems_unique_to_group_n": len(systems - (excluded_systems if group == "Mphys retained" else retained_systems)),
        })
    systems = pd.DataFrame(system_rows)
    systems.to_csv(OUT / "mphys_retained_excluded_chemical_system_coverage.csv", index=False)
    system_summary = pd.concat([
        systems.rename(columns={"row_n": "n_group", "unique_chemical_system_n": "value"})[
            ["group", "n_group", "value"]
        ].assign(
            feature="Unique chemical-system count", feature_kind="numeric_mean",
            n_evaluable=lambda x: x.n_group, unit="count", statistic="count",
        ),
        systems.rename(columns={"row_n": "n_group", "chemical_system_coverage_of_candidate_universe": "value"})[
            ["group", "n_group", "value"]
        ].assign(
            feature="Chemical-system coverage of candidate universe", feature_kind="composition_fraction",
            n_evaluable=lambda x: x.n_group, unit="fraction", statistic="fraction",
        ),
    ], ignore_index=True)
    summary = pd.concat([summary, system_summary[summary.columns]], ignore_index=True)
    summary.to_csv(OUT / "mphys_retained_excluded_summary.csv", index=False)

    element_rows = []
    for group, frame in (("Mphys retained", retained), ("candidate excluded", excluded)):
        for element in sorted({element for values in audit.elements for element in values}):
            element_rows.append({
                "group": group, "element": element, "row_n": len(frame),
                "element_row_fraction": float(frame.elements.map(lambda x: element in x).mean()),
            })
    pd.DataFrame(element_rows).to_csv(OUT / "mphys_retained_excluded_element_distribution.csv", index=False)

    audit.drop(columns="elements").to_parquet(OUT / "mphys_retained_excluded_row_audit.parquet", index=False)
    audit.drop(columns="elements").to_csv(OUT / "mphys_retained_excluded_row_audit.csv", index=False)

    pivot = summary.pivot(index="feature", columns="group", values="value")
    evaluator = summary.pivot(index="feature", columns="group", values="n_evaluable")
    order = [
        "MP source-coordinate stable fraction", "alex-mp-20 source-coordinate stable fraction",
        "Alexandria-PBE source-coordinate stable fraction", "MP matched-pool stable fraction",
        "Alexandria-PBE matched-pool stable fraction", "Formula element count", "Formula atom count",
        "Structure site count", "Reference-hull phase count after target exclusion",
        "Unique chemical-system count", "Chemical-system coverage of candidate universe",
        "Transition-metal-containing", "Lanthanide-containing", "Oxygen-containing", "Halogen-containing",
    ]
    kind = summary.drop_duplicates("feature").set_index("feature").feature_kind
    lines = [
        "% Generated by build_mphys_support_exclusion_audit.py; do not edit.\n",
        "\\begin{table*}[!t]\n\\centering\n",
        "\\caption{Retained/excluded audit for the fixed physical-endpoint cohort. Candidate exclusions are the 31 compound rows without all five physical coordinates; they differ in coordinate availability and composition. Stable fractions use available coordinates, with the evaluable row count shown in parentheses for matched-pool coordinates. Reference-hull phase count is measured after target-equivalence-class exclusion.}\n",
        "\\label{tab:mphys-exclusion-audit}\n\\small\n",
        "\\begin{tabular}{@{}lrr@{}}\n\\toprule\nFeature & $M_{\\mathrm{phys}}$ retained ($n=36{,}650$) & Candidate excluded ($n=31$) \\\\ \n\\midrule\n",
    ]
    for feature in order:
        left, right = pivot.loc[feature, "Mphys retained"], pivot.loc[feature, "candidate excluded"]
        if kind.loc[feature] in {"stable_fraction", "composition_fraction"}:
            lval, rval = latex_pct(left), latex_pct(right)
        else:
            lval, rval = latex_mean(left), latex_mean(right)
        if feature in {"MP matched-pool stable fraction", "Alexandria-PBE matched-pool stable fraction"}:
            lval += f" ({int(evaluator.loc[feature, 'Mphys retained']):,})"
            rval += f" ({int(evaluator.loc[feature, 'candidate excluded']):,})"
        lines.append(f"{feature} & {lval} & {rval} \\\\ \n")
    lines += ["\\bottomrule\n\\end{tabular}\n\\end{table*}\n"]
    (OUT / "table_mphys_retained_excluded.tex").write_text("".join(lines), encoding="utf-8")

    metadata = {
        "candidate_compound_n": len(audit), "mphys_retained_n": len(retained),
        "candidate_excluded_n": len(excluded),
        "candidate_universe_chemical_system_n": len(all_systems),
        "definition": "Mphys support is formed after four rankings and five physical coordinates are frozen.",
    }
    (OUT / "mphys_retained_excluded_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
