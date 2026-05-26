from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FULL_OUT = ROOT / "outputs" / "milestones" / "materials_label_discordance_full_mp_alex_43984"
MATCHES = FULL_OUT / "table_full_mp_alex_structure_matches.csv"

TRANSITION_METALS = {
    "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
    "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
    "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
    "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn",
}
LANTHANIDES = {"La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"}
ACTINIDES = {"Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"}
HALOGENS = {"F", "Cl", "Br", "I", "At", "Ts"}


def element_list(chemical_system: str) -> list[str]:
    if not isinstance(chemical_system, str) or not chemical_system:
        return []
    return chemical_system.split("-")


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["mp_stable_exact"] = out["mp_stable_exact"].astype(bool)
    out["alex_stable_exact"] = out["alex_stable_exact"].astype(bool)
    out["discordant"] = out["mp_stable_exact"].ne(out["alex_stable_exact"])
    out["abs_delta_mev"] = (out["mp_e_above_hull"] - out["alex_e_above_hull"]).abs() * 1000.0
    out["elements"] = out["chemical_system"].map(element_list)
    out["n_elements"] = out["elements"].map(len)
    out["element_count_bin"] = out["n_elements"].map(
        lambda n: "unary" if n == 1 else "binary" if n == 2 else "ternary" if n == 3 else "quaternary_plus"
    )
    out["contains_transition_metal"] = out["elements"].map(lambda xs: bool(set(xs) & TRANSITION_METALS))
    out["contains_lanthanide"] = out["elements"].map(lambda xs: bool(set(xs) & LANTHANIDES))
    out["contains_actinide"] = out["elements"].map(lambda xs: bool(set(xs) & ACTINIDES))
    out["contains_oxygen"] = out["elements"].map(lambda xs: "O" in set(xs))
    out["contains_halogen"] = out["elements"].map(lambda xs: bool(set(xs) & HALOGENS))

    conditions = [
        out["mp_stable_exact"] & out["alex_stable_exact"],
        ~out["mp_stable_exact"] & ~out["alex_stable_exact"],
        out["mp_stable_exact"] & ~out["alex_stable_exact"],
        ~out["mp_stable_exact"] & out["alex_stable_exact"],
    ]
    choices = [
        "both_stable",
        "both_unstable",
        "mp_stable_alex_unstable",
        "mp_unstable_alex_stable",
    ]
    out["label_outcome"] = np.select(conditions, choices, default="unknown")
    return out


def summarize_group(df: pd.DataFrame, group_type: str, group_col: str) -> pd.DataFrame:
    rows = []
    for group, sub in df.groupby(group_col, dropna=False):
        n = len(sub)
        disc = int(sub["discordant"].sum())
        rows.append(
            {
                "group_type": group_type,
                "group": str(group),
                "n": n,
                "discordant": disc,
                "discordance_rate": disc / n if n else np.nan,
                "mp_stable_alex_unstable": int((sub["label_outcome"] == "mp_stable_alex_unstable").sum()),
                "mp_unstable_alex_stable": int((sub["label_outcome"] == "mp_unstable_alex_stable").sum()),
                "median_abs_delta_mev": sub["abs_delta_mev"].median(),
                "p90_abs_delta_mev": sub["abs_delta_mev"].quantile(0.90),
            }
        )
    return pd.DataFrame(rows)


def cluster_bootstrap(df: pd.DataFrame, cluster_col: str, n_boot: int = 5000, seed: int = 20260522) -> dict[str, float | int | str]:
    rng = np.random.default_rng(seed)
    grouped = list(df.groupby(cluster_col, dropna=False))
    clusters = np.array([g for g, _ in grouped], dtype=object)
    sizes = np.array([len(sub) for _, sub in grouped], dtype=float)
    disc = np.array([sub["discordant"].sum() for _, sub in grouped], dtype=float)
    n_clusters = len(clusters)
    rates = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        idx = rng.integers(0, n_clusters, size=n_clusters)
        rates[i] = disc[idx].sum() / sizes[idx].sum()
    return {
        "cluster": cluster_col,
        "n_clusters": n_clusters,
        "point_rate": float(df["discordant"].mean()),
        "bootstrap_mean": float(rates.mean()),
        "ci95_low": float(np.quantile(rates, 0.025)),
        "ci95_high": float(np.quantile(rates, 0.975)),
        "n_boot": n_boot,
        "seed": seed,
    }


def main() -> None:
    raw = pd.read_csv(MATCHES)
    strict = add_derived(raw[raw["match_status"].eq("strict_structure_match")])
    missing = raw[raw["match_status"].eq("missing_mp_record")].copy()

    tables = []
    tables.append(summarize_group(strict, "element_count", "element_count_bin"))
    for col in [
        "contains_transition_metal",
        "contains_lanthanide",
        "contains_actinide",
        "contains_oxygen",
        "contains_halogen",
    ]:
        tables.append(summarize_group(strict, col, col))
    pd.concat(tables, ignore_index=True).to_csv(
        FULL_OUT / "table_major_revision_chemistry_stratified_discordance.csv", index=False
    )

    direction = (
        strict.groupby("label_outcome")
        .agg(
            n=("material_id", "size"),
            rate=("material_id", lambda x: len(x) / len(strict)),
            median_abs_delta_mev=("abs_delta_mev", "median"),
            p25_abs_delta_mev=("abs_delta_mev", lambda x: x.quantile(0.25)),
            p75_abs_delta_mev=("abs_delta_mev", lambda x: x.quantile(0.75)),
            p90_abs_delta_mev=("abs_delta_mev", lambda x: x.quantile(0.90)),
        )
        .reset_index()
    )
    direction.to_csv(FULL_OUT / "table_major_revision_direction_delta_distribution.csv", index=False)

    cluster_rows = [
        cluster_bootstrap(strict, "chemical_system"),
        cluster_bootstrap(strict, "formula"),
        cluster_bootstrap(strict, "element_count_bin"),
    ]
    pd.DataFrame(cluster_rows).to_csv(FULL_OUT / "table_major_revision_cluster_bootstrap_ci.csv", index=False)

    if len(missing):
        missing["elements"] = missing["chemical_system"].map(element_list)
        missing["n_elements"] = missing["elements"].map(len)
        missing["element_count_bin"] = missing["n_elements"].map(
            lambda n: "unary" if n == 1 else "binary" if n == 2 else "ternary" if n == 3 else "quaternary_plus"
        )
        missing["alex_stable_exact"] = missing["alex_stable_exact"].astype(bool)
        missing["contains_transition_metal"] = missing["elements"].map(lambda xs: bool(set(xs) & TRANSITION_METALS))
        missing["contains_lanthanide"] = missing["elements"].map(lambda xs: bool(set(xs) & LANTHANIDES))
        missing["contains_actinide"] = missing["elements"].map(lambda xs: bool(set(xs) & ACTINIDES))
        missing["contains_oxygen"] = missing["elements"].map(lambda xs: "O" in set(xs))
        missing["contains_halogen"] = missing["elements"].map(lambda xs: bool(set(xs) & HALOGENS))
        rows = [
            {
                "subset": "missing_mp_record",
                "n": len(missing),
                "alex_stable": int(missing["alex_stable_exact"].sum()),
                "alex_unstable": int((~missing["alex_stable_exact"]).sum()),
                "n_chemical_systems": missing["chemical_system"].nunique(),
                "median_num_sites": missing["num_sites"].median(),
                "contains_transition_metal": int(missing["contains_transition_metal"].sum()),
                "contains_lanthanide": int(missing["contains_lanthanide"].sum()),
                "contains_actinide": int(missing["contains_actinide"].sum()),
                "contains_oxygen": int(missing["contains_oxygen"].sum()),
                "contains_halogen": int(missing["contains_halogen"].sum()),
            }
        ]
        pd.DataFrame(rows).to_csv(FULL_OUT / "table_major_revision_missing_mp_record_bias.csv", index=False)

    print("Wrote major-revision diagnostics to", FULL_OUT)


if __name__ == "__main__":
    main()
