from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd
from scipy.stats import beta


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "milestones" / "materials_label_discordance_preregistration"
MATCHES = OUT / "table_route_b_full_snapshot_matches.csv"
SCORES = OUT / "table_route_b_full_snapshot_model_scores.csv"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(path: Path, root: Path) -> None:
    ignored_suffixes = {
        ".aux",
        ".bbl",
        ".blg",
        ".fdb_latexmk",
        ".fls",
        ".log",
        ".out",
        ".synctex.gz",
        ".toc",
    }
    rows = []
    for item in sorted(root.rglob("*")):
        if not item.is_file() or item.name == path.name:
            continue
        if item.name == ".DS_Store" or ".git" in item.parts or "__pycache__" in item.parts:
            continue
        if "template_official" in item.parts and "sn-article-template" in item.parts:
            continue
        if ".pytest_cache" in item.parts:
            continue
        if any(str(item).endswith(suffix) for suffix in ignored_suffixes):
            continue
        rows.append(f"{sha256_file(item)}  {item.relative_to(root)}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def exact_binomial_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if n == 0:
        return math.nan, math.nan
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def load_matches() -> pd.DataFrame:
    df = pd.read_csv(MATCHES)
    df = df[df["match_status"].eq("strict_structure_match")].copy()
    df["mp_e_above_hull"] = pd.to_numeric(df["mp_e_above_hull"])
    df["alex_e_above_hull"] = pd.to_numeric(df["alex_e_above_hull"])
    df["mp_stable_exact"] = df["mp_stable_exact"].astype(str).str.lower().eq("true")
    df["alex_stable_exact"] = df["alex_stable_exact"].astype(str).str.lower().eq("true")
    df["discordant"] = df["mp_stable_exact"] != df["alex_stable_exact"]
    df["delta_e_mev"] = 1000.0 * (df["mp_e_above_hull"] - df["alex_e_above_hull"])
    df["abs_delta_e_mev"] = df["delta_e_mev"].abs()
    df["min_abs_e_mev"] = 1000.0 * df[["mp_e_above_hull", "alex_e_above_hull"]].abs().min(axis=1)
    df["max_abs_e_mev"] = 1000.0 * df[["mp_e_above_hull", "alex_e_above_hull"]].abs().max(axis=1)
    df["mean_signed_e_mev"] = 500.0 * (df["mp_e_above_hull"] + df["alex_e_above_hull"])
    df["mean_abs_e_mev"] = 500.0 * (df["mp_e_above_hull"].abs() + df["alex_e_above_hull"].abs())
    return df


def summarize_mask(df: pd.DataFrame, mask: pd.Series) -> dict[str, Any]:
    n = int(mask.sum())
    k = int(df.loc[mask, "discordant"].sum()) if n else 0
    ci_lo, ci_hi = exact_binomial_ci(k, n)
    return {
        "n": n,
        "discordant_n": k,
        "discordance_rate": k / n if n else math.nan,
        "ci95_lo": ci_lo,
        "ci95_hi": ci_hi,
    }


def delta_e_binned_discordance(df: pd.DataFrame) -> pd.DataFrame:
    edges = [0.0, 5.0, 10.0, 25.0, 50.0, 100.0, math.inf]
    labels = ["0-5", "5-10", "10-25", "25-50", "50-100", ">=100"]
    rows = []
    total_discordant = int(df["discordant"].sum())
    for lo, hi, label in zip(edges[:-1], edges[1:], labels, strict=True):
        values = df["abs_delta_e_mev"]
        mask = values.ge(lo) if math.isinf(hi) else values.ge(lo) & values.lt(hi)
        row = summarize_mask(df, mask)
        chunk = df[mask]
        row.update(
            {
                "abs_delta_e_bin_mev": label,
                "bin_start_mev": lo,
                "bin_end_mev": hi,
                "population_fraction": row["n"] / len(df),
                "discordant_capture_fraction": row["discordant_n"] / total_discordant
                if total_discordant
                else math.nan,
                "concordant_n": row["n"] - row["discordant_n"],
                "median_abs_delta_e_mev": float(chunk["abs_delta_e_mev"].median()) if row["n"] else math.nan,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)[
        [
            "abs_delta_e_bin_mev",
            "bin_start_mev",
            "bin_end_mev",
            "n",
            "population_fraction",
            "discordant_n",
            "concordant_n",
            "discordance_rate",
            "ci95_lo",
            "ci95_hi",
            "discordant_capture_fraction",
            "median_abs_delta_e_mev",
        ]
    ]


def delta_e_quantiles(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    groups = {
        "all": df,
        "concordant": df[~df["discordant"]],
        "discordant": df[df["discordant"]],
    }
    quantiles = [0, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 1.0]
    for label, chunk in groups.items():
        row: dict[str, Any] = {
            "group": label,
            "n": int(len(chunk)),
            "mean_abs_delta_e_mev": float(chunk["abs_delta_e_mev"].mean()) if len(chunk) else math.nan,
        }
        for q in quantiles:
            row[f"q{int(q * 100):02d}_abs_delta_e_mev"] = (
                float(chunk["abs_delta_e_mev"].quantile(q)) if len(chunk) else math.nan
            )
        rows.append(row)
    return pd.DataFrame(rows)


def delta_e_tail_thresholds(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total_discordant = int(df["discordant"].sum())
    for threshold in [1, 2, 5, 10, 15, 20, 25, 30, 40, 50, 75, 100]:
        mask = df["abs_delta_e_mev"].ge(threshold)
        row = summarize_mask(df, mask)
        row.update(
            {
                "abs_delta_e_threshold_mev": threshold,
                "tail_population_fraction": row["n"] / len(df),
                "discordant_capture_fraction": row["discordant_n"] / total_discordant
                if total_discordant
                else math.nan,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)[
        [
            "abs_delta_e_threshold_mev",
            "n",
            "tail_population_fraction",
            "discordant_n",
            "discordance_rate",
            "ci95_lo",
            "ci95_hi",
            "discordant_capture_fraction",
        ]
    ]


def boundary_definition_robustness(df: pd.DataFrame) -> pd.DataFrame:
    definitions = {
        "either_source_min_abs": df["min_abs_e_mev"],
        "both_sources_max_abs": df["max_abs_e_mev"],
        "mp_reference_abs": 1000.0 * df["mp_e_above_hull"].abs(),
        "alexandria_reference_abs": 1000.0 * df["alex_e_above_hull"].abs(),
        "mean_source_abs": df["mean_abs_e_mev"],
    }
    rows = []
    total_discordant = int(df["discordant"].sum())
    for threshold in [10, 25, 50, 100]:
        for name, values in definitions.items():
            mask = values.le(threshold)
            inside = summarize_mask(df, mask)
            outside_mask = ~mask
            outside = summarize_mask(df, outside_mask)
            rows.append(
                {
                    "definition": name,
                    "threshold_mev": threshold,
                    "flag_n": inside["n"],
                    "flag_fraction": inside["n"] / len(df),
                    "flagged_discordant_n": inside["discordant_n"],
                    "flagged_discordance_rate": inside["discordance_rate"],
                    "flagged_ci95_lo": inside["ci95_lo"],
                    "flagged_ci95_hi": inside["ci95_hi"],
                    "discordant_capture_fraction": inside["discordant_n"] / total_discordant
                    if total_discordant
                    else math.nan,
                    "flagged_concordant_n": inside["n"] - inside["discordant_n"],
                    "flag_false_alarm_fraction": (inside["n"] - inside["discordant_n"]) / inside["n"]
                    if inside["n"]
                    else math.nan,
                    "outside_n": outside["n"],
                    "outside_discordant_n": outside["discordant_n"],
                    "outside_discordance_rate": outside["discordance_rate"],
                    "outside_ci95_lo": outside["ci95_lo"],
                    "outside_ci95_hi": outside["ci95_hi"],
                }
            )
    return pd.DataFrame(rows)


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
    elements = set(re.findall(r"[A-Z][a-z]?", str(formula)))
    groups = [
        ("transition_metal", transition),
        ("lanthanide_actinide", lan_act),
        ("alkali", alkali),
        ("alkaline_earth", alkaline),
        ("halogen", halogen),
        ("chalcogen", chalcogen),
        ("pnictogen", pnictogen),
    ]
    flags = {name for name, group in groups if elements & group}
    return flags or {"other"}


def element_family_discordance(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total_discordant = int(df["discordant"].sum())
    all_families = sorted({family for formula in df["formula"] for family in family_flags(str(formula))})
    for family in all_families:
        mask = df["formula"].map(lambda formula: family in family_flags(str(formula)))
        row = summarize_mask(df, mask)
        row.update(
            {
                "element_family": family,
                "membership": "overlapping",
                "population_fraction": row["n"] / len(df),
                "share_of_all_discordant": row["discordant_n"] / total_discordant
                if total_discordant
                else math.nan,
                "median_abs_delta_e_mev": float(df.loc[mask, "abs_delta_e_mev"].median())
                if row["n"]
                else math.nan,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows).sort_values(
        ["discordant_n", "discordance_rate", "n"], ascending=[False, False, False]
    )


def formula_proxy_discordance(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for formula, chunk in df.groupby("formula"):
        mask = df.index.isin(chunk.index)
        row = summarize_mask(df, mask)
        row.update({"formula": formula})
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(
        ["discordant_n", "discordance_rate", "n"], ascending=[False, False, False]
    )


def analysis_summary(df: pd.DataFrame) -> pd.DataFrame:
    low = df["abs_delta_e_mev"].lt(10)
    mid_tail = df["abs_delta_e_mev"].ge(10) & df["abs_delta_e_mev"].lt(100)
    high_tail = df["abs_delta_e_mev"].ge(100)
    rows = []
    for label, mask in [
        ("abs_delta_e_lt_10_meV", low),
        ("abs_delta_e_10_to_100_meV", mid_tail),
        ("abs_delta_e_ge_100_meV", high_tail),
        ("full_intersection", pd.Series(True, index=df.index)),
    ]:
        row = summarize_mask(df, mask)
        row.update({"stratum": label})
        rows.append(row)
    return pd.DataFrame(rows)[["stratum", "n", "discordant_n", "discordance_rate", "ci95_lo", "ci95_hi"]]


def source_label_value_clipping(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for source, energy_col, stable_col in [
        ("MP", "mp_e_above_hull", "mp_stable_exact"),
        ("Alexandria", "alex_e_above_hull", "alex_stable_exact"),
    ]:
        for label, mask in [
            ("stable", df[stable_col]),
            ("unstable", ~df[stable_col]),
        ]:
            chunk = df[mask].copy()
            rows.append(
                {
                    "source": source,
                    "label": label,
                    "n": int(len(chunk)),
                    "energy_min_eV_atom": float(chunk[energy_col].min()) if len(chunk) else math.nan,
                    "energy_max_eV_atom": float(chunk[energy_col].max()) if len(chunk) else math.nan,
                    "nonzero_abs_gt_1e_12_n": int((chunk[energy_col].abs() > 1e-12).sum()),
                    "zero_abs_le_1e_12_n": int((chunk[energy_col].abs() <= 1e-12).sum()),
                }
            )
    return pd.DataFrame(rows)


def top_decile_overlap(df: pd.DataFrame) -> pd.DataFrame:
    scores = pd.read_csv(SCORES)
    scores = scores[scores["score_status"].eq("scored")].copy()
    scores["score"] = pd.to_numeric(scores["score"], errors="coerce")
    matched_ids = set(df["material_id"].astype(str))
    top_sets: dict[str, set[str]] = {}
    for model, sdf in scores.groupby("model"):
        sdf = sdf.copy()
        sdf["material_id"] = sdf["material_id"].astype(str)
        common = sorted(set(sdf["material_id"]) & matched_ids)
        sub = sdf.set_index("material_id").loc[common]
        top_n = max(math.ceil(0.10 * len(sub)), 20)
        top_sets[str(model)] = set(sub.sort_values("score", ascending=True).head(top_n).index)

    rows = []
    models = sorted(top_sets)
    for i, model_a in enumerate(models):
        for model_b in models[i + 1 :]:
            a = top_sets[model_a]
            b = top_sets[model_b]
            union = a | b
            rows.append(
                {
                    "comparison": f"{model_a}_vs_{model_b}",
                    "model_a": model_a,
                    "model_b": model_b,
                    "top_n_a": len(a),
                    "top_n_b": len(b),
                    "intersection_n": len(a & b),
                    "union_n": len(union),
                    "jaccard": len(a & b) / len(union) if union else math.nan,
                }
            )
    if top_sets:
        all_intersection = set.intersection(*top_sets.values())
        all_union = set.union(*top_sets.values())
        rows.append(
            {
                "comparison": "all_three",
                "model_a": "|".join(models),
                "model_b": "",
                "top_n_a": min(len(values) for values in top_sets.values()),
                "top_n_b": max(len(values) for values in top_sets.values()),
                "intersection_n": len(all_intersection),
                "union_n": len(all_union),
                "jaccard": len(all_intersection) / len(all_union) if all_union else math.nan,
            }
        )
    return pd.DataFrame(rows)


def probe_reconciliation_bars(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    seen_cases = set()
    case = pd.read_csv(OUT / "table_wbm_alex_case_comparison.csv")
    for item in case.itertuples(index=False):
        rate = float(item.discordance_rate)
        n = int(item.n_common)
        role = item.role
        if item.case == "MP_vs_alex_route_b_full_snapshot":
            role = "matched_denominator_pairwise_baseline"
        rows.append(
            {
                "case": item.case,
                "n": n,
                "discordant_n": int(round(rate * n)),
                "discordance_rate": rate,
                "role": role,
                "status": "available",
            }
        )
        seen_cases.add(item.case)
    full = summarize_mask(df, pd.Series(True, index=df.index))
    if "MP_vs_alex_route_b_full_snapshot" not in seen_cases:
        rows.append(
            {
                "case": "MP_vs_alex_route_b_full_snapshot",
                "n": full["n"],
                "discordant_n": full["discordant_n"],
                "discordance_rate": full["discordance_rate"],
                "role": "matched_denominator_pairwise_baseline",
                "status": "available",
            }
        )
    mp_exact_stable = df["mp_stable_exact"]
    mp_exact_stable_summary = summarize_mask(df, mp_exact_stable)
    rows.append(
        {
            "case": "MP_native_exact_stable_release_conditioned",
            "n": mp_exact_stable_summary["n"],
            "discordant_n": mp_exact_stable_summary["discordant_n"],
            "discordance_rate": mp_exact_stable_summary["discordance_rate"],
            "role": "fig4c_source_native_selection_conditioned_diagnostic",
            "status": "available",
        }
    )
    mp_near_hull = df["mp_e_above_hull"].le(0.025)
    mp_near_hull_summary = summarize_mask(df, mp_near_hull)
    rows.append(
        {
            "case": "MP_native_near_hull_25meV_conditioned",
            "n": mp_near_hull_summary["n"],
            "discordant_n": mp_near_hull_summary["discordant_n"],
            "discordance_rate": mp_near_hull_summary["discordance_rate"],
            "role": "fig4c_boundary_sensitivity",
            "status": "available",
        }
    )
    outside = df["min_abs_e_mev"].gt(25)
    outside_summary = summarize_mask(df, outside)
    rows.append(
        {
            "case": "MP_vs_Alex_outside_either_source_25meV_flag",
            "n": outside_summary["n"],
            "discordant_n": outside_summary["discordant_n"],
            "discordance_rate": outside_summary["discordance_rate"],
            "role": "outside_conservative_near_hull_uncertainty_flag",
            "status": "available",
        }
    )
    rows.append(
        {
            "case": "MP_vs_Alex_strict_SCS_PARC_portability_check",
            "n": 100,
            "discordant_n": 0,
            "discordance_rate": 0.0,
            "role": "zero_non_empty_releases_across_seed_budget_rows",
            "status": "available_portability_check_not_fig4c_bar",
        }
    )
    return pd.DataFrame(rows)


def fig4_reconciliation_bars(df: pd.DataFrame) -> pd.DataFrame:
    case = pd.read_csv(OUT / "table_wbm_alex_case_comparison.csv").iloc[0]
    full = summarize_mask(df, pd.Series(True, index=df.index))
    mp_exact_stable = summarize_mask(df, df["mp_stable_exact"])
    mp_near_hull = summarize_mask(df, df["mp_e_above_hull"].le(0.025))
    return pd.DataFrame(
        [
            {
                "fig4_panel": "a",
                "bar": case["case"],
                "n": int(case["n_common"]),
                "discordance_rate": float(case["discordance_rate"]),
                "interpretation": "selection/source-specific high-discordance case analysis; not matched-denominator baseline",
            },
            {
                "fig4_panel": "b",
                "bar": "MP_vs_alex_full_denominator",
                "n": full["n"],
                "discordance_rate": full["discordance_rate"],
                "interpretation": "full strict-structure MP-vs-Alex denominator baseline",
            },
            {
                "fig4_panel": "c",
                "bar": "MP_native_exact_stable_release_conditioned",
                "n": mp_exact_stable["n"],
                "discordance_rate": mp_exact_stable["discordance_rate"],
                "interpretation": "source-native release conditioning applied to MP and evaluated under Alexandria",
            },
            {
                "fig4_panel": "c_sensitivity",
                "bar": "MP_native_near_hull_25meV_conditioned",
                "n": mp_near_hull["n"],
                "discordance_rate": mp_near_hull["discordance_rate"],
                "interpretation": "near-hull release-boundary sensitivity for panel c",
            },
        ]
    )


def fig4c_selection_conditioned_mp_alex(df: pd.DataFrame) -> pd.DataFrame:
    definitions = [
        ("full_MP_Alex_strict_denominator", pd.Series(True, index=df.index), "fig4b_full_denominator_baseline"),
        ("MP_native_exact_stable_release_ehull_le_0", df["mp_stable_exact"], "fig4c_selection_conditioned_primary_bar"),
        ("MP_native_near_hull_release_ehull_le_25meV", df["mp_e_above_hull"].le(0.025), "selection_boundary_sensitivity"),
        ("MP_score_top_decile_lowest_ehull", df["mp_e_above_hull"].rank(method="first").le(math.ceil(0.10 * len(df))), "score_conditioned_sensitivity"),
        ("MP_score_top_quartile_lowest_ehull", df["mp_e_above_hull"].rank(method="first").le(math.ceil(0.25 * len(df))), "score_conditioned_sensitivity"),
        ("MP_score_top_half_lowest_ehull", df["mp_e_above_hull"].rank(method="first").le(math.ceil(0.50 * len(df))), "score_conditioned_sensitivity"),
    ]
    rows = []
    for name, mask, role in definitions:
        sub = df[mask]
        summary = summarize_mask(df, mask)
        mp_selected_alex_unstable = int((sub["mp_stable_exact"] & ~sub["alex_stable_exact"]).sum())
        alex_selected_mp_unstable = int((~sub["mp_stable_exact"] & sub["alex_stable_exact"]).sum())
        rows.append(
            {
                "selection_rule": name,
                "n_selected": summary["n"],
                "discordant_n": summary["discordant_n"],
                "discordance_rate": summary["discordance_rate"],
                "mp_selected_but_alex_unstable_n": mp_selected_alex_unstable,
                "alex_selected_but_mp_unstable_n": alex_selected_mp_unstable,
                "mp_selected_but_alex_unstable_rate": mp_selected_alex_unstable / summary["n"]
                if summary["n"]
                else math.nan,
                "alex_selected_but_mp_unstable_rate": alex_selected_mp_unstable / summary["n"]
                if summary["n"]
                else math.nan,
                "mp_ehull_min": float(sub["mp_e_above_hull"].min()) if summary["n"] else math.nan,
                "mp_ehull_max": float(sub["mp_e_above_hull"].max()) if summary["n"] else math.nan,
                "alex_ehull_min": float(sub["alex_e_above_hull"].min()) if summary["n"] else math.nan,
                "alex_ehull_max": float(sub["alex_e_above_hull"].max()) if summary["n"] else math.nan,
                "paper_role": role,
            }
        )
    return pd.DataFrame(rows)


def fig4c_scs_portability_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "check": "strict_SCS_PARC_portability_check",
                "alpha": 0.10,
                "rho": 0.10,
                "K_values": "50;100;124;200;287",
                "seed_budget_rows": 100,
                "non_empty_releases": 0,
                "claim_scope": "portability_check_not_fig4c_bar",
            }
        ]
    )


def main() -> None:
    df = load_matches()
    delta_e_binned_discordance(df).to_csv(OUT / "table_fig2_delta_e_binned_discordance.csv", index=False)
    delta_e_quantiles(df).to_csv(OUT / "table_fig2_delta_e_quantiles.csv", index=False)
    delta_e_tail_thresholds(df).to_csv(OUT / "table_fig2_delta_e_tail_thresholds.csv", index=False)
    boundary_definition_robustness(df).to_csv(
        OUT / "table_boundary_definition_robustness.csv", index=False
    )
    element_family_discordance(df).to_csv(
        OUT / "table_structural_localization_element_family_overlap.csv", index=False
    )
    formula_proxy_discordance(df).head(100).to_csv(
        OUT / "table_structural_localization_formula_proxy_top.csv", index=False
    )
    analysis_summary(df).to_csv(OUT / "table_fig2_delta_e_summary.csv", index=False)
    source_label_value_clipping(df).to_csv(OUT / "table_source_label_value_clipping.csv", index=False)
    top_decile_overlap(df).to_csv(OUT / "table_selection_top_decile_overlap.csv", index=False)
    probe_reconciliation_bars(df).to_csv(OUT / "table_probe_reconciliation_bars.csv", index=False)
    fig4_reconciliation_bars(df).to_csv(OUT / "table_fig4_reconciliation_bars.csv", index=False)
    fig4c_selection_conditioned_mp_alex(df).to_csv(
        OUT / "table_fig4c_selection_conditioned_mp_alex.csv", index=False
    )
    fig4c_scs_portability_summary().to_csv(OUT / "table_fig4c_scs_portability_summary.csv", index=False)
    write_manifest(OUT / "MANIFEST_SHA256.txt", OUT)
    write_manifest(ROOT / "MANIFEST_SHA256.txt", ROOT)
    print("Wrote revised Fig. 2 energy-difference analysis tables", flush=True)


if __name__ == "__main__":
    main()
