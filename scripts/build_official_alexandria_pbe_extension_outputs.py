from __future__ import annotations

import hashlib
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from pymatgen.core import Composition


ROOT = Path(__file__).resolve().parents[1]
FEAS = ROOT / "outputs" / "milestones" / "official_alexandria_pbe_feasibility"
OUT = ROOT / "outputs" / "milestones" / "official_alexandria_pbe_extension"
CHGNET_SCORES = ROOT / "outputs" / "milestones" / "model_facing_benchmark_sensitivity_check" / "candidate_scores_chgnet_5000.csv"

CUTOFFS_MEV = [0, 1, 5, 10, 25]
TOPK_SOURCE = [100, 300, 500, 1000, 5000, 10000]
TOPK_CHGNET = [100, 300, 500, 1000, 2000, 5000]
BOOTSTRAP_N = 5000
BOOTSTRAP_SEED = 20260705

TRANSITION_METALS = {
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
LANTHANIDES = {"La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"}
HALOGENS = {"F", "Cl", "Br", "I", "At"}


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


def stable_label(values: pd.Series, cutoff_mev: int) -> pd.Series:
    return pd.to_numeric(values, errors="coerce").le(cutoff_mev / 1000.0)


def primary_triple(matches: pd.DataFrame) -> pd.DataFrame:
    counts = matches.groupby("material_id").size()
    single_ids = set(counts[counts.eq(1)].index.astype(str))
    return matches[matches["material_id"].astype(str).isin(single_ids)].copy().reset_index(drop=True)


def tie_break_denominators(matches: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "single_match_primary": primary_triple(matches),
        "include_multiple_lowest_official_alexandria_ehull": matches.sort_values(
            ["material_id", "official_alexandria_e_above_hull", "official_alexandria_id"]
        ).drop_duplicates("material_id", keep="first").reset_index(drop=True),
        "include_multiple_first_official_alexandria_identifier": matches.sort_values(
            ["material_id", "official_alexandria_id"]
        ).drop_duplicates("material_id", keep="first").reset_index(drop=True),
    }


def add_labels(df: pd.DataFrame, cutoff_mev: int) -> pd.DataFrame:
    out = df.copy()
    out["mp_label"] = stable_label(out["mp_e_above_hull"], cutoff_mev)
    out["alex_mp20_label"] = stable_label(out["alex_mp20_e_above_hull"], cutoff_mev)
    out["official_alexandria_label"] = stable_label(out["official_alexandria_e_above_hull"], cutoff_mev)
    return out


def pairwise_conflict_tables(matches: pd.DataFrame) -> None:
    pair_defs = [
        ("MP", "official_Alexandria_PBE", "mp_label", "official_alexandria_label"),
        ("MatterGen_alex_mp20", "official_Alexandria_PBE", "alex_mp20_label", "official_alexandria_label"),
        ("MP", "MatterGen_alex_mp20", "mp_label", "alex_mp20_label"),
    ]
    rate_rows = []
    direction_rows = []
    for rule, base in tie_break_denominators(matches).items():
        for cutoff in CUTOFFS_MEV:
            df = add_labels(base, cutoff)
            for source_a, source_b, a, b in pair_defs:
                valid = df[a].notna() & df[b].notna()
                sub = df.loc[valid].copy()
                conflict = sub[a].ne(sub[b])
                a_stable_b_unstable = sub[a] & ~sub[b]
                a_unstable_b_stable = ~sub[a] & sub[b]
                n = int(len(sub))
                k = int(conflict.sum())
                rate_rows.append(
                    {
                        "denominator_rule": rule,
                        "cutoff_mev_atom": cutoff,
                        "source_pair": f"{source_a}--{source_b}",
                        "source_a": source_a,
                        "source_b": source_b,
                        "n": n,
                        "conflict_n": k,
                        "conflict_fraction": k / n if n else math.nan,
                        "evidence_scope": "source_native_public_label_audit_not_common_hull",
                    }
                )
                direction_rows.append(
                    {
                        "denominator_rule": rule,
                        "cutoff_mev_atom": cutoff,
                        "source_pair": f"{source_a}--{source_b}",
                        "source_a_stable_source_b_unstable_n": int(a_stable_b_unstable.sum()),
                        "source_a_unstable_source_b_stable_n": int(a_unstable_b_stable.sum()),
                        "source_a_stable_source_b_unstable_fraction": float(a_stable_b_unstable.mean()) if n else math.nan,
                        "source_a_unstable_source_b_stable_fraction": float(a_unstable_b_stable.mean()) if n else math.nan,
                        "evidence_scope": "directionality_for_source_native_public_label_conflicts",
                    }
                )
    pd.DataFrame(rate_rows).to_csv(OUT / "table_official_alexandria_pairwise_conflict_by_cutoff.csv", index=False)
    pd.DataFrame(direction_rows).to_csv(OUT / "table_official_alexandria_pairwise_directionality_by_cutoff.csv", index=False)


def three_source_composition(df: pd.DataFrame) -> None:
    rows = []
    for cutoff in CUTOFFS_MEV:
        tmp = add_labels(df, cutoff)
        tmp["label_tuple"] = tmp.apply(
            lambda r: f"{int(bool(r.mp_label))}{int(bool(r.alex_mp20_label))}{int(bool(r.official_alexandria_label))}",
            axis=1,
        )
        counts = tmp["label_tuple"].value_counts().sort_index()
        for label_tuple, n in counts.items():
            rows.append(
                {
                    "cutoff_mev_atom": cutoff,
                    "label_tuple_mp_alexmp20_officialalex": label_tuple,
                    "n": int(n),
                    "fraction": int(n) / len(tmp),
                    "interpretation": tuple_interpretation(label_tuple),
                    "evidence_scope": "three_source_source_native_label_composition",
                }
            )
    pd.DataFrame(rows).to_csv(OUT / "table_official_alexandria_three_source_label_composition_by_cutoff.csv", index=False)


def tuple_interpretation(label_tuple: str) -> str:
    names = ["MP", "alex-mp-20", "official Alexandria-PBE"]
    stable_sources = [name for bit, name in zip(label_tuple, names) if bit == "1"]
    if len(stable_sources) == 3:
        return "stable in all three sources"
    if len(stable_sources) == 0:
        return "unstable in all three sources"
    if len(stable_sources) == 1:
        return "stable only in " + stable_sources[0]
    return "stable in " + " and ".join(stable_sources)


def ehull_drift_tables(df: pd.DataFrame) -> None:
    out = df[
        [
            "material_id",
            "formula",
            "reduced_formula",
            "chemical_system",
            "alex_mp20_e_above_hull",
            "official_alexandria_e_above_hull",
            "alex_mp20_stable_exact",
            "official_alexandria_stable_exact",
        ]
    ].copy()
    out["official_minus_alex_mp20_ehull"] = out["official_alexandria_e_above_hull"] - out["alex_mp20_e_above_hull"]
    out["abs_official_minus_alex_mp20_ehull"] = out["official_minus_alex_mp20_ehull"].abs()
    out["label_relation_exact_zero"] = np.select(
        [
            out["alex_mp20_stable_exact"].astype(bool) & out["official_alexandria_stable_exact"].astype(bool),
            out["alex_mp20_stable_exact"].astype(bool) & ~out["official_alexandria_stable_exact"].astype(bool),
            ~out["alex_mp20_stable_exact"].astype(bool) & out["official_alexandria_stable_exact"].astype(bool),
        ],
        ["both_stable", "alex_mp20_stable_only", "official_alexandria_stable_only"],
        default="both_unstable",
    )
    out.to_csv(OUT / "table_official_alexandria_alexmp20_ehull_drift_rows.csv", index=False)

    rows = []
    for label, sub in {"all": out, **{k: v for k, v in out.groupby("label_relation_exact_zero")}}.items():
        rows.append(
            {
                "subset": label,
                "n": int(len(sub)),
                "mean_official_minus_alex_mp20_ehull": float(sub["official_minus_alex_mp20_ehull"].mean()),
                "median_official_minus_alex_mp20_ehull": float(sub["official_minus_alex_mp20_ehull"].median()),
                "median_abs_official_minus_alex_mp20_ehull": float(sub["abs_official_minus_alex_mp20_ehull"].median()),
                "p90_abs_official_minus_alex_mp20_ehull": float(sub["abs_official_minus_alex_mp20_ehull"].quantile(0.9)),
                "evidence_scope": "source_native_hull_value_difference_not_mechanism_attribution",
            }
        )
    pd.DataFrame(rows).to_csv(OUT / "table_official_alexandria_alexmp20_ehull_drift_summary.csv", index=False)


def formula_elements(formula: str) -> set[str]:
    try:
        return {str(el) for el in Composition(str(formula)).elements}
    except Exception:
        return set()


def add_chemistry_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    elements = out["reduced_formula"].map(formula_elements)
    out["n_elements"] = elements.map(len)
    out["element_count_bin"] = out["n_elements"].map(
        lambda n: "unary" if n == 1 else "binary" if n == 2 else "ternary" if n == 3 else "quaternary_or_higher"
    )
    out["transition_metal_present"] = elements.map(lambda s: bool(s & TRANSITION_METALS))
    out["lanthanide_present"] = elements.map(lambda s: bool(s & LANTHANIDES))
    out["oxygen_present"] = elements.map(lambda s: "O" in s)
    out["halogen_present"] = elements.map(lambda s: bool(s & HALOGENS))
    return out


def cluster_bootstrap_fraction(df: pd.DataFrame, conflict_col: str, seed_offset: int = 0) -> tuple[float, float]:
    if df.empty:
        return math.nan, math.nan
    local = df.reset_index(drop=True)
    by_cluster = local.groupby("chemical_system")[conflict_col].agg(["sum", "count"]).reset_index(drop=True)
    conflict_sum = by_cluster["sum"].astype(float).to_numpy()
    cluster_n = by_cluster["count"].astype(float).to_numpy()
    rng = np.random.default_rng(BOOTSTRAP_SEED + seed_offset)
    vals = []
    for _ in range(BOOTSTRAP_N):
        picked = rng.integers(0, len(by_cluster), size=len(by_cluster))
        vals.append(float(conflict_sum[picked].sum() / cluster_n[picked].sum()))
    lo, hi = np.quantile(vals, [0.025, 0.975])
    return float(lo), float(hi)


def chemistry_bootstrap_table(df: pd.DataFrame) -> None:
    pair_defs = [
        ("MP--official_Alexandria_PBE", "mp_label", "official_alexandria_label"),
        ("alex-mp-20--official_Alexandria_PBE", "alex_mp20_label", "official_alexandria_label"),
        ("MP--alex-mp-20", "mp_label", "alex_mp20_label"),
    ]
    rows = []
    flagged = add_chemistry_flags(df)
    stratum_defs: list[tuple[str, str, pd.Series]] = [("overall", "all", pd.Series(True, index=flagged.index))]
    for value in ["unary", "binary", "ternary", "quaternary_or_higher"]:
        stratum_defs.append(("element_count", value, flagged["element_count_bin"].eq(value)))
    for col in ["transition_metal_present", "lanthanide_present", "oxygen_present", "halogen_present"]:
        stratum_defs.append(("element_family", col, flagged[col].astype(bool)))

    seed = 0
    for cutoff in CUTOFFS_MEV:
        tmp = add_labels(flagged, cutoff)
        for pair, a, b in pair_defs:
            tmp_pair = tmp.copy()
            tmp_pair["source_conflict"] = tmp_pair[a].ne(tmp_pair[b])
            for stratum_type, stratum, mask in stratum_defs:
                sub = tmp_pair.loc[mask].copy()
                n = int(len(sub))
                if n == 0:
                    continue
                k = int(sub["source_conflict"].sum())
                lo, hi = cluster_bootstrap_fraction(sub, "source_conflict", seed)
                seed += 1
                rows.append(
                    {
                        "cutoff_mev_atom": cutoff,
                        "source_pair": pair,
                        "stratum_type": stratum_type,
                        "stratum": stratum,
                        "n": n,
                        "chemical_system_n": int(sub["chemical_system"].nunique()),
                        "conflict_n": k,
                        "conflict_fraction": k / n,
                        "cluster_bootstrap_ci_low": lo,
                        "cluster_bootstrap_ci_high": hi,
                        "bootstrap_unit": "chemical_system",
                        "n_bootstrap": BOOTSTRAP_N,
                        "bootstrap_seed": BOOTSTRAP_SEED,
                        "evidence_scope": "chemistry_stratified_source_conflict_public_label_audit",
                    }
                )
    pd.DataFrame(rows).to_csv(OUT / "table_official_alexandria_chemistry_stratified_bootstrap.csv", index=False)


def bootstrap_mean(series: pd.Series, n_eval: int, rng: np.random.Generator) -> tuple[float, float]:
    if n_eval == 0:
        return math.nan, math.nan
    values = series.astype(float).to_numpy()
    idx = np.arange(len(values))
    vals = []
    for _ in range(2000):
        sample = rng.choice(idx, size=len(idx), replace=True)
        vals.append(float(values[sample].mean()))
    lo, hi = np.quantile(vals, [0.025, 0.975])
    return float(lo), float(hi)


def label_view_values(df: pd.DataFrame, label_view: str) -> tuple[pd.Series, pd.Series]:
    mp = df["mp_stable_exact"].astype(bool)
    alex = df["alex_mp20_stable_exact"].astype(bool)
    official = df["official_alexandria_stable_exact"].astype(bool)
    if label_view == "MP":
        return mp, pd.Series(True, index=df.index)
    if label_view == "MatterGen_alex_mp20":
        return alex, pd.Series(True, index=df.index)
    if label_view == "official_Alexandria_PBE":
        return official, pd.Series(True, index=df.index)
    if label_view == "consensus_all_three_stable":
        return mp & alex & official, pd.Series(True, index=df.index)
    if label_view == "conflict_excluded_consensus":
        agree = mp.eq(alex) & mp.eq(official)
        return mp, agree
    raise ValueError(label_view)


def ranking_uncertainty_tables(df: pd.DataFrame) -> None:
    label_views = [
        "MP",
        "MatterGen_alex_mp20",
        "official_Alexandria_PBE",
        "consensus_all_three_stable",
        "conflict_excluded_consensus",
    ]
    ranking_specs = {
        "MP_source_native_ehull_rank": ("mp_e_above_hull", True),
        "MatterGen_alex_mp20_source_native_ehull_rank": ("alex_mp20_e_above_hull", True),
        "official_Alexandria_PBE_source_native_ehull_rank": ("official_alexandria_e_above_hull", True),
    }
    rows = []
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    for ranking_name, (score_col, ascending) in ranking_specs.items():
        ranked = df.sort_values([score_col, "material_id"], ascending=[ascending, True]).reset_index(drop=True)
        for k in TOPK_SOURCE:
            if len(ranked) < k:
                continue
            top = ranked.head(k).copy()
            for label_view in label_views:
                values, eval_mask = label_view_values(top, label_view)
                eval_values = values.loc[eval_mask]
                n_eval = int(eval_mask.sum())
                stable_n = int(eval_values.sum()) if n_eval else 0
                lo, hi = bootstrap_mean(eval_values, n_eval, rng)
                rows.append(
                    {
                        "ranking": ranking_name,
                        "ranking_score": score_col,
                        "ranking_direction": "ascending_lower_ehull_first",
                        "K": k,
                        "label_view": label_view,
                        "topk_n": int(k),
                        "evaluation_n": n_eval,
                        "retained_fraction": n_eval / k,
                        "stable_n": stable_n,
                        "stable_fraction": stable_n / n_eval if n_eval else math.nan,
                        "bootstrap_ci_low": lo,
                        "bootstrap_ci_high": hi,
                        "bootstrap_n": 2000,
                        "bootstrap_seed": BOOTSTRAP_SEED,
                        "evidence_scope": "fixed_source_native_ranking_label_uncertainty_band_not_model_benchmark",
                    }
                )
    pd.DataFrame(rows).to_csv(OUT / "table_official_alexandria_source_native_ranking_uncertainty.csv", index=False)


def chgnet_uncertainty_table(df: pd.DataFrame) -> None:
    if not CHGNET_SCORES.exists():
        return
    score = pd.read_csv(CHGNET_SCORES)
    merged = score.merge(
        df[
            [
                "material_id",
                "official_alexandria_e_above_hull",
                "official_alexandria_stable_exact",
            ]
        ],
        on="material_id",
        how="inner",
    )
    if merged.empty:
        return
    merged = merged.rename(columns={"alex_stable": "alex_mp20_stable_exact", "mp_stable": "mp_stable_exact"})
    merged["mp_stable_exact"] = merged["mp_stable_exact"].astype(bool)
    merged["alex_mp20_stable_exact"] = merged["alex_mp20_stable_exact"].astype(bool)
    merged["official_alexandria_stable_exact"] = merged["official_alexandria_stable_exact"].astype(bool)
    ranked = merged.sort_values(["score", "material_id"], ascending=[False, True]).reset_index(drop=True)
    label_views = [
        "MP",
        "MatterGen_alex_mp20",
        "official_Alexandria_PBE",
        "consensus_all_three_stable",
        "conflict_excluded_consensus",
    ]
    rows = []
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    for k in TOPK_CHGNET:
        if len(ranked) < k:
            continue
        top = ranked.head(k).copy()
        for label_view in label_views:
            values, eval_mask = label_view_values(top, label_view)
            eval_values = values.loc[eval_mask]
            n_eval = int(eval_mask.sum())
            stable_n = int(eval_values.sum()) if n_eval else 0
            lo, hi = bootstrap_mean(eval_values, n_eval, rng)
            rows.append(
                {
                    "ranking": "CHGNet_fixed_public_safe_score_rank",
                    "ranking_score": "score",
                    "ranking_direction": "descending_higher_score_first",
                    "K": k,
                    "label_view": label_view,
                    "topk_n": int(k),
                    "evaluation_n": n_eval,
                    "retained_fraction": n_eval / k,
                    "stable_n": stable_n,
                    "stable_fraction": stable_n / n_eval if n_eval else math.nan,
                    "bootstrap_ci_low": lo,
                    "bootstrap_ci_high": hi,
                    "bootstrap_n": 2000,
                    "bootstrap_seed": BOOTSTRAP_SEED,
                    "scored_rows_with_single_official_alexandria_match": int(len(ranked)),
                    "evidence_scope": "fixed_chgnet_ranking_label_uncertainty_band_not_chgnet_benchmark",
                }
            )
    pd.DataFrame(rows).to_csv(OUT / "table_official_alexandria_chgnet_ranking_uncertainty.csv", index=False)


def write_figure_sources() -> None:
    conflict = pd.read_csv(OUT / "table_official_alexandria_pairwise_conflict_by_cutoff.csv")
    comp = pd.read_csv(OUT / "table_official_alexandria_three_source_label_composition_by_cutoff.csv")
    drift = pd.read_csv(OUT / "table_official_alexandria_alexmp20_ehull_drift_summary.csv")
    rank = pd.read_csv(OUT / "table_official_alexandria_source_native_ranking_uncertainty.csv")
    conflict[
        (conflict["denominator_rule"].eq("single_match_primary")) & (conflict["cutoff_mev_atom"].isin([0, 5, 25]))
    ].to_csv(OUT / "figure_official_alexandria_pairwise_conflicts_inputs.csv", index=False)
    comp[comp["cutoff_mev_atom"].eq(0)].to_csv(OUT / "figure_official_alexandria_label_composition_inputs.csv", index=False)
    drift.to_csv(OUT / "figure_official_alexandria_ehull_drift_inputs.csv", index=False)
    rank[(rank["K"].isin([100, 500, 1000, 5000]))].to_csv(
        OUT / "figure_official_alexandria_ranking_uncertainty_inputs.csv", index=False
    )


def write_closeout(df: pd.DataFrame) -> None:
    conflict = pd.read_csv(OUT / "table_official_alexandria_pairwise_conflict_by_cutoff.csv")
    primary = conflict[(conflict["denominator_rule"].eq("single_match_primary")) & (conflict["cutoff_mev_atom"].eq(0))]
    lines = [
        "# Official Alexandria-PBE extension closeout",
        "",
        "Scope: source-native public-label audit across MP, MatterGen alex-mp-20 and official Alexandria-PBE.",
        "This is not a common-hull reconstruction and does not attribute conflicts to pseudopotentials, corrections, magnetism or relaxation settings.",
        "",
        f"Primary single-match triple denominator: {len(df):,} rows.",
        "",
        "## Exact-zero pairwise source-conflict burdens",
        "",
        primary[["source_pair", "n", "conflict_n", "conflict_fraction"]].to_markdown(index=False),
        "",
        "## Public-safe artifacts",
        "",
        "The milestone contains cutoff-grid conflict tables, directionality, three-source label composition, alex-mp-20--official Alexandria-PBE hull-value drift, chemistry-stratified chemical-system bootstraps, fixed-ranking uncertainty bands and figure-source inputs.",
    ]
    (OUT / "OFFICIAL_ALEXANDRIA_PBE_EXTENSION_CLOSEOUT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    matches = pd.read_csv(FEAS / "table_official_alexandria_pbe_exact_matches.csv")
    triple = primary_triple(matches)
    triple.to_csv(OUT / "table_official_alexandria_single_match_triple_denominator.csv", index=False)
    pairwise_conflict_tables(matches)
    three_source_composition(triple)
    ehull_drift_tables(triple)
    chemistry_bootstrap_table(triple)
    ranking_uncertainty_tables(triple)
    chgnet_uncertainty_table(triple)
    write_figure_sources()
    write_closeout(triple)
    write_manifest()
    print(f"Wrote official Alexandria-PBE extension outputs to {OUT}", flush=True)


if __name__ == "__main__":
    main()
