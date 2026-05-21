from __future__ import annotations

import hashlib
import math
import random
import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "milestones" / "materials_label_discordance_preregistration"


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


def load_matches() -> pd.DataFrame:
    matches = pd.read_csv(OUT / "table_route_b_full_snapshot_matches.csv")
    strict = matches[matches["match_status"].eq("strict_structure_match")].copy()
    strict["mp_e_above_hull"] = pd.to_numeric(strict["mp_e_above_hull"], errors="coerce")
    strict["alex_e_above_hull"] = pd.to_numeric(strict["alex_e_above_hull"], errors="coerce")
    strict["mp_stable_exact"] = strict["mp_stable_exact"].astype(str).str.lower().eq("true")
    strict["alex_stable_exact"] = strict["alex_stable_exact"].astype(str).str.lower().eq("true")
    strict["discordant"] = strict["mp_stable_exact"] != strict["alex_stable_exact"]
    strict["mp_selected_but_alex_unstable"] = strict["mp_stable_exact"] & ~strict["alex_stable_exact"]
    strict["alex_selected_but_mp_unstable"] = ~strict["mp_stable_exact"] & strict["alex_stable_exact"]
    return strict.sort_values(["mp_e_above_hull", "material_id"]).reset_index(drop=True)


def summarize_selection(df: pd.DataFrame, *, selection_rule: str, mask: pd.Series, role: str) -> dict:
    selected = df[mask].copy()
    n = len(selected)
    discordant_n = int(selected["discordant"].sum()) if n else 0
    mp_selected_alex_unstable = int(selected["mp_selected_but_alex_unstable"].sum()) if n else 0
    alex_selected_mp_unstable = int(selected["alex_selected_but_mp_unstable"].sum()) if n else 0
    return {
        "selection_rule": selection_rule,
        "n_selected": n,
        "discordant_n": discordant_n,
        "discordance_rate": float(discordant_n / n) if n else math.nan,
        "mp_selected_but_alex_unstable_n": mp_selected_alex_unstable,
        "alex_selected_but_mp_unstable_n": alex_selected_mp_unstable,
        "mp_selected_but_alex_unstable_rate": float(mp_selected_alex_unstable / n) if n else math.nan,
        "alex_selected_but_mp_unstable_rate": float(alex_selected_mp_unstable / n) if n else math.nan,
        "mp_ehull_min": float(selected["mp_e_above_hull"].min()) if n else math.nan,
        "mp_ehull_max": float(selected["mp_e_above_hull"].max()) if n else math.nan,
        "alex_ehull_min": float(selected["alex_e_above_hull"].min()) if n else math.nan,
        "alex_ehull_max": float(selected["alex_e_above_hull"].max()) if n else math.nan,
        "paper_role": role,
    }


def build_rows(df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    top_decile_n = max(math.ceil(0.10 * n), 20)
    top_quartile_n = math.ceil(0.25 * n)
    top_half_n = math.ceil(0.50 * n)
    rows = [
        summarize_selection(
            df,
            selection_rule="full_MP_Alex_strict_denominator",
            mask=pd.Series([True] * n, index=df.index),
            role="fig4b_full_denominator_baseline",
        ),
        summarize_selection(
            df,
            selection_rule="MP_native_exact_stable_release_ehull_le_0",
            mask=df["mp_e_above_hull"] <= 0.0,
            role="fig4c_selection_conditioned_primary_bar",
        ),
        summarize_selection(
            df,
            selection_rule="MP_native_near_hull_release_ehull_le_25meV",
            mask=df["mp_e_above_hull"] <= 0.025,
            role="selection_boundary_sensitivity",
        ),
        summarize_selection(
            df,
            selection_rule="MP_score_top_decile_lowest_ehull",
            mask=pd.Series(range(n), index=df.index) < top_decile_n,
            role="score_conditioned_sensitivity",
        ),
        summarize_selection(
            df,
            selection_rule="MP_score_top_quartile_lowest_ehull",
            mask=pd.Series(range(n), index=df.index) < top_quartile_n,
            role="score_conditioned_sensitivity",
        ),
        summarize_selection(
            df,
            selection_rule="MP_score_top_half_lowest_ehull",
            mask=pd.Series(range(n), index=df.index) < top_half_n,
            role="score_conditioned_sensitivity",
        ),
    ]
    return pd.DataFrame(rows)


def build_reconciliation(fig4c: pd.DataFrame) -> pd.DataFrame:
    case = pd.read_csv(OUT / "table_wbm_alex_case_comparison.csv")
    wbm = case[case["case"].eq("WBM_vs_alex_existing_probe")].iloc[0]
    full = fig4c[fig4c["selection_rule"].eq("full_MP_Alex_strict_denominator")].iloc[0]
    selected = fig4c[fig4c["selection_rule"].eq("MP_native_exact_stable_release_ehull_le_0")].iloc[0]
    near = fig4c[fig4c["selection_rule"].eq("MP_native_near_hull_release_ehull_le_25meV")].iloc[0]
    return pd.DataFrame(
        [
            {
                "fig4_panel": "a",
                "bar": "WBM_vs_alex_existing_probe",
                "n": int(wbm["n_common"]),
                "discordance_rate": float(wbm["discordance_rate"]),
                "interpretation": "selection/source-specific high-discordance case analysis; not full-snapshot baseline",
            },
            {
                "fig4_panel": "b",
                "bar": "MP_vs_alex_full_denominator",
                "n": int(full["n_selected"]),
                "discordance_rate": float(full["discordance_rate"]),
                "interpretation": "full strict-structure MP-vs-Alex denominator baseline",
            },
            {
                "fig4_panel": "c",
                "bar": "MP_native_exact_stable_release_conditioned",
                "n": int(selected["n_selected"]),
                "discordance_rate": float(selected["discordance_rate"]),
                "interpretation": "portable source-native release rule applied to MP, evaluated under Alex",
            },
            {
                "fig4_panel": "c_sensitivity",
                "bar": "MP_native_near_hull_25meV_conditioned",
                "n": int(near["n_selected"]),
                "discordance_rate": float(near["discordance_rate"]),
                "interpretation": "near-hull release-boundary sensitivity for panel c",
            },
        ]
    )


def element_list(formula: str) -> list[str]:
    return sorted(set(re.findall(r"[A-Z][a-z]?", str(formula))))


def gamma_star_from_p(p_value: float | None) -> float | None:
    if p_value is None or p_value <= 0.0 or p_value >= 1.0:
        return None
    gamma = -1.0 / math.log(p_value)
    return gamma if 0.0 < gamma < 1.0 else None


def scs_release_count(evalues: np.ndarray, alpha: float, budget: int) -> tuple[int, float]:
    if len(evalues) == 0:
        return 0, 0.0
    sorted_e = np.sort(evalues.astype(float))[::-1]
    released = 0
    best_ratio = 0.0
    for k, evalue in enumerate(sorted_e, start=1):
        best_ratio = max(best_ratio, float(alpha * k * evalue / budget))
        if evalue >= budget / (alpha * k):
            released = k
    return released, best_ratio


def split_blocks(block_ids: list[str], seed: int) -> tuple[set[str], set[str]]:
    ordered = sorted(set(str(block) for block in block_ids))
    rng = random.Random(seed)
    rng.shuffle(ordered)
    cut = len(ordered) // 2
    return set(ordered[:cut]), set(ordered[cut:])


def observed_positive_mask(frame: pd.DataFrame, rho: float, seed: int) -> np.ndarray:
    true_idx = np.flatnonzero(frame["mp_stable_exact"].to_numpy(dtype=bool))
    observed = np.zeros(len(frame), dtype=bool)
    n_observed = int(round(len(true_idx) * min(rho, 1.0)))
    if n_observed <= 0:
        return observed
    scores = frame["mp_score"].to_numpy(dtype=float)
    chosen = true_idx[np.argsort(scores[true_idx])[::-1]][:n_observed]
    observed[chosen] = True
    return observed


def compute_scs_portability(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    elements = work["formula"].map(element_list)
    work["n_elements"] = elements.map(len).astype(int)
    work["first_two_elements"] = elements.map(lambda xs: "-".join(xs[:2]) if xs else "unknown")
    work["composition_family_pair"] = work["n_elements"].astype(str) + "|" + work["first_two_elements"]
    work["mp_score"] = -work["mp_e_above_hull"].astype(float)

    rows = []
    for budget in [50, 100, 124, 200, 287]:
        for seed in range(20):
            observed = observed_positive_mask(work, rho=0.10, seed=seed)
            cal_blocks, test_blocks = split_blocks(work["composition_family_pair"].astype(str).tolist(), seed)
            block_series = work["composition_family_pair"].astype(str)
            cal_mask = block_series.isin(cal_blocks).to_numpy()
            test_mask = block_series.isin(test_blocks).to_numpy()
            cal_null = work.loc[cal_mask & ~observed, ["composition_family_pair", "mp_score"]].copy()
            maxima = cal_null.groupby("composition_family_pair", sort=False)["mp_score"].max().astype(float).to_numpy()
            gamma = gamma_star_from_p(1.0 / (len(maxima) + 1.0) if len(maxima) else 1.0)
            test = work.loc[test_mask].sort_values("mp_score", ascending=False).copy()
            if gamma is None or len(maxima) == 0 or len(test) == 0:
                test["_evalue"] = 0.0
            else:
                maxima_sorted = np.sort(maxima)
                scores = test["mp_score"].to_numpy(dtype=float)
                exceed = len(maxima_sorted) - np.searchsorted(maxima_sorted, scores, side="left")
                p_block = (1.0 + exceed) / (len(maxima_sorted) + 1.0)
                test["_evalue"] = gamma * (np.minimum(1.0, p_block) ** (gamma - 1.0))
            pool = test.head(budget).copy()
            released, best_ratio = scs_release_count(pool["_evalue"].to_numpy(dtype=float), alpha=0.10, budget=budget)
            selected = pool.iloc[np.argsort(pool["_evalue"].to_numpy(dtype=float))[::-1][:released]].copy() if released else pool.iloc[[]].copy()
            rows.append(
                {
                    "alpha": 0.10,
                    "rho": 0.10,
                    "K": budget,
                    "seed": seed,
                    "released": int(released),
                    "best_mass_ratio": float(best_ratio),
                    "alex_FTR_if_released": float((~selected["alex_stable_exact"].astype(bool)).mean()) if released else 0.0,
                    "mp_FTR_if_released": float((~selected["mp_stable_exact"].astype(bool)).mean()) if released else 0.0,
                    "claim_scope": "strict_SCS_portability_check_not_fig4c_bar",
                }
            )
    return pd.DataFrame(rows)


def write_closeout(fig4c: pd.DataFrame, recon: pd.DataFrame, scs: pd.DataFrame) -> None:
    selected = fig4c[fig4c["selection_rule"].eq("MP_native_exact_stable_release_ehull_le_0")].iloc[0]
    full = fig4c[fig4c["selection_rule"].eq("full_MP_Alex_strict_denominator")].iloc[0]
    scs_nonempty = int((scs["released"].astype(int) > 0).sum())
    text = f"""# Fig. 4c Selection-Conditioned MP-vs-Alex Diagnostic

## Question

Does the high WBM-vs-Alex discordance case persist when the same release-style
conditioning is applied inside the MP-vs-Alex exact-match denominator?

## Definition

The primary panel-c bar uses a portable source-native release rule:

```text
denominator: MP-vs-Alex strict-structure matches
score/source label: MP energy_above_hull
selection rule: MP energy_above_hull <= 0 eV/atom
evaluation: binary exact-stability disagreement with Alex labels
```

This is a diagnostic reconciliation bar. It is not a new PARC guarantee and not
a three-source validation.

A strict SCS/PARC portability check was also run on this small denominator at
`alpha=0.10`, `rho=0.10` and `K in {{50,100,124,200,287}}`. It produced
`{scs_nonempty}` non-empty seed rows out of `{len(scs)}`. Thus the panel-c bar
uses source-native release conditioning rather than a certified PARC release.

## Result

```text
full MP-vs-Alex denominator discordance: {float(full['discordance_rate']):.3f} (n={int(full['n_selected'])})
MP-native exact-stable selected discordance: {float(selected['discordance_rate']):.3f} (n={int(selected['n_selected'])})
MP-selected but Alex-unstable count: {int(selected['mp_selected_but_alex_unstable_n'])}
```

Interpretation: selection conditioning within the MP-vs-Alex denominator raises
discordance modestly relative to the full denominator, but it remains far below
the earlier WBM-vs-Alex/PARC-style case. The reconciliation is therefore mostly
a source-pair / denominator effect, with a smaller MP-native selection effect.
"""
    (OUT / "FIG4C_SELECTION_CONDITIONED_MP_ALEX_CLOSEOUT.md").write_text(text, encoding="utf-8")


def main() -> None:
    matches = load_matches()
    fig4c = build_rows(matches)
    recon = build_reconciliation(fig4c)
    scs = compute_scs_portability(matches)
    fig4c.to_csv(OUT / "table_fig4c_selection_conditioned_mp_alex.csv", index=False)
    recon.to_csv(OUT / "table_fig4_reconciliation_bars.csv", index=False)
    scs.to_csv(OUT / "table_fig4c_scs_portability_check.csv", index=False)
    write_closeout(fig4c, recon, scs)
    write_manifest()


if __name__ == "__main__":
    main()
