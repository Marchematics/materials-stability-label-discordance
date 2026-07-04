"""
C4: WBM-Alexandria probe with explicit CI.

Promote the n=270 WBM-Alex exact-match measurement to main-text with:
- Binomial CI for discordance rate
- Explicit n, CI, and underpowered caveat
- Comparison to full MP-Alex denominator discordance

Also build a Matbench-Discovery-aligned perspective: what does a WBM-level
structure selection imply for label discordance?
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path("")
OUT = ROOT / "outputs" / "milestones" / "benchmark_impact_label_source_choice"


def wilson_ci(n: int, k: int, alpha: float = 0.05) -> tuple[float, float, float]:
    """Wilson score interval for binomial proportion."""
    p = k / n
    z = stats.norm.ppf(1 - alpha / 2)
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return p, center - margin, center + margin


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # WBM-Alex probe
    n_wbm = 270
    k_disc = 141
    wbm_stable = 204
    alex_stable = 71

    p, ci_lo, ci_hi = wilson_ci(n_wbm, k_disc)

    # Full MP-Alex denominator
    n_full = 43139
    k_full = 5060
    p_full, ci_lo_full, ci_hi_full = wilson_ci(n_full, k_full)

    # Expected discordance under full-denominator rate
    expected_disc = int(n_wbm * p_full)
    # Binomial test: is WBM rate significantly different from full rate?
    from scipy.stats import binomtest
    bt = binomtest(k_disc, n_wbm, p_full, alternative="two-sided")

    rows = [
        {
            "denominator": "WBM-Alex exact-match probe",
            "n": n_wbm,
            "discordant_n": k_disc,
            "discordance_rate": p,
            "ci_low_95": ci_lo,
            "ci_high_95": ci_hi,
            "mp_stable_n": wbm_stable,
            "alex_stable_n": alex_stable,
            "mp_stable_rate": wbm_stable / n_wbm,
            "alex_stable_rate": alex_stable / n_wbm,
            "base_rate_gap_pp": (wbm_stable - alex_stable) / n_wbm * 100,
            "comparison_to_full_rate_p": p_full,
            "binomial_p_vs_full": bt.pvalue,
            "interpretation": (
                f"WBM-level discordance {p:.3f} [{ci_lo:.3f}, {ci_hi:.3f}] is substantially "
                f"higher than full-denominator rate {p_full:.3f} [{ci_lo_full:.3f}, {ci_hi_full:.3f}], "
                f"reflecting selection bias: WBM structures are enriched near the convex hull. "
                f"n={n_wbm} is underpowered for model-ranking claims. "
                f"Report as case-study contrast, not as headline baseline."
            ),
            "claim_scope": "main_text_case_study_with_explicit_n_and_ci",
        },
        {
            "denominator": "Full MP-Alex strict-match denominator",
            "n": n_full,
            "discordant_n": k_full,
            "discordance_rate": p_full,
            "ci_low_95": ci_lo_full,
            "ci_high_95": ci_hi_full,
            "mp_stable_n": 16872,
            "alex_stable_n": 14676,
            "mp_stable_rate": 16872 / n_full,
            "alex_stable_rate": 14676 / n_full,
            "base_rate_gap_pp": (16872 - 14676) / n_full * 100,
            "comparison_to_full_rate_p": "",
            "binomial_p_vs_full": "",
            "interpretation": "Primary denominator result. 43,139 strict matches, 11.73% discordance.",
            "claim_scope": "primary_evidence_full_denominator",
        },
    ]

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "table_wbm_alex_denominator_ci.csv", index=False)
    print(df.to_string(index=False))
    print(f"\nWrote to {OUT / 'table_wbm_alex_denominator_ci.csv'}")


if __name__ == "__main__":
    main()
