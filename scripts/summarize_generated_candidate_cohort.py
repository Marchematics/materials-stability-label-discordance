#!/usr/bin/env python3
"""Summarize a generated crystal cohort while retaining matching tiers explicitly.

Label-view yields are evaluated only on candidates with an exact SourceAware
structure match. Formula-only and unmatched candidates remain in the cohort
accounting table and are never folded into a label-view yield denominator.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
VIEWS = ("mp_native", "alexmp20_native", "alex_pbe_native", "common_pool", "audit_view", "consensus")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    cohort = pd.read_parquet(args.candidates)
    required = {"candidate_id", "cleaning_status", "match_tier"}
    missing = required - set(cohort.columns)
    if missing:
        raise ValueError(f"Candidate table is missing required columns: {sorted(missing)}")

    input_n = len(cohort)
    accepted = cohort.loc[cohort.cleaning_status.eq("accepted")].copy()
    exact = accepted.loc[accepted.match_tier.eq("exact_structure")].copy()
    formula_only = accepted.loc[accepted.match_tier.eq("formula_only_or_unmatched")].copy()
    duplicate_n = int(cohort.cleaning_status.eq("duplicate").sum())
    invalid_n = int(cohort.cleaning_status.eq("invalid_structure").sum())

    accounting = pd.DataFrame(
        [
            {"cohort_partition": "input", "n": input_n, "fraction_of_input": 1.0},
            {"cohort_partition": "accepted", "n": len(accepted), "fraction_of_input": rate(len(accepted), input_n)},
            {"cohort_partition": "exact_sourceaware_match", "n": len(exact), "fraction_of_input": rate(len(exact), input_n)},
            {"cohort_partition": "formula_only_or_unmatched", "n": len(formula_only), "fraction_of_input": rate(len(formula_only), input_n)},
            {"cohort_partition": "duplicate", "n": duplicate_n, "fraction_of_input": rate(duplicate_n, input_n)},
            {"cohort_partition": "invalid_structure", "n": invalid_n, "fraction_of_input": rate(invalid_n, input_n)},
        ]
    )
    accounting.to_csv(args.out / "generated_candidate_cohort_accounting.csv", index=False)

    yields: list[dict[str, object]] = []
    for view in VIEWS:
        label_col, evaluable_col = f"{view}_label", f"{view}_evaluable"
        if label_col not in exact.columns:
            evaluable = exact.iloc[0:0]
        else:
            evaluable = exact.copy()
            if evaluable_col in evaluable.columns:
                evaluable = evaluable.loc[evaluable[evaluable_col].fillna(False).astype(bool)]
            evaluable = evaluable.loc[evaluable[label_col].notna()]
        stable_n = int((evaluable[label_col].astype(bool)).sum()) if label_col in evaluable else 0
        yields.append(
            {
                "label_view": view,
                "match_tier": "exact_structure",
                "evaluable_exact_match_n": len(evaluable),
                "stable_exact_match_n": stable_n,
                "stable_yield_exact_match": rate(stable_n, len(evaluable)),
            }
        )
    pd.DataFrame(yields).to_csv(args.out / "generated_candidate_exact_match_label_yields.csv", index=False)

    metadata = {
        "candidate_table": str(args.candidates),
        "input_structure_n": input_n,
        "accepted_n": len(accepted),
        "exact_sourceaware_match_n": len(exact),
        "formula_only_or_unmatched_n": len(formula_only),
        "duplicate_n": duplicate_n,
        "invalid_n": invalid_n,
        "label_yield_population": "accepted candidates with exact_structure match_tier only",
    }
    (args.out / "generated_candidate_summary_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(accounting.to_string(index=False))


if __name__ == "__main__":
    main()
