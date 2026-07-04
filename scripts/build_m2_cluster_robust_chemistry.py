"""
M2: Cluster-robust intervals for chemistry strata discordance.

1. Cluster-bootstrap CIs (by chemical system) for each chemistry stratum
2. Multiplicity-adjusted significance (Bonferroni)
3. Logistic regression controlling for element count
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from pymatgen.core import Composition

ROOT = Path("")
FULL = ROOT / "outputs" / "milestones" / "materials_label_discordance_full_mp_alex_43984"
OUT = ROOT / "outputs" / "milestones" / "benchmark_reliability_enhancement"
MATCHES_CSV = FULL / "table_full_mp_alex_structure_matches.csv"
N_BOOTSTRAP = 2000
BOOTSTRAP_SEED = 20260606


def cluster_bootstrap_ci(
    df: pd.DataFrame,
    cluster_col: str,
    value_col: str,
    n_bootstrap: int = 2000,
    seed: int = 20260606,
) -> tuple[float, float, float]:
    """Cluster-bootstrap CI for a mean, resampling clusters."""
    rng = np.random.default_rng(seed)
    clusters = sorted(df[cluster_col].unique())
    n_clusters = len(clusters)
    obs = df[value_col].mean()
    means = []
    for _ in range(n_bootstrap):
        sampled = rng.choice(clusters, size=n_clusters, replace=True)
        boot = df[df[cluster_col].isin(sampled)]
        means.append(boot[value_col].mean())
    lo, hi = np.quantile(means, [0.025, 0.975])
    return obs, lo, hi


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(MATCHES_CSV)
    strict = df[df["match_status"] == "strict_structure_match"].copy()
    strict["discordant"] = (strict["mp_stable_exact"] != strict["alex_stable_exact"]).astype(int)
    strict["n_elements"] = strict["formula"].apply(lambda f: len(Composition(str(f)).elements))

    # ---- Chemistry strata definitions ----
    def check_elements(formula: str, elements: set[str]) -> bool:
        try:
            comp_els = {str(el) for el in Composition(str(formula)).elements}
            return bool(comp_els & elements)
        except Exception:
            return False

    halogens = {"F", "Cl", "Br", "I"}
    lanthanides = {"La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"}
    transition_metals = {"Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Y", "Zr", "Nb", "Mo", "Tc",
                         "Ru", "Rh", "Pd", "Ag", "Cd", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg"}
    oxygen = {"O"}

    strata_defs = {
        "full_denominator": ("Full denominator", strict["discordant"]),
        "oxygen_containing": ("Oxygen-containing", strict[strict["formula"].apply(lambda f: check_elements(f, oxygen))]["discordant"]),
        "halogen_containing": ("Halogen-containing", strict[strict["formula"].apply(lambda f: check_elements(f, halogens))]["discordant"]),
        "lanthanide_containing": ("Lanthanide-containing", strict[strict["formula"].apply(lambda f: check_elements(f, lanthanides))]["discordant"]),
        "transition_metal_containing": ("TM-containing", strict[strict["formula"].apply(lambda f: check_elements(f, transition_metals))]["discordant"]),
    }

    # ---- Simple (non-clustered) CIs ----
    from scipy.stats import norm

    rows = []
    for key, (label, series) in strata_defs.items():
        n = len(series)
        k = int(series.sum())
        p = k / n
        z = norm.ppf(0.975)
        se = np.sqrt(p * (1 - p) / n)
        ci_lo = p - z * se
        ci_hi = p + z * se

        rows.append({
            "stratum": label,
            "stratum_key": key,
            "n": n,
            "discordant_n": k,
            "discordance_rate": p,
            "ci_low_95_simple": ci_lo,
            "ci_high_95_simple": ci_hi,
        })

    # ---- Cluster-bootstrap CIs (only for chemistry strata) ----
    # For each stratum, cluster-bootstrap by chemical_system
    for row_dict in rows:
        key = row_dict["stratum_key"]
        if key == "full_denominator":
            sub = strict
        elif key == "oxygen_containing":
            sub = strict[strict["formula"].apply(lambda f: check_elements(f, oxygen))]
        elif key == "halogen_containing":
            sub = strict[strict["formula"].apply(lambda f: check_elements(f, halogens))]
        elif key == "lanthanide_containing":
            sub = strict[strict["formula"].apply(lambda f: check_elements(f, lanthanides))]
        elif key == "transition_metal_containing":
            sub = strict[strict["formula"].apply(lambda f: check_elements(f, transition_metals))]
        else:
            continue

        obs, ci_lo_cb, ci_hi_cb = cluster_bootstrap_ci(sub, "chemical_system", "discordant")
        row_dict["discordance_rate_cluster"] = obs
        row_dict["ci_low_95_cluster"] = ci_lo_cb
        row_dict["ci_high_95_cluster"] = ci_hi_cb
        row_dict["n_clusters"] = sub["chemical_system"].nunique()

    ci_df = pd.DataFrame(rows)

    # ---- Multiplicity adjustment (Bonferroni) ----
    n_tests = 4  # 4 chemistry contrasts
    z_bonf = norm.ppf(1 - 0.05 / (2 * n_tests))
    for idx, row_dict in enumerate(rows):
        if row_dict["stratum_key"] == "full_denominator":
            continue
        p = row_dict["discordance_rate"]
        n_s = row_dict["n"]
        se = np.sqrt(p * (1 - p) / n_s)
        row_dict["ci_low_95_bonferroni"] = p - z_bonf * se
        row_dict["ci_high_95_bonferroni"] = p + z_bonf * se

    ci_df = pd.DataFrame(rows)

    # ---- Logistic regression: does halogen/oxygen effect survive controlling for n_elements? ----
    logit_data = strict.copy()
    logit_data["has_oxygen"] = logit_data["formula"].apply(lambda f: check_elements(f, oxygen)).astype(int)
    logit_data["has_halogen"] = logit_data["formula"].apply(lambda f: check_elements(f, halogens)).astype(int)
    logit_data["has_lanthanide"] = logit_data["formula"].apply(lambda f: check_elements(f, lanthanides)).astype(int)
    logit_data["has_tm"] = logit_data["formula"].apply(lambda f: check_elements(f, transition_metals)).astype(int)

    # Model 1: just chemistry indicators
    X1 = logit_data[["has_oxygen", "has_halogen", "has_lanthanide", "has_tm"]]
    y = logit_data["discordant"]

    # Model 2: chemistry + n_elements
    scaler = StandardScaler()
    X2 = logit_data[["has_oxygen", "has_halogen", "has_lanthanide", "has_tm", "n_elements"]].copy()
    X2["n_elements"] = scaler.fit_transform(X2[["n_elements"]])

    logit_rows = []
    for name, X in [("chemistry_only", X1), ("chemistry_plus_nelements", X2)]:
        lr = LogisticRegression(max_iter=1000, random_state=20260606)
        lr.fit(X, y)
        for i, col in enumerate(X.columns):
            logit_rows.append({
                "model": name,
                "predictor": col,
                "coefficient": lr.coef_[0][i],
                "odds_ratio": np.exp(lr.coef_[0][i]),
                "intercept": lr.intercept_[0] if i == 0 else "",
            })

    logit_df = pd.DataFrame(logit_rows)

    # ---- Save ----
    ci_df.to_csv(OUT / "table_chemistry_strata_cluster_ci.csv", index=False)
    logit_df.to_csv(OUT / "table_chemistry_logistic_regression.csv", index=False)

    print("=== Chemistry strata with cluster-bootstrap CIs ===")
    print(ci_df.to_string(index=False))
    print("\n=== Logistic regression ===")
    print(logit_df.to_string(index=False))
    print(f"\nWrote to {OUT}/")


if __name__ == "__main__":
    main()
