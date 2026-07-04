from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "outputs" / "milestones" / "materials_label_discordance_full_mp_alex_43984"
OUT = ROOT / "outputs" / "milestones" / "benchmark_impact_label_source_choice"


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


def load_denominator() -> pd.DataFrame:
    df = pd.read_csv(FULL / "table_full_mp_alex_structure_matches.csv")
    df = df[df["match_status"].eq("strict_structure_match")].copy()
    df["mp_e_above_hull"] = pd.to_numeric(df["mp_e_above_hull"], errors="coerce")
    df["alex_e_above_hull"] = pd.to_numeric(df["alex_e_above_hull"], errors="coerce")
    df["mp_stable"] = df["mp_stable_exact"].astype(str).str.lower().eq("true")
    df["alex_stable"] = df["alex_stable_exact"].astype(str).str.lower().eq("true")
    df["discordant"] = df["mp_stable"] != df["alex_stable"]
    return df


def binary_metrics(pred: pd.Series, truth: pd.Series) -> dict[str, float | int]:
    pred = pred.astype(bool)
    truth = truth.astype(bool)
    tp = int((pred & truth).sum())
    fp = int((pred & ~truth).sum())
    fn = int((~pred & truth).sum())
    tn = int((~pred & ~truth).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / len(pred) if len(pred) else 0.0
    balanced_accuracy = 0.5 * (
        (tp / (tp + fn) if tp + fn else 0.0) + (tn / (tn + fp) if tn + fp else 0.0)
    )
    return {
        "n": int(len(pred)),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
        "balanced_accuracy": balanced_accuracy,
    }


def write_confusion(df: pd.DataFrame) -> None:
    rows = []
    for name, mask in {
        "both_stable": df["mp_stable"] & df["alex_stable"],
        "mp_stable_alex_unstable": df["mp_stable"] & ~df["alex_stable"],
        "mp_unstable_alex_stable": ~df["mp_stable"] & df["alex_stable"],
        "both_unstable": ~df["mp_stable"] & ~df["alex_stable"],
    }.items():
        rows.append(
            {
                "label_cell": name,
                "n": int(mask.sum()),
                "fraction": float(mask.mean()),
                "claim_scope": "completed_full_denominator_label_source_impact",
            }
        )
    pd.DataFrame(rows).to_csv(OUT / "table_label_confusion_matrix_full_denominator.csv", index=False)


def write_perfect_source_cross_eval(df: pd.DataFrame) -> None:
    rows = []
    for predictor_name, pred in {
        "perfect_MP_source_labeler": df["mp_stable"],
        "perfect_Alexandria_source_labeler": df["alex_stable"],
    }.items():
        for truth_name, truth in {
            "MP_source_native_truth": df["mp_stable"],
            "Alexandria_source_native_truth": df["alex_stable"],
        }.items():
            row = {
                "predictor": predictor_name,
                "evaluation_label_source": truth_name,
                **binary_metrics(pred, truth),
                "claim_scope": "source_label_transfer_upper_bound_not_ml_model",
            }
            rows.append(row)
    out = pd.DataFrame(rows)
    mp_self = out[
        out["predictor"].eq("perfect_MP_source_labeler")
        & out["evaluation_label_source"].eq("MP_source_native_truth")
    ].iloc[0]
    alex_cross = out[
        out["predictor"].eq("perfect_MP_source_labeler")
        & out["evaluation_label_source"].eq("Alexandria_source_native_truth")
    ].iloc[0]
    out["delta_from_source_native_f1"] = ""
    out.loc[
        out["predictor"].eq("perfect_MP_source_labeler"),
        "delta_from_source_native_f1",
    ] = out.loc[out["predictor"].eq("perfect_MP_source_labeler"), "f1"] - float(mp_self["f1"])
    alex_self = out[
        out["predictor"].eq("perfect_Alexandria_source_labeler")
        & out["evaluation_label_source"].eq("Alexandria_source_native_truth")
    ].iloc[0]
    out.loc[
        out["predictor"].eq("perfect_Alexandria_source_labeler"),
        "delta_from_source_native_f1",
    ] = out.loc[out["predictor"].eq("perfect_Alexandria_source_labeler"), "f1"] - float(alex_self["f1"])
    out.to_csv(OUT / "table_perfect_source_labeler_cross_evaluation.csv", index=False)


def write_topk_source_native_rankings(df: pd.DataFrame) -> None:
    rows = []
    for ranking_name, score_col in {
        "MP_source_native_ehull_rank": "mp_e_above_hull",
        "Alexandria_source_native_ehull_rank": "alex_e_above_hull",
    }.items():
        ranked = df.sort_values([score_col, "material_id"], ascending=[True, True]).reset_index(drop=True)
        for k in [100, 300, 500, 1000, 5000, 10000]:
            sub = ranked.head(k)
            rows.append(
                {
                    "ranking": ranking_name,
                    "K": k,
                    "mp_stable_rate_at_K": float(sub["mp_stable"].mean()),
                    "alex_stable_rate_at_K": float(sub["alex_stable"].mean()),
                    "absolute_stable_rate_shift": abs(
                        float(sub["mp_stable"].mean()) - float(sub["alex_stable"].mean())
                    ),
                    "discordance_at_K": float(sub["discordant"].mean()),
                    "claim_scope": "source_native_oracle_ranking_reference_not_ml_model",
                }
            )
    pd.DataFrame(rows).to_csv(OUT / "table_source_native_ranking_topk_stable_yield.csv", index=False)


def write_conflict_excluded(df: pd.DataFrame) -> None:
    agreement = df[~df["discordant"]].copy()
    conflict = df[df["discordant"]].copy()
    rows = [
        {
            "denominator": "full_strict_MP_Alex",
            "n": int(len(df)),
            "mp_stable_rate": float(df["mp_stable"].mean()),
            "alex_stable_rate": float(df["alex_stable"].mean()),
            "source_conflict_n": int(df["discordant"].sum()),
            "source_conflict_fraction": float(df["discordant"].mean()),
            "claim_scope": "completed_full_denominator_label_source_impact",
        },
        {
            "denominator": "source_agreement_only_conflict_excluded",
            "n": int(len(agreement)),
            "mp_stable_rate": float(agreement["mp_stable"].mean()),
            "alex_stable_rate": float(agreement["alex_stable"].mean()),
            "source_conflict_n": 0,
            "source_conflict_fraction": 0.0,
            "claim_scope": "completed_conflict_excluded_denominator_definition",
        },
        {
            "denominator": "source_conflict_only",
            "n": int(len(conflict)),
            "mp_stable_rate": float(conflict["mp_stable"].mean()),
            "alex_stable_rate": float(conflict["alex_stable"].mean()),
            "source_conflict_n": int(len(conflict)),
            "source_conflict_fraction": 1.0,
            "claim_scope": "completed_source_conflict_burden_definition",
        },
    ]
    pd.DataFrame(rows).to_csv(OUT / "table_conflict_excluded_denominator_metrics.csv", index=False)


def write_interpretation(df: pd.DataFrame) -> None:
    both_stable = int((df["mp_stable"] & df["alex_stable"]).sum())
    mp_only = int((df["mp_stable"] & ~df["alex_stable"]).sum())
    alex_only = int((~df["mp_stable"] & df["alex_stable"]).sum())
    both_unstable = int((~df["mp_stable"] & ~df["alex_stable"]).sum())
    rows = [
        {
            "impact_statement": "binary_label_disagreement_burden",
            "value": float(df["discordant"].mean()),
            "unit": "fraction_of_full_strict_denominator",
            "paper_use": "completed benchmark-label source uncertainty number",
        },
        {
            "impact_statement": "MP_stable_candidates_rejected_by_Alexandria",
            "value": mp_only / int(df["mp_stable"].sum()),
            "unit": "fraction_of_MP_stable_set",
            "paper_use": "upper-bound transfer loss for MP-native stable releases evaluated by Alexandria",
        },
        {
            "impact_statement": "Alexandria_stable_candidates_rejected_by_MP",
            "value": alex_only / int(df["alex_stable"].sum()),
            "unit": "fraction_of_Alexandria_stable_set",
            "paper_use": "upper-bound transfer loss for Alexandria-native stable releases evaluated by MP",
        },
        {
            "impact_statement": "conflict_excluded_denominator_retention",
            "value": (both_stable + both_unstable) / len(df),
            "unit": "fraction_of_full_strict_denominator",
            "paper_use": "cost of source-agreement-only benchmark reporting",
        },
    ]
    pd.DataFrame(rows).to_csv(OUT / "table_metric_shift_interpretation.csv", index=False)


def write_closeout(df: pd.DataFrame) -> None:
    confusion = pd.read_csv(OUT / "table_label_confusion_matrix_full_denominator.csv")
    transfer = pd.read_csv(OUT / "table_perfect_source_labeler_cross_evaluation.csv")
    ranking = pd.read_csv(OUT / "table_source_native_ranking_topk_stable_yield.csv")
    conflict = pd.read_csv(OUT / "table_conflict_excluded_denominator_metrics.csv")
    interpretation = pd.read_csv(OUT / "table_metric_shift_interpretation.csv")
    (OUT / "BENCHMARK_IMPACT_LABEL_SOURCE_CHOICE_CLOSEOUT.md").write_text(
        "# Benchmark Impact of Label-Source Choice\n\n"
        "This completed milestone quantifies benchmark consequences of MP-vs-Alexandria label-source choice on the full 43,139 strict-match denominator. "
        "It deliberately does not claim a full-denominator ML model leaderboard, because full-denominator model scores are not available in the public-safe artifact set. "
        "Instead, it reports source-label transfer limits and source-native ranking references that any downstream benchmark must confront.\n\n"
        "## Label Confusion\n\n"
        f"{confusion.to_markdown(index=False)}\n\n"
        "## Perfect Source-Labeler Cross-Evaluation\n\n"
        f"{transfer.to_markdown(index=False)}\n\n"
        "## Source-Native Ranking Reference\n\n"
        f"{ranking.to_markdown(index=False)}\n\n"
        "## Conflict-Excluded Denominator\n\n"
        f"{conflict.to_markdown(index=False)}\n\n"
        "## Paper-Facing Interpretation\n\n"
        f"{interpretation.to_markdown(index=False)}\n",
        encoding="utf-8",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_denominator()
    write_confusion(df)
    write_perfect_source_cross_eval(df)
    write_topk_source_native_rankings(df)
    write_conflict_excluded(df)
    write_interpretation(df)
    write_closeout(df)
    write_manifest()


if __name__ == "__main__":
    main()
