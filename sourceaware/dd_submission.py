"""Digital Discovery submission data products.

This module is deliberately limited to the frozen Phase 1/2 public-source
evidence. It never reads the NMI-upgrade or referee-DFT scaffold trees.
"""
from __future__ import annotations

from itertools import combinations
from pathlib import Path
import hashlib
import json
import math

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PHASE1 = ROOT / "outputs" / "phase1_v2"
DEFAULT_PHASE2 = ROOT / "outputs" / "phase2_v1"
DEFAULT_OUT = ROOT / "outputs" / "dd_submission_v2"

REAL_MODELS = ("ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP")
PRIMARY_LABEL_VIEWS = (
    "mp_native",
    "alexmp20_native",
    "alex_pbe_native",
    "common_pool",
    "consensus",
    "audit_view",
)
DISCOVERY_LABEL_VIEWS = ("mp_native", "consensus", "audit_view")
K_GRID = (100, 300, 500, 1000, 5000, 10000)
PRIMARY_METRICS = ("f1", "auprc", "auroc", "balanced_accuracy", "stable_yield@1000")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_metric(fn, y: np.ndarray, score: np.ndarray) -> float:
    if len(y) == 0 or len(np.unique(y)) < 2:
        return math.nan
    try:
        return float(fn(y, score))
    except Exception:
        return math.nan


def _threshold_matched_predictions(frame: pd.DataFrame) -> np.ndarray:
    """Select as many top-ranked rows as there are positive labels.

    This reproduces the frozen Phase 1/2 classification convention. Scores
    remain ranking diagnostics; this is not a calibrated 0 eV/atom threshold.
    """
    n_positive = int(frame["label"].astype(bool).sum())
    pred = np.zeros(len(frame), dtype=bool)
    if n_positive:
        order = np.lexsort((frame["row_id"].astype(str).to_numpy(), -frame["score"].to_numpy()))
        pred[order[:n_positive]] = True
    return pred


def load_label_table(phase1: Path = DEFAULT_PHASE1) -> pd.DataFrame:
    required = {
        "row_id",
        "chemical_system",
        "label_view",
        "label",
        "is_uncertain",
        "is_evaluable",
        "source_native_mp_ehull",
    }
    labels = pd.read_parquet(phase1 / "labels_by_view.parquet")
    missing = required - set(labels.columns)
    if missing:
        raise ValueError(f"labels_by_view.parquet missing columns: {sorted(missing)}")
    return labels


def denominator_summary(phase1: Path = DEFAULT_PHASE1, phase2: Path = DEFAULT_PHASE2) -> pd.DataFrame:
    """Return manuscript terminology without mutating frozen Phase 1 files."""
    rows = [
        ("F0", "formula-support catalogue", phase1 / "denominator_d0_formula.parquet", "formula_support_not_exact_denominator"),
        ("D1", "MP--alex-mp-20 exact", phase1 / "denominator_d1_mp_alexmp20_exact.parquet", "exact_structure_denominator"),
        ("D2", "three-source single-match exact", phase1 / "denominator_d2_triple_single_match.parquet", "primary_label_denominator"),
        ("D4", "source-union target/status", phase1 / "denominator_d4_source_union_pool.parquet", "diagnostic_target_set"),
        ("D5", "four-real-model complete", phase1 / "denominator_d5_model_complete.parquet", "primary_exact_model_denominator"),
    ]
    out = []
    for identifier, name, path, role in rows:
        frame = pd.read_parquet(path)
        out.append(
            {
                "set_id": identifier,
                "set_name": name,
                "n_rows": int(len(frame)),
                "n_columns": int(len(frame.columns)),
                "role": role,
                "frozen_input": str(path.relative_to(ROOT)),
                "sha256": sha256_file(path),
            }
        )
    return pd.DataFrame(out)


def pairwise_native_conflicts(phase1: Path = DEFAULT_PHASE1) -> pd.DataFrame:
    labels = load_label_table(phase1)
    views = ["mp_native", "alexmp20_native", "alex_pbe_native"]
    wide = labels[labels["label_view"].isin(views)].pivot(index="row_id", columns="label_view", values="label")
    pairs = [
        ("MP vs official Alexandria-PBE", "mp_native", "alex_pbe_native"),
        ("alex-mp-20 vs official Alexandria-PBE", "alexmp20_native", "alex_pbe_native"),
        ("MP vs alex-mp-20", "mp_native", "alexmp20_native"),
    ]
    rows = []
    for name, a, b in pairs:
        valid = wide[a].notna() & wide[b].notna()
        n = int(valid.sum())
        conflicts = int(wide.loc[valid, a].ne(wide.loc[valid, b]).sum())
        rows.append(
            {
                "source_pair": name,
                "denominator": "D2",
                "denominator_n": n,
                "conflict_n": conflicts,
                "conflict_rate": conflicts / n,
            }
        )

    strict_path = ROOT / "outputs" / "milestones" / "materials_label_discordance_full_mp_alex_43984" / "table_full_mp_alex_structure_matches.csv"
    if strict_path.exists():
        strict = pd.read_csv(strict_path, low_memory=False)
        if "match_status" in strict.columns:
            strict = strict[strict["match_status"].eq("strict_structure_match")].copy()
        cols = set(strict.columns)
        mp_col = next((c for c in ["mp_stable", "mp_label", "mp_stable_exact"] if c in cols), None)
        alex_col = next((c for c in ["alex_stable", "alex_label", "alex_stable_exact"] if c in cols), None)
        if mp_col and alex_col:
            valid = strict[mp_col].notna() & strict[alex_col].notna()
            conflict = strict.loc[valid, mp_col].astype(bool).ne(strict.loc[valid, alex_col].astype(bool))
            rows.append(
                {
                    "source_pair": "MP vs alex-mp-20 (strict full)",
                    "denominator": "D1",
                    "denominator_n": int(valid.sum()),
                    "conflict_n": int(conflict.sum()),
                    "conflict_rate": float(conflict.mean()),
                }
            )
    if not any(row["denominator"] == "D1" for row in rows):
        rows.append(
            {
                "source_pair": "MP vs alex-mp-20 (strict full)",
                "denominator": "D1",
                "denominator_n": 43139,
                "conflict_n": 5060,
                "conflict_rate": 5060 / 43139,
            }
        )
    return pd.DataFrame(rows)


def conflict_decomposition(phase1: Path = DEFAULT_PHASE1) -> pd.DataFrame:
    """Build the identity-closing native-to-common-pool decomposition."""
    hull = pd.read_parquet(phase1 / "source_union_hull_labels.parquet")
    native = hull["source_native_mp_label"].ne(hull["source_native_alex_pbe_label"])
    mechanism = hull["common_pool_mechanism_component"].fillna("")
    unreconstructable = native & mechanism.eq("unreconstructable_missing_formation_energy")
    phase_sensitive = native & mechanism.eq("phase_pool_component_removed_by_common_pool")
    persistent = native & mechanism.eq("energy_workflow_component_persists_under_common_pool")
    hidden = (~native) & mechanism.eq("hidden_common_pool_energy_workflow_component")
    reconstructable_native = phase_sensitive | persistent
    common_pool_conflicts = persistent | hidden

    counts = {
        "native_full": int(native.sum()),
        "reconstructable_native": int(reconstructable_native.sum()),
        "phase_pool_sensitive": int(phase_sensitive.sum()),
        "persistent": int(persistent.sum()),
        "common_pool_conflicts": int(common_pool_conflicts.sum()),
        "hidden_common_pool": int(hidden.sum()),
        "unreconstructable": int(unreconstructable.sum()),
    }
    identities = {
        "reconstructable_native_equals_phase_plus_persistent": counts["reconstructable_native"] == counts["phase_pool_sensitive"] + counts["persistent"],
        "common_pool_conflicts_equals_persistent_plus_hidden": counts["common_pool_conflicts"] == counts["persistent"] + counts["hidden_common_pool"],
        "native_full_equals_reconstructable_plus_unreconstructable": counts["native_full"] == counts["reconstructable_native"] + counts["unreconstructable"],
    }
    if not all(identities.values()):
        raise AssertionError(f"conflict decomposition does not close: {counts}; {identities}")
    labels = {
        "native_full": "native MP--Alex-PBE conflicts",
        "reconstructable_native": "native conflicts reconstructable in matched common pool",
        "phase_pool_sensitive": "phase-pool-sensitive native conflicts",
        "persistent": "persistent native conflicts",
        "common_pool_conflicts": "matched common-pool conflicts",
        "hidden_common_pool": "hidden common-pool conflicts",
        "unreconstructable": "native conflicts unreconstructable in matched common pool",
    }
    return pd.DataFrame(
        [
            {
                "component": key,
                "display_name": labels[key],
                "n": value,
                "d2_denominator_n": int(len(hull)),
                "fraction_of_d2": value / len(hull),
                **identities,
            }
            for key, value in counts.items()
        ]
    )


def _primary_rows_and_scores(phase1: Path, phase2: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    d5 = pd.read_parquet(phase1 / "denominator_d5_model_complete.parquet")
    scores = pd.read_parquet(phase2 / "model_scores" / "all_model_scores_long.parquet")
    scores = scores[scores["model_name"].isin(REAL_MODELS)].copy()
    scores = scores[scores["row_id"].isin(set(d5["row_id"]))]
    scores["score"] = pd.to_numeric(scores["score_standardized"], errors="coerce")
    scores = scores.dropna(subset=["score"])
    duplicate = scores.duplicated(["model_name", "row_id"], keep=False)
    if duplicate.any():
        raise AssertionError("duplicate real-model score rows in primary exact denominator")
    coverage = scores.groupby("model_name")["row_id"].nunique().reindex(REAL_MODELS)
    if not coverage.eq(len(d5)).all():
        raise AssertionError(f"primary real-model coverage mismatch: {coverage.to_dict()}, D5={len(d5)}")
    return d5, scores


def exact_discovery_curves(
    phase1: Path = DEFAULT_PHASE1,
    phase2: Path = DEFAULT_PHASE2,
    label_views: tuple[str, ...] = DISCOVERY_LABEL_VIEWS,
) -> pd.DataFrame:
    """Compute cumulative discovery outcomes at every observed rank."""
    d5, scores = _primary_rows_and_scores(phase1, phase2)
    labels = load_label_table(phase1)
    labels = labels[labels["label_view"].isin(label_views) & labels["row_id"].isin(set(d5["row_id"]))]
    rows: list[pd.DataFrame] = []
    for model in REAL_MODELS:
        model_scores = scores[scores["model_name"].eq(model)][["row_id", "score"]]
        for view in label_views:
            lab = labels[labels["label_view"].eq(view)][["row_id", "label", "is_uncertain", "is_evaluable"]]
            merged = model_scores.merge(lab, on="row_id", how="inner", validate="one_to_one")
            merged = merged[merged["is_evaluable"]].copy()
            merged = merged.sort_values(["score", "row_id"], ascending=[False, True], kind="mergesort").reset_index(drop=True)
            merged["rank"] = np.arange(1, len(merged) + 1, dtype=np.int32)
            stable = merged["label"].astype(bool).astype(np.int32).to_numpy()
            uncertain = merged["is_uncertain"].astype(bool).astype(np.int32).to_numpy()
            cumulative_stable = np.cumsum(stable)
            cumulative_uncertain = np.cumsum(uncertain)
            total_stable = int(stable.sum())
            merged["cumulative_stable_n"] = cumulative_stable
            merged["total_stable_n"] = total_stable
            merged["precision"] = cumulative_stable / merged["rank"].to_numpy()
            merged["stable_yield"] = merged["precision"]
            merged["recall"] = cumulative_stable / total_stable if total_stable else np.nan
            merged["uncertain_fraction"] = cumulative_uncertain / merged["rank"].to_numpy()
            merged["model_name"] = model
            merged["label_view"] = view
            merged["denominator"] = "D5_primary_exact"
            merged["curve_method"] = "row_level_exact_cumulative_no_interpolation"
            rows.append(merged[["denominator", "model_name", "label_view", "rank", "row_id", "score", "cumulative_stable_n", "total_stable_n", "precision", "recall", "stable_yield", "uncertain_fraction", "curve_method"]])
    return pd.concat(rows, ignore_index=True)


def exact_primary_metrics(
    phase1: Path = DEFAULT_PHASE1,
    phase2: Path = DEFAULT_PHASE2,
    label_views: tuple[str, ...] = PRIMARY_LABEL_VIEWS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    d5, scores = _primary_rows_and_scores(phase1, phase2)
    labels = load_label_table(phase1)
    labels = labels[labels["label_view"].isin(label_views) & labels["row_id"].isin(set(d5["row_id"]))]
    metric_rows: list[dict[str, object]] = []
    topk_rows: list[dict[str, object]] = []
    for model in REAL_MODELS:
        model_scores = scores[scores["model_name"].eq(model)][["row_id", "score"]]
        for view in label_views:
            lab = labels[labels["label_view"].eq(view)][["row_id", "label", "is_uncertain", "is_evaluable"]]
            merged = model_scores.merge(lab, on="row_id", how="inner", validate="one_to_one")
            merged = merged[merged["is_evaluable"]].copy()
            merged = merged.sort_values(["score", "row_id"], ascending=[False, True], kind="mergesort").reset_index(drop=True)
            y = merged["label"].astype(bool).astype(int).to_numpy()
            score = merged["score"].to_numpy(dtype=float)
            pred = _threshold_matched_predictions(merged)
            metric_rows.append(
                {
                    "denominator": "D5_primary_exact",
                    "model_name": model,
                    "label_view": view,
                    "n": int(len(merged)),
                    "positive_n": int(y.sum()),
                    "positive_rate": float(y.mean()),
                    "f1": float(f1_score(y, pred, zero_division=0)),
                    "precision": float(precision_score(y, pred, zero_division=0)),
                    "recall": float(recall_score(y, pred, zero_division=0)),
                    "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
                    "auroc": _safe_metric(roc_auc_score, y, score),
                    "auprc": _safe_metric(average_precision_score, y, score),
                    "score_interpretation": "diagnostic_ranking_not_calibrated_source_comparable_hull_distance",
                }
            )
            total_positive = int(y.sum())
            for k in K_GRID:
                top = merged.head(min(k, len(merged)))
                stable_n = int(top["label"].astype(bool).sum())
                topk_rows.append(
                    {
                        "denominator": "D5_primary_exact",
                        "model_name": model,
                        "label_view": view,
                        "K": k,
                        "K_effective": int(len(top)),
                        "n_ranked": int(len(merged)),
                        "stable_n": stable_n,
                        "stable_yield_at_k": stable_n / len(top),
                        "precision_at_k": stable_n / len(top),
                        "recall_at_k": stable_n / total_positive if total_positive else math.nan,
                        "uncertain_fraction_at_k": float(top["is_uncertain"].astype(bool).mean()),
                    }
                )
    return pd.DataFrame(metric_rows), pd.DataFrame(topk_rows)


def uncertainty_dominance_tables(metrics: pd.DataFrame, topk: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    long_parts = []
    for metric in ("f1", "auprc", "auroc", "balanced_accuracy"):
        part = metrics[["model_name", "label_view", metric]].rename(columns={metric: "metric_value"})
        part["metric"] = metric
        long_parts.append(part)
    part = topk[topk["K"].eq(1000)][["model_name", "label_view", "stable_yield_at_k"]].rename(columns={"stable_yield_at_k": "metric_value"})
    part["metric"] = "stable_yield@1000"
    long_parts.append(part)
    long = pd.concat(long_parts, ignore_index=True)

    rows = []
    for metric, metric_frame in long.groupby("metric"):
        spread_by_view = metric_frame.groupby("label_view")["metric_value"].agg(lambda s: float(s.max() - s.min()))
        reference_margin = float(spread_by_view.median())
        for model, model_frame in metric_frame.groupby("model_name"):
            band = float(model_frame["metric_value"].max() - model_frame["metric_value"].min())
            rows.append(
                {
                    "model_name": model,
                    "metric": metric,
                    "label_view_band": band,
                    "between_model_margin_median": reference_margin,
                    "uncertainty_dominance_ratio": band / reference_margin if reference_margin else math.inf,
                    "label_band_exceeds_between_model_margin": bool(band > reference_margin),
                    "n_label_views": int(model_frame["label_view"].nunique()),
                }
            )
    dominance = pd.DataFrame(rows)
    ranks = long.copy()
    ranks["rank"] = ranks.groupby(["metric", "label_view"])["metric_value"].rank(method="min", ascending=False).astype(int)
    ranks = ranks.sort_values(["metric", "label_view", "rank", "model_name"])
    slope = ranks[ranks["metric"].eq("f1") & ranks["label_view"].isin(["mp_native", "alex_pbe_native", "common_pool", "consensus", "audit_view"])].copy()
    return dominance, ranks, slope


def rolling_conflict_table(
    phase1: Path = DEFAULT_PHASE1,
    window_ev: float = 0.040,
    step_ev: float = 0.0025,
    x_max_ev: float = 0.20,
    min_n: int = 1000,
    ci_level: float = 0.95,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    """Compute 40 meV rolling rates and Wilson binomial intervals."""
    labels = load_label_table(phase1)
    views = ["mp_native", "alexmp20_native", "alex_pbe_native"]
    wide_labels = labels[labels["label_view"].isin(views)].pivot(index="row_id", columns="label_view", values="label")
    base = labels.drop_duplicates("row_id").set_index("row_id")[["chemical_system", "source_native_mp_ehull"]]
    wide = base.join(wide_labels).dropna(subset=["source_native_mp_ehull", *views])
    pair_defs = [
        ("MP vs official Alexandria-PBE", "mp_native", "alex_pbe_native"),
        ("alex-mp-20 vs official Alexandria-PBE", "alexmp20_native", "alex_pbe_native"),
        ("MP vs alex-mp-20", "mp_native", "alexmp20_native"),
    ]
    z = 1.959963984540054
    if ci_level != 0.95:
        raise ValueError("only a 95% Wilson interval is currently implemented")
    centers = np.arange(0.0, x_max_ev + step_ev / 2, step_ev)
    x = wide["source_native_mp_ehull"].astype(float)
    rows: list[dict[str, object]] = []
    for center in centers:
        lo = max(0.0, center - window_ev / 2)
        hi = center + window_ev / 2
        mask = x.between(lo, hi, inclusive="both")
        n = int(mask.sum())
        for name, a, b in pair_defs:
            switched = wide.loc[mask, a].ne(wide.loc[mask, b])
            successes = int(switched.sum())
            rate = successes / n if n else math.nan
            if n:
                denom = 1 + z * z / n
                centre_adj = (rate + z * z / (2 * n)) / denom
                half = z * math.sqrt(rate * (1 - rate) / n + z * z / (4 * n * n)) / denom
                ci_low, ci_high = max(0.0, centre_adj - half), min(1.0, centre_adj + half)
            else:
                ci_low = ci_high = math.nan
            supported = n >= min_n
            rows.append(
                {
                    "reference_mp_native_e_above_hull_eV": float(center),
                    "window_lower_eV": float(lo),
                    "window_upper_eV": float(hi),
                    "window_width_eV": float(window_ev),
                    "source_pair": name,
                    "n_rows": n,
                    "switch_n": successes,
                    "endpoint_switch_rate": rate if supported else math.nan,
                    "ci_low": ci_low if supported else math.nan,
                    "ci_high": ci_high if supported else math.nan,
                    "supported": supported,
                    "minimum_n": min_n,
                    "interval_method": "Wilson binomial 95% confidence interval",
                }
            )
    rolling = pd.DataFrame(rows)
    bins = np.arange(0.0, x_max_ev + step_ev, step_ev)
    counts, edges = np.histogram(x[(x >= 0) & (x <= x_max_ev)], bins=bins)
    density = pd.DataFrame({"bin_left_eV": edges[:-1], "bin_right_eV": edges[1:], "bin_center_eV": (edges[:-1] + edges[1:]) / 2, "row_count": counts})
    metadata = {
        "reference_axis": "MP-native e_above_hull",
        "window_definition": "closed interval [max(0, centre-20 meV), centre+20 meV]",
        "window_width_eV": window_ev,
        "step_eV": step_ev,
        "x_max_eV": x_max_ev,
        "minimum_n": min_n,
        "interval_method": "Wilson binomial 95% confidence interval",
        "bootstrap_seed": None,
        "bootstrap_iterations": 0,
        "bootstrap_note": "not applicable because binomial intervals, not bootstrap intervals, are used",
        "under_supported_windows": "masked",
    }
    return rolling, density, metadata


def candidate_claim_tables(phase2: Path = DEFAULT_PHASE2) -> tuple[pd.DataFrame, pd.DataFrame]:
    consequence = pd.read_csv(phase2 / "generative" / "generated_pipeline_consequence_summary.csv")
    match = pd.read_csv(phase2 / "generative" / "generated_candidate_match_quality_by_pipeline.csv")
    exact = consequence[consequence["matched_n"].fillna(0).gt(0)].copy()
    unsupported = match[match["exact_sourceaware_match_n"].fillna(0).eq(0)].copy()
    return exact, unsupported


def rank_flip_normalisation(phase2: Path = DEFAULT_PHASE2) -> pd.DataFrame:
    flips = pd.read_csv(phase2 / "model_metrics" / "pairwise_complete_label_dependent_inversions.csv")
    margins = pd.read_csv(phase2 / "model_metrics" / "pairwise_complete_model_margins.csv")

    def scope_row(name: str, model_filter: set[str] | None) -> dict[str, object]:
        f = flips if model_filter is None else flips[flips["model_a"].isin(model_filter) & flips["model_b"].isin(model_filter)]
        m = margins if model_filter is None else margins[margins["model_a"].isin(model_filter) & margins["model_b"].isin(model_filter)]
        possible = 0
        for _, group in m.groupby(["model_a", "model_b", "metric"]):
            possible += math.comb(int(group["label_view"].nunique()), 2)
        return {
            "scope": name,
            "winner_flip_n": int(len(f)),
            "possible_pairwise_label_view_comparisons_n": int(possible),
            "winner_flip_rate": len(f) / possible if possible else math.nan,
            "model_pair_n": int(m[["model_a", "model_b"]].drop_duplicates().shape[0]),
            "metric_n": int(m["metric"].nunique()),
            "label_view_n": int(m["label_view"].nunique()),
            "guardrail": "aggregate includes baselines/oracles" if model_filter is None else "four real SourceAware-scored models only",
        }
    return pd.DataFrame([scope_row("aggregate_diagnostic", None), scope_row("real_models_only", set(REAL_MODELS))])


def build_claims(phase1: Path = DEFAULT_PHASE1, phase2: Path = DEFAULT_PHASE2) -> dict[str, object]:
    denom = denominator_summary(phase1, phase2).set_index("set_id")
    conflicts = pairwise_native_conflicts(phase1)
    decomp = conflict_decomposition(phase1).set_index("component")
    rank_audit = pd.read_csv(phase2 / "rank_inversions" / "real_model_rank_claim_audit.csv")
    pair_norm = rank_flip_normalisation(phase2).set_index("scope")
    exact_candidates, unsupported_candidates = candidate_claim_tables(phase2)
    candidate_consequence = pd.read_csv(phase2 / "generative" / "generated_pipeline_consequence_summary.csv").set_index("pipeline_name")
    candidate_match = pd.read_csv(phase2 / "generative" / "generated_candidate_match_quality_by_pipeline.csv").set_index("pipeline_name")
    global_metrics = {"f1", "auprc", "auroc", "balanced_accuracy", "precision", "recall"}
    global_audit = rank_audit[rank_audit["metric"].isin(global_metrics)]
    lower_rank_rows_all = int(rank_audit["claim_interpretation"].eq("lower_rank_real_model_order_changes").sum())
    top_global = int(global_audit["top_real_model_inversion"].sum())
    pair_records = {row["source_pair"]: row for row in conflicts.to_dict("records")}
    full_union_status = json.loads((phase1 / "source_union_hull_status.json").read_text())
    return {
        "evidence_scope": "frozen_phase1_v2_and_phase2_v1_only",
        "guardrails": {
            "homogeneous_dft_referee_truth_labels": False,
            "generated_material_validation": False,
            "complete_full_source_union_hull": False,
            "diagnostic_labels_are_physical_truth": False,
        },
        "denominators": {key: {"n": int(row.n_rows), "name": row.set_name, "role": row.role} for key, row in denom.iterrows()},
        "native_conflicts": {name: {"n": int(row["conflict_n"]), "denominator_n": int(row["denominator_n"]), "rate": float(row["conflict_rate"])} for name, row in pair_records.items()},
        "conflict_decomposition": {key: int(decomp.loc[key, "n"]) for key in ["native_full", "reconstructable_native", "phase_pool_sensitive", "persistent", "common_pool_conflicts", "hidden_common_pool", "unreconstructable"]},
        "conflict_identities": {
            "reconstructable_native = phase_pool_sensitive + persistent": True,
            "common_pool_conflicts = persistent + hidden_common_pool": True,
            "native_full = reconstructable_native + unreconstructable": True,
        },
        "model_evidence": {
            "primary_real_models": list(REAL_MODELS),
            "primary_real_model_n": len(REAL_MODELS),
            "primary_exact_denominator_n": int(denom.loc["D5", "n_rows"]),
            "scores_are_calibrated_source_comparable_hull_distances": False,
            "global_metric_top_model_inversion_rows": top_global,
            "legacy_lower_rank_order_change_rows_all_denominators_metrics": lower_rank_rows_all,
            "aggregate_pairwise_winner_flips": int(pair_norm.loc["aggregate_diagnostic", "winner_flip_n"]),
            "aggregate_pairwise_winner_flip_denominator": int(pair_norm.loc["aggregate_diagnostic", "possible_pairwise_label_view_comparisons_n"]),
            "aggregate_pairwise_winner_flip_rate": float(pair_norm.loc["aggregate_diagnostic", "winner_flip_rate"]),
            "real_model_pairwise_winner_flips": int(pair_norm.loc["real_models_only", "winner_flip_n"]),
            "real_model_pairwise_winner_flip_denominator": int(pair_norm.loc["real_models_only", "possible_pairwise_label_view_comparisons_n"]),
            "real_model_pairwise_winner_flip_rate": float(pair_norm.loc["real_models_only", "winner_flip_rate"]),
        },
        "candidate_evidence": {
            "exact_matched_pipeline_n": int(len(exact_candidates)),
            "formula_only_or_unmatched_pipeline_n": int(len(unsupported_candidates)),
            "claim_scope": "public_sourceaware_candidate_consequence_not_generated_material_validation",
            "chgnet_public_hull_top5000": {
                "candidate_n": int(candidate_consequence.loc["CHGNet_screened_public_hull_top5000", "candidate_n"]),
                "exact_match_n": int(candidate_consequence.loc["CHGNet_screened_public_hull_top5000", "matched_n"]),
                "mp_native_stable_yield": float(candidate_consequence.loc["CHGNet_screened_public_hull_top5000", "mp_native_stable_yield"]),
                "audit_view_stable_yield": float(candidate_consequence.loc["CHGNet_screened_public_hull_top5000", "audit_view_stable_yield"]),
                "source_uncertain_fraction": float(candidate_consequence.loc["CHGNet_screened_public_hull_top5000", "source_uncertain_fraction"]),
                "unmatched_fraction": float(candidate_consequence.loc["CHGNet_screened_public_hull_top5000", "unmatched_fraction"]),
            },
            "mattergen_formula_pool": {
                "candidate_n": int(candidate_match.loc["MatterGen_pilot_5k_public_safe_formulas", "candidate_n"]),
                "exact_match_n": int(candidate_match.loc["MatterGen_pilot_5k_public_safe_formulas", "exact_sourceaware_match_n"]),
                "formula_only_n": int(candidate_match.loc["MatterGen_pilot_5k_public_safe_formulas", "formula_only_overlap_n"]),
                "unmatched_n": int(candidate_match.loc["MatterGen_pilot_5k_public_safe_formulas", "no_formula_overlap_n"]),
            },
            "pgcgm_pool": {
                "candidate_n": int(candidate_match.loc["PGCGM_public_safe_generated_pool", "candidate_n"]),
                "exact_match_n": int(candidate_match.loc["PGCGM_public_safe_generated_pool", "exact_sourceaware_match_n"]),
                "formula_only_n": int(candidate_match.loc["PGCGM_public_safe_generated_pool", "formula_only_overlap_n"]),
                "unmatched_n": int(candidate_match.loc["PGCGM_public_safe_generated_pool", "no_formula_overlap_n"]),
            },
        },
        "full_source_union_status": full_union_status,
    }


def write_claims_outputs(out_dir: Path = DEFAULT_OUT, phase1: Path = DEFAULT_PHASE1, phase2: Path = DEFAULT_PHASE2) -> dict[str, object]:
    out_dir = ensure_dir(out_dir)
    claims = build_claims(phase1, phase2)
    (out_dir / "manuscript_claims.json").write_text(json.dumps(claims, indent=2, sort_keys=True) + "\n")
    d = claims["denominators"]
    c = claims["conflict_decomposition"]
    n = claims["native_conflicts"]
    m = claims["model_evidence"]
    ce = claims["candidate_evidence"]
    lines = [
        "# Manuscript claims audit", "", "Status: **PASS**", "",
        "Evidence scope: frozen `outputs/phase1_v2` and `outputs/phase2_v1` only. NMI/referee scaffolds are excluded.", "",
        "## Denominators", "", *[f"- {key}: {value['n']:,} — {value['name']}" for key, value in d.items()], "",
        "## Conflict identities", "",
        f"- reconstructable_native: {c['reconstructable_native']:,} = phase_pool_sensitive {c['phase_pool_sensitive']:,} + persistent {c['persistent']:,}",
        f"- common_pool_conflicts: {c['common_pool_conflicts']:,} = persistent {c['persistent']:,} + hidden_common_pool {c['hidden_common_pool']:,}",
        f"- native_full: {c['native_full']:,} = reconstructable_native {c['reconstructable_native']:,} + unreconstructable {c['unreconstructable']:,}", "",
        "## Source-native endpoint switches", "", *[f"- {key}: {value['n']:,}/{value['denominator_n']:,} = {100*value['rate']:.2f}%" for key, value in n.items()], "",
        "## Model evidence boundary", "",
        f"- Primary exact models: {', '.join(m['primary_real_models'])} ({m['primary_real_model_n']} models; D5 n={m['primary_exact_denominator_n']:,}).",
        "- All other model entries are external WBM context, artifact inventory, baselines or oracle diagnostics.",
        "- Scores are diagnostic rankings, not calibrated source-comparable hull distances.",
        f"- Full-denominator classification-metric top-model inversion rows: {m['global_metric_top_model_inversion_rows']}.",
        f"- Legacy lower-rank audit rows (all three model denominators and all metric families): {m['legacy_lower_rank_order_change_rows_all_denominators_metrics']:,}.",
        f"- Aggregate diagnostic winner flips: {m['aggregate_pairwise_winner_flips']:,}/{m['aggregate_pairwise_winner_flip_denominator']:,} = {100*m['aggregate_pairwise_winner_flip_rate']:.2f}% (includes baselines/oracles).",
        f"- Real-model-only winner flips: {m['real_model_pairwise_winner_flips']:,}/{m['real_model_pairwise_winner_flip_denominator']:,} = {100*m['real_model_pairwise_winner_flip_rate']:.2f}%.", "",
        "## Guardrails", "",
        "- No homogeneous DFT referee truth labels.",
        "- No generated-material validation.",
        "- No complete full-source-union hull claim.",
        "- Consensus, common-pool, source-union and audit labels are benchmark diagnostics, not physical truth.",
    ]
    (out_dir / "manuscript_claims_audit.md").write_text("\n".join(lines) + "\n")
    macros = {
        "FZeroN": f"{d['F0']['n']:,}",
        "DOneN": f"{d['D1']['n']:,}",
        "DTwoN": f"{d['D2']['n']:,}",
        "DFourN": f"{d['D4']['n']:,}",
        "DFiveN": f"{d['D5']['n']:,}",
        "NativeConflictN": f"{c['native_full']:,}",
        "ReconstructableNativeN": f"{c['reconstructable_native']:,}",
        "PhasePoolSensitiveN": f"{c['phase_pool_sensitive']:,}",
        "PersistentConflictN": f"{c['persistent']:,}",
        "CommonPoolConflictN": f"{c['common_pool_conflicts']:,}",
        "CommonPoolConflictRate": f"{100*c['common_pool_conflicts']/d['D2']['n']:.1f}",
        "HiddenCommonPoolN": f"{c['hidden_common_pool']:,}",
        "UnreconstructableNativeN": f"{c['unreconstructable']:,}",
        "RealModelN": str(m["primary_real_model_n"]),
        "LowerRankAuditRows": f"{m['legacy_lower_rank_order_change_rows_all_denominators_metrics']:,}",
        "AggregateWinnerFlips": f"{m['aggregate_pairwise_winner_flips']:,}",
        "AggregateWinnerFlipDenominator": f"{m['aggregate_pairwise_winner_flip_denominator']:,}",
        "AggregateWinnerFlipRate": f"{100*m['aggregate_pairwise_winner_flip_rate']:.2f}",
        "RealWinnerFlips": f"{m['real_model_pairwise_winner_flips']:,}",
        "RealWinnerFlipDenominator": f"{m['real_model_pairwise_winner_flip_denominator']:,}",
        "RealWinnerFlipRate": f"{100*m['real_model_pairwise_winner_flip_rate']:.2f}",
        "CHGNetPublicExactN": f"{ce['chgnet_public_hull_top5000']['exact_match_n']:,}",
        "CHGNetPublicMPYield": f"{ce['chgnet_public_hull_top5000']['mp_native_stable_yield']:.3f}",
        "CHGNetPublicAuditYield": f"{ce['chgnet_public_hull_top5000']['audit_view_stable_yield']:.3f}",
        "CHGNetPublicUncertain": f"{ce['chgnet_public_hull_top5000']['source_uncertain_fraction']:.3f}",
        "MatterGenFormulaOnlyN": f"{ce['mattergen_formula_pool']['formula_only_n']:,}",
        "MatterGenUnmatchedN": f"{ce['mattergen_formula_pool']['unmatched_n']:,}",
        "PGCGMFormulaOnlyN": f"{ce['pgcgm_pool']['formula_only_n']:,}",
        "PGCGMUnmatchedN": f"{ce['pgcgm_pool']['unmatched_n']:,}",
    }
    for source_name, row in n.items():
        key = {
            "MP vs official Alexandria-PBE": "MPAlexConflictRate",
            "alex-mp-20 vs official Alexandria-PBE": "MatterGenAlexConflictRate",
            "MP vs alex-mp-20": "MPMatterGenConflictRate",
            "MP vs alex-mp-20 (strict full)": "MPMatterGenDOneConflictRate",
        }[source_name]
        macros[key] = f"{100*row['rate']:.1f}"
    tex = ["% Auto-generated by scripts/audit_manuscript_claims.py; do not hand edit."]
    tex.extend(f"\\newcommand{{\\{key}}}{{{value}}}" for key, value in macros.items())
    (out_dir / "manuscript_claims_generated.tex").write_text("\n".join(tex) + "\n")
    return claims
