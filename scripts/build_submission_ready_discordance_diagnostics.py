from __future__ import annotations

import hashlib
import json
import math
import signal
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pymatgen.core import Composition, Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "milestones" / "materials_label_discordance_preregistration"
ALEX_ZIP = Path("/home/waas/paper_experiments/private/mattergen_repo/data-release/alex-mp/alex_mp_20.zip")
WBM_ALEX_MATCHES = Path(
    "/home/waas/paper_experiments/github/Certified-Open-Vocabulary-MOT/outputs/milestones/"
    "materials_alex_mp_a1_a2_validation/table_alex_mp_a2_candidate_matches.csv"
)


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


def load_alex_all() -> pd.DataFrame:
    frames = []
    with zipfile.ZipFile(ALEX_ZIP) as zf:
        for name in ["alex_mp_20/val.csv", "alex_mp_20/train.csv"]:
            with zf.open(name) as f:
                df = pd.read_csv(
                    f,
                    usecols=[
                        "material_id",
                        "reduced_formula",
                        "chemical_system",
                        "num_sites",
                        "cif",
                        "energy_above_hull",
                    ],
                )
                df["alex_source_file"] = name
            frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out["material_id"] = out["material_id"].astype(str)
    out["is_mp_identifier"] = out["material_id"].str.startswith("mp-")
    out["alex_stable_exact"] = pd.to_numeric(out["energy_above_hull"], errors="coerce") <= 0
    return out


def load_mp_alex_matches() -> pd.DataFrame:
    matches = pd.read_csv(OUT / "table_route_b_full_snapshot_matches.csv")
    strict = matches[matches["match_status"].eq("strict_structure_match")].copy()
    strict["mp_e_above_hull"] = pd.to_numeric(strict["mp_e_above_hull"], errors="coerce")
    strict["alex_e_above_hull"] = pd.to_numeric(strict["alex_e_above_hull"], errors="coerce")
    strict["mp_stable_exact"] = strict["mp_stable_exact"].astype(str).str.lower().eq("true")
    strict["alex_stable_exact"] = strict["alex_stable_exact"].astype(str).str.lower().eq("true")
    strict["discordant"] = strict["mp_stable_exact"] != strict["alex_stable_exact"]
    strict["abs_delta_ehull"] = (strict["mp_e_above_hull"] - strict["alex_e_above_hull"]).abs()
    strict["min_abs_ehull"] = np.minimum(strict["mp_e_above_hull"].abs(), strict["alex_e_above_hull"].abs())
    return strict.sort_values("material_id").reset_index(drop=True)


def load_scores() -> pd.DataFrame:
    scores = pd.read_csv(OUT / "table_route_b_full_snapshot_model_scores.csv")
    scores = scores[scores["score_status"].eq("scored")].copy()
    scores["score"] = pd.to_numeric(scores["score"], errors="coerce")
    return scores


def build_denominator_audit(alex: pd.DataFrame, matches_all: pd.DataFrame, strict: pd.DataFrame, scores: pd.DataFrame) -> pd.DataFrame:
    oqmd = pd.read_csv(OUT / "table_mp_alex_oqmd_exact_matches.csv")
    rows = [
        {
            "step": "Alexandria v20 entries",
            "count": int(len(alex)),
            "exclusion_reason": "full alex-mp v20 train+val rows available locally",
        },
        {
            "step": "Alexandria entries with MP identifiers",
            "count": int(alex["is_mp_identifier"].sum()),
            "exclusion_reason": "non-MP Alexandria IDs cannot be queried through MP material_id join",
        },
        {
            "step": "Frozen Route B MP-ID candidates attempted",
            "count": int(len(matches_all)),
            "exclusion_reason": "predeclared minimal MP-vs-Alex rescue subset, not full Alexandria population",
        },
        {
            "step": "MP records successfully queried",
            "count": int((~matches_all["match_status"].eq("missing_mp_record")).sum()),
            "exclusion_reason": "missing/deprecated MP IDs removed",
        },
        {
            "step": "Reduced-formula compatible pairs",
            "count": int((~matches_all["match_status"].eq("missing_mp_record")).sum()),
            "exclusion_reason": "formula screen not a binding exclusion in this artifact; strict StructureMatcher is binding",
        },
        {
            "step": "StructureMatcher strict matches",
            "count": int(len(strict)),
            "exclusion_reason": "retained denominator",
        },
        {
            "step": "MP/Alex labels available",
            "count": int(strict[["mp_e_above_hull", "alex_e_above_hull"]].notna().all(axis=1).sum()),
            "exclusion_reason": "primary pairwise analysis",
        },
    ]
    for model in ["ALIGNN-FF", "CHGNet", "MACE-MP"]:
        rows.append(
            {
                "step": f"{model} scores available",
                "count": int(scores[scores["model"].eq(model)]["material_id"].nunique()),
                "exclusion_reason": "model analysis",
            }
        )
    rows.append(
        {
            "step": "OQMD exact matches",
            "count": int(oqmd["oqmd_match_status"].eq("strict_structure_match").sum()),
            "exclusion_reason": "coverage boundary, not three-source measurement",
        }
    )
    out = pd.DataFrame(rows)
    out["source_artifact"] = "table_route_b_full_snapshot_matches.csv"
    out.loc[out["step"].str.contains("Alexandria"), "source_artifact"] = "alex_mp_20.zip"
    out.loc[out["step"].str.contains("OQMD"), "source_artifact"] = "table_mp_alex_oqmd_exact_matches.csv"
    return out


def alex_rows_for_strict(alex: pd.DataFrame, strict: pd.DataFrame) -> pd.DataFrame:
    rows = alex[alex["material_id"].isin(set(strict["material_id"].astype(str)))].drop_duplicates("material_id").copy()
    return rows.merge(strict[["material_id", "mp_e_above_hull", "alex_e_above_hull", "discordant"]], on="material_id", how="inner")


def representativeness_tables(alex: pd.DataFrame, strict: pd.DataFrame) -> dict[str, pd.DataFrame]:
    selected = alex_rows_for_strict(alex, strict)
    num_bins = [0, 2, 4, 8, 16, 32, 64, 128, math.inf]
    num_labels = ["1-2", "3-4", "5-8", "9-16", "17-32", "33-64", "65-128", ">128"]
    num_sites = selected[["material_id", "num_sites"]].copy()
    num_sites["num_sites_bin"] = pd.cut(num_sites["num_sites"], bins=num_bins, labels=num_labels)
    num_dist = num_sites.groupby("num_sites_bin", observed=False).size().reset_index(name="n")

    element_rows = []
    for row in selected.itertuples(index=False):
        try:
            elements = [str(el) for el in Composition(str(row.reduced_formula)).elements]
        except Exception:
            elements = []
        for el in elements:
            element_rows.append({"element": el, "material_id": row.material_id, "discordant": bool(row.discordant)})
    element_frequency = pd.DataFrame(element_rows)
    if not element_frequency.empty:
        element_frequency = (
            element_frequency.groupby("element")
            .agg(n=("material_id", "nunique"), discordant_n=("discordant", "sum"))
            .reset_index()
            .sort_values(["n", "element"], ascending=[False, True])
        )
        element_frequency["discordance_rate"] = element_frequency["discordant_n"] / element_frequency["n"]

    crystal_rows = []
    for row in selected.itertuples(index=False):
        try:
            structure = Structure.from_str(row.cif, fmt="cif")
            analyzer = SpacegroupAnalyzer(structure, symprec=0.1)
            crystal_system = analyzer.get_crystal_system()
            space_group_number = analyzer.get_space_group_number()
            space_group_symbol = analyzer.get_space_group_symbol()
        except Exception as exc:  # noqa: BLE001
            crystal_system = f"parse_failed_{type(exc).__name__}"
            space_group_number = ""
            space_group_symbol = ""
        crystal_rows.append(
            {
                "material_id": row.material_id,
                "crystal_system": crystal_system,
                "space_group_number": space_group_number,
                "space_group_symbol": space_group_symbol,
                "discordant": bool(row.discordant),
            }
        )
    crystal = pd.DataFrame(crystal_rows)
    crystal_dist = (
        crystal.groupby("crystal_system")
        .agg(n=("material_id", "nunique"), discordant_n=("discordant", "sum"))
        .reset_index()
        .sort_values(["n", "crystal_system"], ascending=[False, True])
    )
    crystal_dist["discordance_rate"] = crystal_dist["discordant_n"] / crystal_dist["n"]

    ehull_rows = []
    bins = [-math.inf, 0, 0.005, 0.01, 0.025, 0.05, 0.1, math.inf]
    labels = ["<=0", "0-5meV", "5-10meV", "10-25meV", "25-50meV", "50-100meV", ">100meV"]
    for source, col in [("MP", "mp_e_above_hull"), ("Alexandria", "alex_e_above_hull")]:
        tmp = strict[["material_id", col, "discordant"]].copy()
        tmp["source"] = source
        tmp["ehull_bin"] = pd.cut(tmp[col], bins=bins, labels=labels)
        ehull_rows.append(
            tmp.groupby(["source", "ehull_bin"], observed=False)
            .agg(n=("material_id", "nunique"), discordant_n=("discordant", "sum"))
            .reset_index()
        )
    ehull_dist = pd.concat(ehull_rows, ignore_index=True)
    ehull_dist["discordance_rate"] = ehull_dist["discordant_n"] / ehull_dist["n"].replace(0, np.nan)

    stable_fraction = pd.DataFrame(
        [
            {
                "population": "Alexandria_v20_all_rows",
                "n": int(len(alex)),
                "stable_fraction_source_native": float(alex["alex_stable_exact"].mean()),
                "label_source": "Alexandria",
            },
            {
                "population": "Alexandria_v20_MP_identifier_rows",
                "n": int(alex["is_mp_identifier"].sum()),
                "stable_fraction_source_native": float(alex[alex["is_mp_identifier"]]["alex_stable_exact"].mean()),
                "label_source": "Alexandria",
            },
            {
                "population": "MP_Alex_strict_denominator_MP_labels",
                "n": int(len(strict)),
                "stable_fraction_source_native": float(strict["mp_stable_exact"].mean()),
                "label_source": "MP",
            },
            {
                "population": "MP_Alex_strict_denominator_Alex_labels",
                "n": int(len(strict)),
                "stable_fraction_source_native": float(strict["alex_stable_exact"].mean()),
                "label_source": "Alexandria",
            },
        ]
    )

    return {
        "table_representativeness_num_sites_distribution.csv": num_dist,
        "table_representativeness_element_frequency.csv": element_frequency,
        "table_representativeness_crystal_system.csv": crystal_dist,
        "table_representativeness_ehull_distribution.csv": ehull_dist,
        "table_representativeness_stable_fraction.csv": stable_fraction,
    }


def uncertainty_flag_sweep(strict: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total_disc = int(strict["discordant"].sum())
    for thr in [0.005, 0.01, 0.025, 0.05, 0.1]:
        flag = (strict["mp_e_above_hull"].abs() <= thr) | (strict["alex_e_above_hull"].abs() <= thr)
        flagged = strict[flag]
        outside = strict[~flag]
        captured = int(flagged["discordant"].sum())
        rows.append(
            {
                "threshold_eV_per_atom": thr,
                "threshold_meV_per_atom": int(round(thr * 1000)),
                "n_total": int(len(strict)),
                "flagged_n": int(flag.sum()),
                "flagged_fraction": float(flag.mean()),
                "discordant_total_n": total_disc,
                "discordant_captured_n": captured,
                "captured_discordant_fraction": float(captured / total_disc) if total_disc else math.nan,
                "outside_n": int((~flag).sum()),
                "outside_discordant_n": int(outside["discordant"].sum()),
                "outside_discordance_rate": float(outside["discordant"].mean()) if len(outside) else math.nan,
                "flag_precision_for_discordance": float(flagged["discordant"].mean()) if len(flagged) else math.nan,
                "concordant_but_flagged_n": int((~flagged["discordant"]).sum()) if len(flagged) else 0,
                "concordant_but_flagged_fraction_of_total": float(((flag) & (~strict["discordant"])).mean()),
            }
        )
    return pd.DataFrame(rows)


def metrics_for_predictions(
    data: pd.DataFrame,
    scores: pd.DataFrame,
    *,
    label_col: str,
    model: str,
    threshold: float | None,
) -> dict[str, Any]:
    sdf = scores[scores["model"].eq(model)].copy()
    merged = data.merge(sdf[["material_id", "score"]], on="material_id", how="inner")
    if threshold is not None:
        uncertain = (merged["mp_e_above_hull"].abs() <= threshold) | (merged["alex_e_above_hull"].abs() <= threshold)
        merged = merged[~uncertain].copy()
    n = len(merged)
    if n == 0:
        return {}
    pred_n = min(n, max(math.ceil(0.05 * n), 20))
    pred_ids = set(merged.sort_values("score", ascending=True).head(pred_n)["material_id"])
    y_pred = merged["material_id"].isin(pred_ids).to_numpy(dtype=bool)
    y_true = merged[label_col].astype(bool).to_numpy()
    return {
        "n_evaluated": n,
        "predicted_positive_n": int(pred_n),
        "stable_positive_n": int(y_true.sum()),
        "binary_precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "binary_recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "binary_F1": float(f1_score(y_true, y_pred, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "topK_stable_rate": float(precision_score(y_true, y_pred, zero_division=0)),
        "AUROC_supporting": float(roc_auc_score(y_true, -merged["score"].to_numpy(dtype=float))) if len(set(y_true)) == 2 else math.nan,
    }


def uncertainty_filtered_benchmark(strict: pd.DataFrame, scores: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    thresholds = [None, 0.005, 0.01, 0.025, 0.05, 0.1]
    for thr in thresholds:
        for source, label_col in [("MP", "mp_stable_exact"), ("Alexandria", "alex_stable_exact")]:
            for model in ["ALIGNN-FF", "CHGNet", "MACE-MP"]:
                met = metrics_for_predictions(strict, scores, label_col=label_col, model=model, threshold=thr)
                if not met:
                    continue
                rows.append(
                    {
                        "threshold_eV_per_atom": "none" if thr is None else thr,
                        "threshold_meV_per_atom": "none" if thr is None else int(round(thr * 1000)),
                        "label_source": source,
                        "model": model,
                        **met,
                    }
                )
    metrics = pd.DataFrame(rows)
    rank_rows = []
    full_orders: dict[str, list[str]] = {}
    for source in ["MP", "Alexandria"]:
        full = metrics[(metrics["threshold_eV_per_atom"].astype(str).eq("none")) & metrics["label_source"].eq(source)]
        full_orders[source] = list(full.sort_values("binary_F1", ascending=False)["model"])
    for (thr, source), group in metrics.groupby(["threshold_eV_per_atom", "label_source"], dropna=False):
        order = list(group.sort_values("binary_F1", ascending=False)["model"])
        base = full_orders.get(source, [])
        rank_rows.append(
            {
                "threshold_eV_per_atom": thr,
                "label_source": source,
                "model_order_by_F1": "|".join(order),
                "full_order_by_F1": "|".join(base),
                "top_model": order[0] if order else "",
                "full_top_model": base[0] if base else "",
                "top_model_changed_vs_unfiltered": bool(order and base and order[0] != base[0]),
                "order_changed_vs_unfiltered": bool(order != base),
            }
        )
    return metrics, pd.DataFrame(rank_rows)


def selection_fraction_curve(strict: pd.DataFrame, scores: pd.DataFrame, *, n_boot: int = 2000, n_perm: int = 10000) -> pd.DataFrame:
    rng = np.random.default_rng(20260521)
    rows = []
    for model, sdf in scores.groupby("model"):
        merged = strict.merge(sdf[["material_id", "score"]], on="material_id", how="inner").sort_values("score", ascending=True)
        baseline = float(merged["discordant"].mean())
        labels = merged["discordant"].astype(int).to_numpy()
        n = len(merged)
        for frac in [0.01, 0.05, 0.10, 0.20, 0.50]:
            top_n = max(1, math.ceil(frac * n))
            top = labels[:top_n]
            observed = float(top.mean())
            boot = np.array([top[rng.integers(0, top_n, top_n)].mean() for _ in range(n_boot)])
            null = np.empty(n_perm)
            for i in range(n_perm):
                null[i] = rng.choice(labels, size=top_n, replace=False).mean()
            rows.append(
                {
                    "model": model,
                    "selection_fraction": frac,
                    "top_n": int(top_n),
                    "discordant_n": int(top.sum()),
                    "discordance_rate": observed,
                    "baseline_discordance_rate": baseline,
                    "enrichment_vs_baseline": observed / baseline if baseline else math.nan,
                    "bootstrap95_low": float(np.quantile(boot, 0.025)),
                    "bootstrap95_high": float(np.quantile(boot, 0.975)),
                    "random_null_mean": float(null.mean()),
                    "random_null95_low": float(np.quantile(null, 0.025)),
                    "random_null95_high": float(np.quantile(null, 0.975)),
                    "permutation_p_ge_observed": float((np.sum(null >= observed) + 1) / (n_perm + 1)),
                }
            )
    return pd.DataFrame(rows)


def logistic_and_rank_tests(strict: pd.DataFrame, scores: pd.DataFrame, *, n_perm: int = 2000) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(20260521)
    rows = []
    perm_rows = []
    for model, sdf in scores.groupby("model"):
        merged = strict.merge(sdf[["material_id", "score"]], on="material_id", how="inner").sort_values("score", ascending=True)
        n = len(merged)
        merged["rank_percentile"] = (np.arange(n) + 1) / n
        X_raw = merged[["abs_delta_ehull", "min_abs_ehull", "mp_e_above_hull", "alex_e_above_hull", "rank_percentile"]].to_numpy(dtype=float)
        y = merged["discordant"].astype(int).to_numpy()
        scaler = StandardScaler()
        X = scaler.fit_transform(X_raw)
        clf = LogisticRegression(max_iter=1000, solver="liblinear")
        clf.fit(X, y)
        for name, coef in zip(["abs_delta_ehull", "min_abs_ehull", "mp_e_above_hull", "alex_e_above_hull", "rank_percentile"], clf.coef_[0], strict=True):
            rows.append({"model": model, "predictor": name, "standardized_logistic_coef": float(coef), "n": n})

        obs_coef = float(clf.coef_[0][-1])
        perm = np.empty(n_perm)
        for i in range(n_perm):
            shuffled_rank = rng.permutation(X[:, -1])
            X_perm = X.copy()
            X_perm[:, -1] = shuffled_rank
            fit = LogisticRegression(max_iter=1000, solver="liblinear").fit(X_perm, y)
            perm[i] = fit.coef_[0][-1]
        perm_rows.append(
            {
                "model": model,
                "test": "rank_percentile_logistic_coef_permutation_with_other_predictors_fixed",
                "observed_rank_coef": obs_coef,
                "permutation_n": n_perm,
                "p_abs_ge_observed": float((np.sum(np.abs(perm) >= abs(obs_coef)) + 1) / (n_perm + 1)),
                "permutation_mean": float(perm.mean()),
                "permutation_p95_abs": float(np.quantile(np.abs(perm), 0.95)),
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(perm_rows)


def scatter_source(strict: pd.DataFrame, scores: pd.DataFrame) -> pd.DataFrame:
    out = strict.copy()
    out["quadrant"] = np.select(
        [
            out["mp_stable_exact"] & out["alex_stable_exact"],
            out["mp_stable_exact"] & ~out["alex_stable_exact"],
            ~out["mp_stable_exact"] & out["alex_stable_exact"],
            ~out["mp_stable_exact"] & ~out["alex_stable_exact"],
        ],
        ["both_stable", "MP_stable_only", "Alex_stable_only", "both_unstable"],
        default="unknown",
    )
    out["near_hull_10meV"] = (out["mp_e_above_hull"].abs() <= 0.01) | (out["alex_e_above_hull"].abs() <= 0.01)
    out["near_hull_25meV"] = (out["mp_e_above_hull"].abs() <= 0.025) | (out["alex_e_above_hull"].abs() <= 0.025)
    out["near_hull_50meV"] = (out["mp_e_above_hull"].abs() <= 0.05) | (out["alex_e_above_hull"].abs() <= 0.05)
    for model, sdf in scores.groupby("model"):
        rank = sdf.sort_values("score", ascending=True).reset_index(drop=True).copy()
        rank[f"{model}_rank"] = np.arange(1, len(rank) + 1)
        rank[f"{model}_rank_percentile"] = rank[f"{model}_rank"] / len(rank)
        out = out.merge(rank[["material_id", f"{model}_rank", f"{model}_rank_percentile"]], on="material_id", how="left")
    return out[
        [
            "material_id",
            "formula",
            "mp_e_above_hull",
            "alex_e_above_hull",
            "abs_delta_ehull",
            "mp_stable_exact",
            "alex_stable_exact",
            "discordant",
            "quadrant",
            "near_hull_10meV",
            "near_hull_25meV",
            "near_hull_50meV",
        ]
        + [col for col in out.columns if col.endswith("_rank") or col.endswith("_rank_percentile")]
    ]


def top_discordant_cases(scatter: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "material_id",
        "formula",
        "mp_e_above_hull",
        "alex_e_above_hull",
        "abs_delta_ehull",
        "mp_stable_exact",
        "alex_stable_exact",
        "quadrant",
    ] + [col for col in scatter.columns if col.endswith("_rank") or col.endswith("_rank_percentile")]
    out = scatter[scatter["discordant"]].sort_values("abs_delta_ehull", ascending=False)[cols].head(50).copy()
    out["structure_match_method"] = "pymatgen StructureMatcher ltol=0.2 stol=0.3 angle_tol=5 primitive_cell=True scale=True attempt_supercell=True"
    out["structure_match_rms"] = "not_recorded_public_safe_artifact"
    return out


def formal_wbm_alex_definition() -> tuple[pd.DataFrame, pd.DataFrame]:
    wbm = pd.read_csv(WBM_ALEX_MATCHES)
    exact = wbm[wbm["match_confidence"].eq("exact_structure_match")].copy()
    exact["discordant"] = exact["wbm_stable_DFT"].astype(bool) != exact["alex_stable_exact"].astype(bool)
    definition = pd.DataFrame(
        [
            {
                "component": "WBM source",
                "definition": "Matbench/WBM candidate rows from phase29 alex-mp A2 diagnostic",
                "value": str(WBM_ALEX_MATCHES),
            },
            {
                "component": "Alexandria label source",
                "definition": "alex-mp v20 local snapshot, train+val files",
                "value": str(ALEX_ZIP),
            },
            {
                "component": "candidate universe",
                "definition": "union of reconstructed raw/PARC candidates in the phase29 external-source diagnostic",
                "value": str(len(wbm)),
            },
            {
                "component": "selection/matching rule",
                "definition": "exact_structure_match rows only; formula-only rows excluded from FTR/discordance",
                "value": str(len(exact)),
            },
            {
                "component": "binary labels",
                "definition": "source-native e_above_hull <= 0 eV/atom; no recomputed hull",
                "value": "WBM stable_DFT vs Alexandria alex_stable_exact",
            },
            {
                "component": "duplicates",
                "definition": "candidate material_id rows retained once in public-safe table",
                "value": str(wbm["material_id"].nunique()),
            },
            {
                "component": "Fig4 role",
                "definition": "case-analysis contrast, not full-snapshot baseline",
                "value": "0.522 discordance on exact matches",
            },
        ]
    )
    summary = pd.DataFrame(
        [
            {
                "n_candidate_rows": int(len(wbm)),
                "n_no_formula_match": int(wbm["match_confidence"].eq("no_formula_match").sum()),
                "n_formula_only_no_structure_match": int(wbm["match_confidence"].eq("formula_only_no_structure_match").sum()),
                "n_exact_structure_match": int(len(exact)),
                "discordant_n": int(exact["discordant"].sum()),
                "discordance_rate": float(exact["discordant"].mean()),
                "wbm_stable_n": int(exact["wbm_stable_DFT"].astype(bool).sum()),
                "alex_stable_n": int(exact["alex_stable_exact"].astype(bool).sum()),
                "claim_scope": "formal_case_analysis_not_general_baseline",
            }
        ]
    )
    return definition, summary


def third_source_coverage_closeout() -> pd.DataFrame:
    triangle = pd.read_csv(OUT / "table_third_source_triangle_summary.csv")
    oqmd = triangle[triangle["comparison"].eq("MP_vs_OQMD")].iloc[0]
    wbm_summary = pd.read_csv(OUT / "table_wbm_alex_case_comparison.csv")
    wbm = wbm_summary[wbm_summary["case"].eq("WBM_vs_alex_existing_probe")].iloc[0]
    rows = [
        {
            "source": "OQMD public API",
            "candidate_overlap": 287,
            "strict_matches": int(oqmd["n_common"]),
            "status": "undercovered",
            "reason_for_exclusion": "insufficient exact StructureMatcher coverage for third-source measurement",
        },
        {
            "source": "JARVIS dft_3d via jarvis-tools",
            "candidate_overlap": "not_established",
            "strict_matches": "not_established",
            "status": "blocked",
            "reason_for_exclusion": "public dataset access in this environment raises BadZipFile during jarvis-tools smoke",
        },
        {
            "source": "WBM/Matbench",
            "candidate_overlap": int(wbm["n_common"]),
            "strict_matches": int(wbm["n_common"]),
            "status": "case_analysis_only",
            "reason_for_exclusion": "different benchmark denominator; useful as explicit case analysis, not as third-source triangulation of MP-Alex",
        },
    ]
    return pd.DataFrame(rows)


def write_closeout() -> None:
    text = """# Submission-Ready Discordance Diagnostics

This milestone adds the requested denominator audit and robustness diagnostics
without changing the core claim boundary.

## Added Artifacts

- denominator construction audit for the MP-vs-Alex exact-match set;
- representativeness source data for cell size, elements, crystal system and
  e_above_hull distributions;
- formal WBM-vs-Alex case-analysis definition;
- uncertainty-threshold sweep for near-hull flags;
- uncertainty-filtered benchmark metrics and model-rank stability;
- selection-fraction discordance curves with bootstrap and random-ranking nulls;
- logistic/permutation diagnostics for model-rank amplification;
- MP-vs-Alex scatter source data and top discordant cases;
- third-source coverage closeout.

## Claim Boundary

The durable finding remains modest and scoped: MP-vs-Alex discordance is about
10.8% on the strict denominator, is concentrated near the hull, and is not
robustly amplified by the tested ML model high-score regions. OQMD/JARVIS do
not currently provide a completed third-source measurement.
"""
    (OUT / "SUBMISSION_READY_DIAGNOSTICS_CLOSEOUT.md").write_text(text, encoding="utf-8")


def main() -> None:
    alex = load_alex_all()
    matches_all = pd.read_csv(OUT / "table_route_b_full_snapshot_matches.csv")
    strict = load_mp_alex_matches()
    scores = load_scores()

    build_denominator_audit(alex, matches_all, strict, scores).to_csv(
        OUT / "table_denominator_construction_audit.csv", index=False
    )
    for name, df in representativeness_tables(alex, strict).items():
        df.to_csv(OUT / name, index=False)

    wbm_def, wbm_summary = formal_wbm_alex_definition()
    wbm_def.to_csv(OUT / "table_wbm_alex_probe_formal_definition.csv", index=False)
    wbm_summary.to_csv(OUT / "table_wbm_alex_probe_formal_summary.csv", index=False)

    uncertainty_flag_sweep(strict).to_csv(OUT / "table_uncertainty_threshold_sweep.csv", index=False)
    bench, rank = uncertainty_filtered_benchmark(strict, scores)
    bench.to_csv(OUT / "table_benchmark_metrics_uncertainty_filtered.csv", index=False)
    rank.to_csv(OUT / "table_benchmark_ranking_stability_uncertainty_filtered.csv", index=False)

    selection_fraction_curve(strict, scores).to_csv(OUT / "table_selection_fraction_discordance_curve.csv", index=False)
    logit, perm = logistic_and_rank_tests(strict, scores)
    logit.to_csv(OUT / "table_logistic_regression_discordance.csv", index=False)
    perm.to_csv(OUT / "table_model_rank_permutation_tests.csv", index=False)

    scatter = scatter_source(strict, scores)
    scatter.to_csv(OUT / "table_mp_alex_ehull_scatter_source.csv", index=False)
    top_discordant_cases(scatter).to_csv(OUT / "table_top_discordant_structures_by_delta_ehull.csv", index=False)
    third_source_coverage_closeout().to_csv(OUT / "table_third_source_coverage_closeout.csv", index=False)
    write_closeout()
    write_manifest()


if __name__ == "__main__":
    main()
