#!/usr/bin/env python3
"""Audit the M1 all-view common-support cohort against the archived D5 cohort.

The primary M1 comparison retains rows with all five label-only views and the
four predicted-hull rankings.  This script makes the selection from D2 through
D5 to M1 explicit and compares retained and excluded D5 rows using chemistry,
formula complexity, hull distance, endpoint discordance and model-score ranks.
All quantities are regenerated from row-level tables.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from pymatgen.core import Composition
from scipy.spatial.distance import jensenshannon


ROOT = Path(__file__).resolve().parents[1]
PHASE1 = ROOT / "outputs" / "phase1_v2"
REPAIRED = ROOT / "outputs" / "repaired_model_evaluation_v1"
RAW_SCORES = ROOT / "inputs" / "phase2_v1" / "sourceaware_model_scores_public_safe.parquet"
REAL_MODELS = ("ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP")
VIEWS = ("mp_native", "alexmp20_native", "alex_pbe_native", "common_pool", "audit_view")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=ROOT / "outputs" / "evidence_strengthening_v1" / "complete_case_audit")
    p.add_argument("--legacy-structure-audit", type=Path, default=Path("/home/waas/paper_experiments/github/materials-stability-label-discordance/outputs/milestones/materials_label_discordance_full_mp_alex_43984/table_full_mp_alex_structure_matches.csv"))
    return p.parse_args()


def _formula_features(formula: str) -> tuple[int, int, str]:
    try:
        comp = Composition(str(formula))
        return int(round(comp.num_atoms)), len(comp.elements), comp.reduced_formula
    except Exception:
        return 0, 0, str(formula)


def _wide_labels(labels: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for view in VIEWS:
        x = labels.loc[labels["label_view"].eq(view), ["row_id", "label", "is_evaluable"]].drop_duplicates("row_id")
        x = x.rename(columns={"label": view, "is_evaluable": f"{view}_evaluable"})
        rows.append(x.set_index("row_id"))
    energies = labels.loc[labels["label_view"].eq("mp_native"), [
        "row_id", "source_native_mp_ehull", "source_native_mattergen_ehull",
        "source_native_alexandria_ehull", "common_pool_mp_ehull",
        "common_pool_alexandria_ehull",
    ]].drop_duplicates("row_id").set_index("row_id")
    return pd.concat(rows + [energies], axis=1)


def _score_percentiles() -> pd.DataFrame:
    raw = pd.read_parquet(RAW_SCORES)
    raw = raw.loc[raw["model"].isin(REAL_MODELS), ["row_id", "model", "score"]].copy()
    raw["score_percentile"] = raw.groupby("model", sort=False)["score"].rank(pct=True, method="average")
    return raw.pivot(index="row_id", columns="model", values="score_percentile").rename(columns=lambda c: f"{c}_score_percentile")


def _structure_sites(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["mp_id", "num_sites"])
    x = pd.read_csv(path, usecols=["material_id", "num_sites"])
    x = x.rename(columns={"material_id": "mp_id"}).drop_duplicates("mp_id")
    x["num_sites"] = pd.to_numeric(x["num_sites"], errors="coerce")
    return x


def build_frame(legacy_structure_audit: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    d2 = pd.read_parquet(PHASE1 / "denominator_d2_triple_single_match.parquet")
    d5 = pd.read_parquet(PHASE1 / "denominator_d5_model_complete.parquet")
    fixed = pd.read_parquet(REPAIRED / "fixed_support" / "denominator_all_view_common_support.parquet")
    labels = _wide_labels(pd.read_parquet(PHASE1 / "labels_by_view.parquet"))
    # D5 already carries the D2 identifiers.  The explicit join keeps this
    # script compatible with earlier D5 exports that only stored ``row_id``.
    d2_meta = d2[["row_id", "mp_id", "formula", "reduced_formula", "chemical_system"]].set_index("row_id")
    base = d5.copy().set_index("row_id")
    for col in d2_meta.columns:
        if col not in base.columns:
            base[col] = d2_meta[col]
        else:
            base[col] = base[col].where(base[col].notna(), d2_meta[col])
    base = base.reset_index()
    base = base.join(labels, on="row_id").join(_score_percentiles(), on="row_id")
    base = base.merge(_structure_sites(legacy_structure_audit), on="mp_id", how="left")
    features = base["formula"].map(_formula_features)
    base[["formula_atom_count", "formula_element_count", "reduced_formula_from_formula"]] = pd.DataFrame(features.tolist(), index=base.index)
    base["in_m1_all_view_common_support"] = base["row_id"].isin(set(fixed["row_id"].astype(str)))
    base["all_five_label_views_evaluable"] = base[[f"{view}_evaluable" for view in VIEWS]].fillna(False).all(axis=1)
    base["mp_vs_alexmp20_switch"] = base["mp_native"].astype("boolean") != base["alexmp20_native"].astype("boolean")
    base["mp_vs_alex_pbe_switch"] = base["mp_native"].astype("boolean") != base["alex_pbe_native"].astype("boolean")
    base["alexmp20_vs_alex_pbe_switch"] = base["alexmp20_native"].astype("boolean") != base["alex_pbe_native"].astype("boolean")
    base["any_native_switch"] = base[["mp_vs_alexmp20_switch", "mp_vs_alex_pbe_switch", "alexmp20_vs_alex_pbe_switch"]].any(axis=1)
    return d2, base


def _standardized_difference(a: pd.Series, b: pd.Series) -> float:
    a = pd.to_numeric(a, errors="coerce").dropna()
    b = pd.to_numeric(b, errors="coerce").dropna()
    if not len(a) or not len(b):
        return np.nan
    pooled = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    return float((a.mean() - b.mean()) / pooled) if pooled else np.nan


def numeric_comparison(frame: pd.DataFrame) -> pd.DataFrame:
    retained = frame.loc[frame["in_m1_all_view_common_support"]]
    excluded = frame.loc[~frame["in_m1_all_view_common_support"]]
    metrics: Iterable[tuple[str, str]] = [
        ("formula_atom_count", "Formula atom count"),
        ("formula_element_count", "Formula element count"),
        ("num_sites", "Structure site count"),
        ("source_native_mp_ehull", "MP-native hull distance (eV atom-1)"),
        ("source_native_mattergen_ehull", "alex-mp-20 hull distance (eV atom-1)"),
        ("source_native_alexandria_ehull", "Alexandria-PBE hull distance (eV atom-1)"),
        ("common_pool_mp_ehull", "MP common-pool hull distance (eV atom-1)"),
        ("common_pool_alexandria_ehull", "Alexandria common-pool hull distance (eV atom-1)"),
    ] + [(f"{m}_score_percentile", f"{m} score percentile") for m in REAL_MODELS]
    rows = []
    for col, label in metrics:
        a, b = retained[col], excluded[col]
        rows.append({
            "feature": col, "feature_label": label,
            "retained_n": int(a.notna().sum()), "excluded_n": int(b.notna().sum()),
            "retained_mean": float(pd.to_numeric(a, errors="coerce").mean()),
            "excluded_mean": float(pd.to_numeric(b, errors="coerce").mean()),
            "retained_median": float(pd.to_numeric(a, errors="coerce").median()),
            "excluded_median": float(pd.to_numeric(b, errors="coerce").median()),
            "retained_minus_excluded": float(pd.to_numeric(a, errors="coerce").mean() - pd.to_numeric(b, errors="coerce").mean()),
            "standardized_mean_difference": _standardized_difference(a, b),
        })
    return pd.DataFrame(rows)


def binary_comparison(frame: pd.DataFrame) -> pd.DataFrame:
    retained = frame.loc[frame["in_m1_all_view_common_support"]]
    excluded = frame.loc[~frame["in_m1_all_view_common_support"]]
    fields = [*VIEWS, "mp_vs_alexmp20_switch", "mp_vs_alex_pbe_switch", "alexmp20_vs_alex_pbe_switch", "any_native_switch"]
    rows = []
    for col in fields:
        a = retained[col].astype("boolean")
        b = excluded[col].astype("boolean")
        a_rate = a.mean()
        b_rate = b.mean()
        rows.append({
            "feature": col,
            "retained_n": int(a.notna().sum()), "excluded_n": int(b.notna().sum()),
            "retained_rate": float(a_rate) if pd.notna(a_rate) else np.nan,
            "excluded_rate": float(b_rate) if pd.notna(b_rate) else np.nan,
            "retained_minus_excluded": float(a_rate - b_rate) if pd.notna(a_rate) and pd.notna(b_rate) else np.nan,
        })
    return pd.DataFrame(rows)


def chemistry_comparison(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    retained = frame.loc[frame["in_m1_all_view_common_support"]].copy()
    excluded = frame.loc[~frame["in_m1_all_view_common_support"]].copy()
    systems = sorted(set(retained["chemical_system"]) | set(excluded["chemical_system"]))
    a = retained["chemical_system"].value_counts().reindex(systems, fill_value=0).to_numpy(float)
    b = excluded["chemical_system"].value_counts().reindex(systems, fill_value=0).to_numpy(float)
    jsd = float(jensenshannon(a / a.sum(), b / b.sum(), base=2.0))
    all_elements = sorted({el for v in frame["chemical_system"].dropna() for el in str(v).split("-") if el})
    rows = []
    for el in all_elements:
        ra = retained["chemical_system"].str.split("-").map(lambda xs: el in xs if isinstance(xs, list) else False).mean()
        rb = excluded["chemical_system"].str.split("-").map(lambda xs: el in xs if isinstance(xs, list) else False).mean()
        rows.append({"element": el, "retained_fraction": float(ra), "excluded_fraction": float(rb), "retained_minus_excluded": float(ra-rb), "absolute_difference": float(abs(ra-rb))})
    elements = pd.DataFrame(rows).sort_values("absolute_difference", ascending=False, kind="mergesort")
    top = pd.DataFrame({"chemical_system": systems, "retained_n": a.astype(int), "excluded_n": b.astype(int)})
    top["retained_fraction"] = top["retained_n"] / len(retained)
    top["excluded_fraction"] = top["excluded_n"] / len(excluded)
    top["retained_minus_excluded"] = top["retained_fraction"] - top["excluded_fraction"]
    top = top.reindex(top["retained_minus_excluded"].abs().sort_values(ascending=False).index)
    summary = {
        "retained_chemical_system_n": int(retained["chemical_system"].nunique()),
        "excluded_chemical_system_n": int(excluded["chemical_system"].nunique()),
        "union_chemical_system_n": int(len(systems)),
        "chemical_system_jensen_shannon_distance_base2": jsd,
    }
    return elements, top, summary


def write_summary(d2: pd.DataFrame, frame: pd.DataFrame, chemistry: dict, out: Path) -> None:
    m1_n = int(frame["in_m1_all_view_common_support"].sum())
    summary = {
        "D2_three_source_exact_rows": int(len(d2)),
        "D5_archived_four_score_rows": int(len(frame)),
        "M1_all_view_common_support_rows": m1_n,
        "D5_excluded_from_M1_rows": int(len(frame)-m1_n),
        "all_five_label_views_evaluable_rows_in_D5": int(frame["all_five_label_views_evaluable"].sum()),
        **chemistry,
        "definition": "M1 is the intersection of the archived D5 four-score cohort with evaluable MP-native, alex-mp-20-native, Alexandria-PBE-native, common-pool and audit-view labels.",
    }
    (out / "complete_case_selection_summary.json").write_text(json.dumps(summary, indent=2) + "\n")


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    d2, frame = build_frame(args.legacy_structure_audit)
    elements, systems, chemistry = chemistry_comparison(frame)
    frame.to_parquet(args.out / "d5_to_m1_row_audit.parquet", index=False)
    frame.drop(columns=[c for c in frame.columns if c.endswith("_score_percentile")]).to_csv(args.out / "d5_to_m1_row_audit.csv", index=False)
    numeric_comparison(frame).to_csv(args.out / "d5_to_m1_numeric_comparison.csv", index=False)
    binary_comparison(frame).to_csv(args.out / "d5_to_m1_label_and_conflict_comparison.csv", index=False)
    elements.to_csv(args.out / "d5_to_m1_element_comparison.csv", index=False)
    systems.head(100).to_csv(args.out / "d5_to_m1_chemical_system_comparison_top100.csv", index=False)
    pd.DataFrame([
        {"stage": "D2 three-source exact denominator", "n": len(d2), "selection_rule": "single strict MP--alex-mp-20--Alexandria-PBE structure match"},
        {"stage": "D5 archived four-score cohort", "n": len(frame), "selection_rule": "four archived raw model score tables available"},
        {"stage": "M1 all-view common support", "n": int(frame["in_m1_all_view_common_support"].sum()), "selection_rule": "D5 rows with five evaluable label-only views and corrected predicted-hull rankings"},
    ]).to_csv(args.out / "d2_d5_m1_support_flow.csv", index=False)
    write_summary(d2, frame, chemistry, args.out)
    print(f"wrote complete-case selection audit to {args.out}")


if __name__ == "__main__":
    main()
