from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
try:
    import requests
except Exception:  # pragma: no cover
    requests = None
try:
    from pymatgen.core import Composition
except Exception:  # pragma: no cover
    Composition = None
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

try:
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    plt = None

ROOT = Path(__file__).resolve().parents[2]
PHASE1 = ROOT / "outputs" / "phase1_v2"
PHASE2 = ROOT / "outputs" / "phase2_v1"
SEED_SCORES = ROOT / "inputs" / "phase2_v1" / "sourceaware_model_scores_public_safe.parquet"
CANDIDATE_SCORES = ROOT / "outputs" / "milestones" / "model_facing_benchmark_sensitivity_check" / "candidate_scores_chgnet_5000_v2_ehull.csv"
PGCGM_CANDIDATES = ROOT / "inputs" / "phase2_v1" / "pgcgm_unlabeled_candidate_pool_public_safe_input.csv"
MATTERGEN_SMOKE_CANDIDATES = ROOT / "inputs" / "phase2_v1" / "mattergen_hf_base_smoke_generated_crystals.extxyz"

LABEL_VIEWS = [
    "mp_native",
    "alexmp20_native",
    "alex_pbe_native",
    "common_pool",
    "source_union",
    "consensus",
    "uncertain",
    "audit_view",
]
K_GRID = [100, 300, 500, 1000, 5000, 10000]
PRIMARY_METRICS = ["f1", "precision", "recall", "balanced_accuracy", "auroc", "auprc"]

MODEL_FAMILIES = {
    "ALIGNN-FF": "strong_gnn",
    "CHGNet": "universal_potential",
    "MACE-MP": "universal_potential",
    "M3GNet": "universal_potential",
    "MP_source_native_public_hull_rank": "public_hull_oracle",
    "MatterGen_alex_mp20_source_native_public_hull_rank": "public_hull_oracle",
    "official_Alexandria_PBE_source_native_public_hull_rank": "public_hull_oracle",
    "MP_common_pool_public_hull_rank": "public_hull_oracle",
    "official_Alexandria_PBE_common_pool_public_hull_rank": "public_hull_oracle",
    "random_baseline": "random_baseline",
    "prevalence_dummy": "dummy_baseline",
    "consensus_oracle_proxy": "sourceaware_oracle",
}
MODEL_TYPES = {
    "ALIGNN-FF": "GNN interatomic potential raw-energy ranker",
    "CHGNet": "universal interatomic potential predicted-hull ranker",
    "MACE-MP": "universal interatomic potential raw-energy ranker",
    "M3GNet": "universal interatomic potential raw-energy ranker",
}
MATBENCH_TARGETS = [
    ("Voronoi RF", "fingerprint_baseline"),
    ("CGCNN", "early_gnn"),
    ("CGCNN+P", "early_gnn"),
    ("MEGNet", "early_gnn"),
    ("MEGNet-RS2RE", "early_gnn"),
    ("ALIGNN", "strong_gnn"),
    ("Wrenformer", "coordinate_free_prototype"),
    ("BOWSR", "optimization_strategy"),
    ("eSEN-30M-MP", "universal_potential"),
    ("SevenNet", "universal_potential"),
    ("ORB", "universal_potential"),
    ("EquiformerV2+DeNS", "universal_potential"),
]
MATBENCH_RAW_FILES = {
    "Voronoi RF": {"path": "models/voronoi_rf/2022-11-27-train-test/e-form-preds-IS2RE.csv.gz", "score_col": "e_form_per_atom_voronoi_rf"},
    "CGCNN": {"path": "models/cgcnn/2023-01-26-cgcnn-ens=10-wbm-IS2RE.csv.gz", "score_col": "e_form_per_atom_mp2020_corrected_pred_ens"},
    "CGCNN+P": {"path": "models/cgcnn/2023-02-05-cgcnn-perturb=5-wbm-IS2RE.csv.gz", "score_col": "e_form_per_atom_cgcnn_pred_ens"},
    "MEGNet": {"path": "models/megnet/2022-11-18-megnet-wbm-IS2RE.csv.gz", "score_col": "e_form_per_atom_megnet"},
    "MEGNet-RS2RE": {"path": "models/megnet/2023-08-23-megnet-wbm-RS2RE.csv.gz", "score_col": "e_form_per_atom_megnet_rs2re"},
    "ALIGNN-FF": {"path": "models/alignn_ff/2023-07-11-alignn-ff-wbm-IS2RE.csv.gz", "score_col": "e_form_per_atom_alignn_ff"},
    "eSEN-30M-MP": {"path": "models/esnet/2025-06-20-esnet-wbm-IS2RE.csv.gz", "score_col": "e_form_per_atom_esnet"},
}
MATBENCH_FIGSHARE_TARGETS = {
    "ALIGNN": {"pred_file_url": "https://figshare.com/files/51607262", "pred_file": "models/alignn/alignn-mp22/2023-06-02-wbm-IS2RE.csv.gz", "score_col": "e_form_per_atom_alignn"},
    "Wrenformer": {"pred_file_url": "https://figshare.com/files/52057553", "pred_file": "models/wrenformer/wrenformer-ens=10/2022-11-15-wbm-IS2RE.csv.gz", "score_col": "e_form_per_atom_wrenformer_pred_ens"},
    "BOWSR": {"pred_file_url": "https://figshare.com/files/52057523", "pred_file": "models/bowsr/bowsr-megnet/2023-01-23-wbm-IS2RE.csv.gz", "score_col": "e_form_per_atom_bowsr_megnet"},
    "CHGNet": {"pred_file_url": "https://figshare.com/files/52057526", "pred_file": "models/chgnet/chgnet-0.3.0/2023-12-21-wbm-IS2RE.csv.gz", "score_col": "e_form_per_atom_chgnet"},
    "MACE-MP": {"pred_file_url": "https://figshare.com/files/52057538", "pred_file": "models/mace/mace-mp-0/2023-12-11-wbm-IS2RE-FIRE.csv.gz", "score_col": "e_form_per_atom_mace"},
    "M3GNet": {"pred_file_url": "https://figshare.com/files/52057535", "pred_file": "models/m3gnet/m3gnet-tf-manual-sampling/2023-12-28-wbm-IS2RE.csv.gz", "score_col": "e_form_per_atom_m3gnet"},
    "SevenNet": {"pred_file_url": "https://figshare.com/files/52057544", "pred_file": "models/sevennet/sevennet-0/2024-07-11-wbm-IS2RE.csv.gz", "score_col": "e_form_per_atom_sevennet"},
    "ORB": {"pred_file_url": "https://figshare.com/files/52057562", "pred_file": "models/orb/orbff-v2/2024-10-11-wbm-IS2RE.csv.gz", "score_col": "e_form_per_atom_orb"},
    "EquiformerV2+DeNS": {"pred_file_url": "https://figshare.com/files/52057568", "pred_file": "models/eqV2/eqV2-s-dens-mp/2024-10-18-wbm-IS2RE.csv.gz", "score_col": "e_form_per_atom_eqV2-31M-dens-MP-p5"},
}
MATBENCH_RAW_BASE = "https://raw.githubusercontent.com/janosh/matbench-discovery/main"
GENERATOR_SEARCH_TARGETS = {
    "MatterGen": "official package/checkpoint not installed locally in current environment",
    "FlowMM": "official repo documents generation workflow but package/checkpoint not installed locally",
    "DiffCSP": "available as FlowMM submodule upstream but not installed locally",
    "CDVAE": "available as FlowMM submodule upstream but not installed locally",
    "CrystalFlow": "paper/repo search target; no local candidate artifact found",
}
GENERATOR_TARGETS = ["MatterGen", "FlowMM", "DiffCSP", "CDVAE", "CrystalFlow"]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def stable_random(row_id: str, seed: str = "phase2_v1") -> float:
    return int(sha256_text(f"{seed}|{row_id}")[:12], 16) / float(16**12 - 1)


def safe_metric(fn, y: np.ndarray, score: np.ndarray) -> float:
    if len(y) == 0 or len(np.unique(y)) < 2:
        return np.nan
    try:
        return float(fn(y, score))
    except Exception:
        return np.nan


def threshold_predictions(scores: pd.Series, labels: pd.Series) -> np.ndarray:
    n_pos = int(labels.astype(bool).sum())
    if n_pos <= 0:
        return np.zeros(len(scores), dtype=bool)
    ranked = scores.sort_values(ascending=False, kind="mergesort")
    pred_ids = set(ranked.head(n_pos).index)
    return np.array([idx in pred_ids for idx in scores.index], dtype=bool)


def normalize_formula(formula: Any) -> str | None:
    if pd.isna(formula):
        return None
    text = str(formula).strip()
    if not text or text.lower() in {"nan", "none", "<na>"}:
        return None
    if Composition is not None:
        try:
            return Composition(text).reduced_formula
        except Exception:
            pass
    return text.replace(" ", "")


def slug_token(value: Any) -> str:
    text = str(value).strip().lower()
    for old, new in [(" ", "_"), ("/", "_"), ("-", "_"), ("+", "p"), ("(", ""), (")", "")]:
        text = text.replace(old, new)
    return "".join(ch for ch in text if ch.isalnum() or ch == "_").strip("_") or "unknown"


def parse_extxyz_formulas(path: Path) -> pd.DataFrame:
    """Parse a small generated extxyz file into candidate formula rows.

    This intentionally avoids storing structure coordinates in public Phase 2
    tables. Matching remains unsupported unless a future exact structure-matching
    pass is added.
    """
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return pd.DataFrame(columns=["candidate_id", "formula", "chemical_system", "n_sites"])
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    idx = 1
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        try:
            n = int(lines[i].strip())
        except ValueError:
            break
        atom_lines = lines[i + 2 : i + 2 + n]
        counts: dict[str, int] = {}
        for line in atom_lines:
            parts = line.split()
            if not parts:
                continue
            el = parts[0]
            counts[el] = counts.get(el, 0) + 1
        formula = "".join(f"{el}{counts[el] if counts[el] > 1 else ''}" for el in sorted(counts))
        chem = "-".join(sorted(counts))
        rows.append({"candidate_id": f"MATTERGEN-HF-SMOKE-{idx:04d}", "formula": formula, "chemical_system": chem, "n_sites": n})
        idx += 1
        i += 2 + n
    return pd.DataFrame(rows)


def load_phase1_labels(phase1: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    labels = pd.read_parquet(phase1 / "labels_by_view.parquet")
    base = labels[labels["label_view"].eq("mp_native")].copy()
    base = base[
        [
            "row_id",
            "mp_id",
            "formula",
            "chemical_system",
            "structure_hash",
            "source_native_mp_ehull",
            "source_native_mattergen_ehull",
            "source_native_alexandria_ehull",
            "common_pool_mp_ehull",
            "common_pool_alexandria_ehull",
            "consensus_label",
        ]
    ].drop_duplicates("row_id")
    labels = labels[labels["label_view"].isin(LABEL_VIEWS)].copy()
    return labels, base


def score_metadata(model: str, coverage: int, total_n: int, source: str, status: str = "scored") -> dict[str, Any]:
    family = MODEL_FAMILIES.get(model, "external_matbench_ecosystem")
    is_real = model in {"ALIGNN-FF", "CHGNet", "MACE-MP", "M3GNet"}
    is_baseline = family in {"public_hull_oracle", "random_baseline", "dummy_baseline", "sourceaware_oracle"}
    include = status == "scored" and coverage >= int(0.99 * total_n)
    return {
        "model_name": model,
        "model_family": family,
        "input_type": MODEL_TYPES.get(model, "sourceaware_row_metadata_or_public_hull_baseline" if is_baseline else "unknown_or_external"),
        "training_data": "reported_by_source_or_not_applicable_for_baseline",
        "score_type": "standardized_higher_more_stable",
        "score_direction": "descending_higher_score_first",
        "score_direction_original": "varies_by_source_standardized_in_pipeline",
        "score_direction_standardized": "higher_score_more_likely_stable",
        "coverage_n": int(coverage),
        "missing_n": int(total_n - coverage),
        "whether_calibrated_energy": bool(model in {"CHGNet"}),
        "whether_hull_distance": bool("hull" in model.lower() or model in {"CHGNet"}),
        "source_of_score": source,
        "score_status": status,
        "model_role": "real_model" if is_real else ("baseline" if is_baseline else "external_target_not_scored"),
        "include_in_primary_leaderboard": bool(include),
    }


def collect_matbench_external_scores(out_dir: Path, external_cache: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Download/audit public Matbench Discovery WBM prediction artifacts.

    Rows in the returned parquet are WBM IDs, not SourceAware D2 rows. They are
    collected to document ecosystem coverage but are not used for Phase-1
    label-view metrics unless a future exact WBM-to-SourceAware mapping is
    supplied. Figshare-hosted targets are also audited; in this environment the
    public Figshare endpoint returns HTTP 403, so they are recorded explicitly
    rather than silently omitted.
    """
    model_dir = ensure_dir(out_dir / "model_scores")
    cache_dir = ensure_dir(external_cache / "matbench_discovery")
    frames: list[pd.DataFrame] = []
    audit_rows: list[dict[str, Any]] = []
    for model, spec in MATBENCH_RAW_FILES.items():
        url = f"{MATBENCH_RAW_BASE}/{spec['path']}"
        cache_path = cache_dir / spec["path"].replace("/", "__")
        status = "not_attempted_requests_unavailable"
        rows = 0
        sha = ""
        failure = ""
        http_status = None
        try:
            if requests is None:
                raise RuntimeError("requests unavailable")
            if not cache_path.exists():
                resp = requests.get(url, timeout=30)
                http_status = resp.status_code
                resp.raise_for_status()
                cache_path.write_bytes(resp.content)
            sha = sha256_file(cache_path)
            df = pd.read_csv(cache_path, compression="gzip", low_memory=False)
            score_col = spec["score_col"]
            if score_col not in df.columns:
                raise KeyError(f"missing score column {score_col}")
            keep = df[["material_id", score_col]].copy().rename(columns={"material_id": "external_material_id", score_col: "score_original"})
            keep["model_name"] = model
            keep["score_standardized"] = -pd.to_numeric(keep["score_original"], errors="coerce")
            keep["score_type"] = "matbench_discovery_predicted_formation_energy_standardized_negative_higher_is_more_stable"
            keep["source_panel"] = "matbench_wbm_external_unmapped"
            keep["source_url"] = url
            keep["source_artifact_kind"] = "raw_github_csv_gz"
            keep = keep.dropna(subset=["score_standardized"])
            rows = len(keep)
            frames.append(keep)
            status = "downloaded_external_unmapped"
        except Exception as exc:  # pragma: no cover - network variability
            failure = str(exc)
            status = "download_failed_or_schema_mismatch"
        audit_rows.append({
            "model_name": model,
            "source_url": url,
            "source_artifact_kind": "raw_github_csv_gz",
            "prediction_file": spec["path"],
            "score_col": spec["score_col"],
            "cache_path": str(cache_path),
            "external_score_status": status,
            "external_score_rows_n": int(rows),
            "external_cache_sha256": sha,
            "http_status": http_status,
            "mapping_status": "unmapped_wbm_ids_not_sourceaware_row_ids",
            "failure_reason": failure,
        })

    # Audit Figshare-hosted Matbench Discovery predictions for target models
    # whose full WBM CSVs are not mirrored in the GitHub tree. We intentionally
    # keep these out of the score parquet unless the file can be downloaded and
    # schema-checked; the audit is still valuable provenance for the model matrix.
    for model, spec in MATBENCH_FIGSHARE_TARGETS.items():
        if model in MATBENCH_RAW_FILES:
            continue
        url = spec["pred_file_url"]
        status = "not_attempted_requests_unavailable"
        failure = ""
        http_status = None
        try:
            if requests is None:
                raise RuntimeError("requests unavailable")
            resp = requests.get(url, timeout=15, stream=True, headers={"User-Agent": "SourceAware-Stability/phase2"})
            http_status = resp.status_code
            if resp.status_code == 200:
                # Do not commit large Figshare artifacts in this pass. Record that
                # the endpoint is reachable and requires an explicit cache/import
                # path for future mapped evaluation.
                status = "figshare_reachable_not_imported_unmapped"
            else:
                status = f"figshare_download_unavailable_http_{resp.status_code}"
                failure = (resp.text or "")[:200] if hasattr(resp, "text") else ""
        except Exception as exc:  # pragma: no cover - network variability
            failure = str(exc)
            status = "figshare_download_failed"
        audit_rows.append({
            "model_name": model,
            "source_url": url,
            "source_artifact_kind": "figshare_csv_gz",
            "prediction_file": spec["pred_file"],
            "score_col": spec["score_col"],
            "cache_path": "",
            "external_score_status": status,
            "external_score_rows_n": 0,
            "external_cache_sha256": "",
            "http_status": http_status,
            "mapping_status": "unmapped_wbm_ids_not_sourceaware_row_ids",
            "failure_reason": failure,
        })

    external = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["external_material_id", "score_original", "model_name", "score_standardized", "score_type", "source_panel", "source_url", "source_artifact_kind"])
    audit = pd.DataFrame(audit_rows)
    external.to_parquet(model_dir / "matbench_external_scores_long.parquet", index=False)
    audit.to_csv(model_dir / "matbench_external_score_audit.csv", index=False)
    audit.to_csv(model_dir / "matbench_target_prediction_artifact_audit.csv", index=False)
    return external, audit


def build_model_scores(phase1: Path, out_dir: Path, external_cache: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    labels, base = load_phase1_labels(phase1)
    total_n = len(base)
    external_cache = external_cache or Path("/home/waas/paper_experiments/phase2_external")
    external_scores, external_audit = collect_matbench_external_scores(out_dir, external_cache)
    external_rows_by_model = dict(zip(external_audit["model_name"], external_audit["external_score_rows_n"])) if len(external_audit) else {}
    external_status_by_model = dict(zip(external_audit["model_name"], external_audit["external_score_status"])) if len(external_audit) else {}
    if not SEED_SCORES.exists():
        raise FileNotFoundError(
            f"Missing public-safe seed scores: {SEED_SCORES}. Restore from Phase 1 scoring archive or provide --seed-scores in a future extension."
        )
    raw = pd.read_parquet(SEED_SCORES)
    raw = raw[raw["row_id"].isin(set(base["row_id"]))].copy()
    raw["score"] = pd.to_numeric(raw["score"], errors="coerce")
    raw = raw.dropna(subset=["score"])
    long_cols = ["row_id", "mp_id", "formula", "chemical_system", "model", "model_version", "score", "score_type", "score_source", "score_kind"]
    for col in long_cols:
        if col not in raw:
            raw[col] = ""
    long = raw[long_cols].copy()
    long = long.rename(columns={"model": "model_name"})
    long["score_standardized"] = pd.to_numeric(long["score"], errors="coerce")
    long["score_direction_standardized"] = "higher_score_more_likely_stable"
    long["source_panel"] = "sourceaware_d2"

    # Deterministic baselines and SourceAware proxy baseline.
    b = base.copy()
    baseline_frames: list[pd.DataFrame] = []
    random_scores = b[["row_id", "mp_id", "formula", "chemical_system"]].copy()
    random_scores["score_standardized"] = random_scores["row_id"].map(stable_random)
    random_scores["model_name"] = "random_baseline"
    random_scores["model_version"] = "deterministic_sha256_seed_phase2_v1"
    random_scores["score"] = random_scores["score_standardized"]
    random_scores["score_type"] = "deterministic_random_uniform"
    random_scores["score_source"] = "phase2_deterministic_baseline"
    random_scores["score_kind"] = "baseline"
    baseline_frames.append(random_scores)

    prevalence = b[["row_id", "mp_id", "formula", "chemical_system"]].copy()
    prevalence["score_standardized"] = 0.0
    prevalence["model_name"] = "prevalence_dummy"
    prevalence["model_version"] = "constant_score_baseline"
    prevalence["score"] = 0.0
    prevalence["score_type"] = "constant_prevalence_dummy"
    prevalence["score_source"] = "phase2_deterministic_baseline"
    prevalence["score_kind"] = "baseline"
    baseline_frames.append(prevalence)

    proxy = b[["row_id", "mp_id", "formula", "chemical_system"]].copy()
    consensus_stable = b["consensus_label"].eq("consensus_stable").astype(float)
    consensus_uncertain = ~b["consensus_label"].isin(["consensus_stable", "consensus_unstable"])
    proxy["score_standardized"] = consensus_stable - consensus_uncertain.astype(float) * 0.25 + b["row_id"].map(lambda x: stable_random(x, "proxy") * 1e-6)
    proxy["model_name"] = "consensus_oracle_proxy"
    proxy["model_version"] = "phase2_label_oracle_sanity_bound_not_model"
    proxy["score"] = proxy["score_standardized"]
    proxy["score_type"] = "consensus_label_oracle_proxy_higher_is_more_stable"
    proxy["score_source"] = "phase2_oracle_baseline"
    proxy["score_kind"] = "non_model_oracle_baseline"
    baseline_frames.append(proxy)

    baseline = pd.concat(baseline_frames, ignore_index=True)
    baseline["score_direction_standardized"] = "higher_score_more_likely_stable"
    common_cols = ["row_id", "mp_id", "formula", "chemical_system", "model_name", "model_version", "score", "score_type", "score_source", "score_kind", "score_standardized", "score_direction_standardized"]
    long = pd.concat([long[common_cols], baseline[common_cols]], ignore_index=True)
    long = long.dropna(subset=["score_standardized"])
    long = long.drop_duplicates(["row_id", "model_name"], keep="first")

    inventory_rows = []
    for model, sub in long.groupby("model_name"):
        inventory_rows.append(score_metadata(model, sub["row_id"].nunique(), total_n, str(sub["score_source"].iloc[0]), "scored"))
    for model, family in MATBENCH_TARGETS:
        if model not in set(long["model_name"]):
            row = score_metadata(model, 0, total_n, "matbench_discovery_public_prediction_target", "not_scored_no_exact_sourceaware_mapping_or_download")
            row["model_family"] = family
            row["include_in_primary_leaderboard"] = False
            row["failure_reason"] = "Matbench/WBM predictions require WBM-to-SourceAware exact mapping or local score generation; recorded as ecosystem target, not primary SourceAware evidence."
            inventory_rows.append(row)
    inventory = pd.DataFrame(inventory_rows)
    inventory["external_score_rows_n"] = inventory["model_name"].map(external_rows_by_model).fillna(0).astype(int)
    inventory["external_score_status"] = inventory["model_name"].map(external_status_by_model).fillna("not_applicable")
    inventory.loc[inventory["external_score_rows_n"].gt(0) & inventory["coverage_n"].eq(0), "source_of_score"] = "matbench_discovery_public_wbm_prediction_downloaded_unmapped"
    inventory = inventory.sort_values(["score_status", "model_family", "model_name"]).reset_index(drop=True)

    model_dir = ensure_dir(out_dir / "model_scores")
    long.to_parquet(model_dir / "all_model_scores_long.parquet", index=False)
    wide = long.pivot_table(index="row_id", columns="model_name", values="score_standardized", aggfunc="first").reset_index()
    wide = base[["row_id", "mp_id", "formula", "chemical_system", "structure_hash"]].merge(wide, on="row_id", how="left")
    wide.to_parquet(model_dir / "all_model_scores_wide.parquet", index=False)
    inventory.to_csv(model_dir / "model_score_inventory.csv", index=False)
    coverage = inventory[["model_name", "model_family", "coverage_n", "missing_n", "score_status", "include_in_primary_leaderboard"]].copy()
    coverage.to_csv(model_dir / "model_coverage_by_denominator.csv", index=False)
    metadata = {row["model_name"]: {k: row[k] for k in inventory.columns if k != "model_name"} for _, row in inventory.iterrows()}
    (model_dir / "model_metadata.yaml").write_text(yaml.safe_dump(metadata, sort_keys=True), encoding="utf-8")
    return long, inventory


def build_denominators(phase1: Path, out_dir: Path, scores: pd.DataFrame, inventory: pd.DataFrame) -> dict[str, pd.DataFrame]:
    _, base = load_phase1_labels(phase1)
    den_dir = ensure_dir(out_dir / "denominators")
    include_models = inventory[inventory["include_in_primary_leaderboard"].astype(bool)]["model_name"].tolist()
    coverage_sets = {m: set(g["row_id"]) for m, g in scores.groupby("model_name")}
    full_ids = set.intersection(*(coverage_sets[m] for m in include_models)) if include_models else set()
    full = base[base["row_id"].isin(full_ids)].copy()
    full["denominator"] = "D5_full_complete"
    full.to_parquet(den_dir / "denominator_d5_full_complete.parquet", index=False)

    # One representative per family, highest coverage then model name.
    reps = []
    scored_inv = inventory[inventory["score_status"].eq("scored")].copy()
    for fam, sub in scored_inv.groupby("model_family"):
        reps.append(sub.sort_values(["coverage_n", "model_name"], ascending=[False, True]).iloc[0]["model_name"])
    family_ids = set.intersection(*(coverage_sets[m] for m in reps)) if reps else set()
    family = base[base["row_id"].isin(family_ids)].copy()
    family["denominator"] = "D5_family_complete"
    family["family_representatives"] = ";".join(reps)
    family.to_parquet(den_dir / "denominator_d5_family_complete.parquet", index=False)

    pair_rows = []
    for a, b in itertools.combinations(sorted(scored_inv["model_name"].tolist()), 2):
        ids = sorted(coverage_sets[a] & coverage_sets[b])
        pair_rows.extend({"model_a": a, "model_b": b, "row_id": rid} for rid in ids)
    pairwise = pd.DataFrame(pair_rows)
    pairwise.to_parquet(den_dir / "denominator_d5_pairwise_complete.parquet", index=False)

    max_rows = []
    for model, ids in coverage_sets.items():
        max_rows.extend({"model_name": model, "row_id": rid} for rid in sorted(ids))
    maxcov = pd.DataFrame(max_rows)
    maxcov.to_parquet(den_dir / "denominator_d5_max_coverage_by_model.parquet", index=False)

    audit = inventory.copy()
    audit["d5_full_complete_n"] = len(full)
    audit["d5_family_complete_n"] = len(family)
    audit["pairwise_overlap_min_n"] = pairwise.groupby(["model_a", "model_b"]).size().min() if len(pairwise) else 0
    audit.to_csv(den_dir / "model_denominator_audit.csv", index=False)
    return {"full": full, "family": family, "pairwise": pairwise, "maxcov": maxcov, "audit": audit}


def label_frame(labels: pd.DataFrame, view: str) -> pd.DataFrame:
    f = labels[labels["label_view"].eq(view)][["row_id", "label", "is_uncertain", "label_semantics", "is_evaluable"]].copy()
    f = f[f["is_evaluable"].astype(bool)].copy()
    return f


def compute_metrics_for(scores: pd.DataFrame, labels: pd.DataFrame, denominator_ids: set[str], denominator_name: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metric_rows: list[dict[str, Any]] = []
    topk_rows: list[dict[str, Any]] = []
    ranking_rows: list[dict[str, Any]] = []
    score_sub = scores[scores["row_id"].isin(denominator_ids)].copy()
    for model, sf in score_sub.groupby("model_name"):
        sf = sf[["row_id", "score_standardized"]].dropna()
        for view in LABEL_VIEWS:
            lf = label_frame(labels, view)
            merged = sf.merge(lf, on="row_id", how="inner")
            semantics = str(lf["label_semantics"].iloc[0]) if len(lf) else ("uncertainty_indicator" if view == "uncertain" else "stability")
            status = "ok"
            if view == "source_union" and merged.empty:
                status = "not_evaluable_full_source_union_incomplete"
            if merged.empty:
                metric_rows.append({"denominator": denominator_name, "model_name": model, "label_view": view, "n": 0, "label_semantics": semantics, "metric_status": status})
                for k in K_GRID:
                    topk_rows.append({
                        "denominator": denominator_name,
                        "model_name": model,
                        "label_view": view,
                        "K": k,
                        "K_effective": 0,
                        "n_ranked": 0,
                        "stable_n": 0,
                        "precision_at_k": np.nan,
                        "recall_at_k": np.nan,
                        "stable_yield_at_k": np.nan,
                        "uncertain_fraction_at_k": np.nan,
                        "false_positive_burden_at_k": np.nan,
                        "DAF_at_k": np.nan,
                        "metric_status": status,
                    })
                continue
            y = merged["label"].astype(bool).astype(int).to_numpy()
            score = merged["score_standardized"].astype(float).to_numpy()
            indexed = merged.set_index("row_id")
            pred = threshold_predictions(indexed["score_standardized"], indexed["label"].astype(bool))
            row = {
                "denominator": denominator_name,
                "model_name": model,
                "label_view": view,
                "n": int(len(merged)),
                "positive_rate": float(np.mean(y)),
                "label_semantics": semantics,
                "metric_status": "uncertainty_indicator_not_primary_stability_metric" if view == "uncertain" else status,
                "f1": float(f1_score(y, pred, zero_division=0)),
                "precision": float(precision_score(y, pred, zero_division=0)),
                "recall": float(recall_score(y, pred, zero_division=0)),
                "balanced_accuracy": float(balanced_accuracy_score(y, pred)) if len(np.unique(y)) > 1 else np.nan,
                "auroc": safe_metric(roc_auc_score, y, score),
                "auprc": safe_metric(average_precision_score, y, score),
            }
            metric_rows.append(row)
            for metric in PRIMARY_METRICS:
                ranking_rows.append({"denominator": denominator_name, "label_view": view, "metric": metric, "model_name": model, "metric_value": row.get(metric, np.nan)})
            ranked = merged.sort_values("score_standardized", ascending=False, kind="mergesort")
            base_rate = float(ranked["label"].astype(bool).mean()) if len(ranked) else np.nan
            total_pos = int(ranked["label"].astype(bool).sum())
            for k in K_GRID:
                kk = min(k, len(ranked))
                top = ranked.head(kk)
                stable_n = int(top["label"].astype(bool).sum()) if kk else 0
                stable_yield = float(stable_n / kk) if kk else np.nan
                uncertain_fraction = float(top["is_uncertain"].astype(bool).mean()) if kk else np.nan
                recall_at_k = float(stable_n / total_pos) if total_pos else np.nan
                daf = float(stable_yield / base_rate) if base_rate and not np.isnan(base_rate) else np.nan
                topk_rows.append({
                    "denominator": denominator_name,
                    "model_name": model,
                    "label_view": view,
                    "K": k,
                    "K_effective": kk,
                    "n_ranked": int(len(ranked)),
                    "stable_n": stable_n,
                    "precision_at_k": stable_yield,
                    "recall_at_k": recall_at_k,
                    "stable_yield_at_k": stable_yield,
                    "uncertain_fraction_at_k": uncertain_fraction,
                    "false_positive_burden_at_k": float(1.0 - stable_yield) if not np.isnan(stable_yield) else np.nan,
                    "DAF_at_k": daf,
                    "metric_status": row["metric_status"],
                })
                ranking_rows.append({"denominator": denominator_name, "label_view": view, "metric": f"stable_yield@{k}", "model_name": model, "metric_value": stable_yield})
    metrics = pd.DataFrame(metric_rows)
    topk = pd.DataFrame(topk_rows)
    rankings = pd.DataFrame(ranking_rows).dropna(subset=["metric_value"])
    if not rankings.empty:
        rankings["rank"] = rankings.groupby(["denominator", "label_view", "metric"])["metric_value"].rank(method="min", ascending=False).astype(int)
    return metrics, topk, rankings


def metric_values_from_arrays(y: np.ndarray, score: np.ndarray) -> dict[str, float]:
    y = np.asarray(y).astype(int)
    score = np.asarray(score).astype(float)
    if len(y) == 0:
        return {m: np.nan for m in PRIMARY_METRICS}
    n_pos = int(y.sum())
    pred = np.zeros(len(y), dtype=bool)
    if n_pos > 0:
        order = np.argsort(-score, kind="mergesort")[:n_pos]
        pred[order] = True
    out = {
        "f1": float(f1_score(y, pred, zero_division=0)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)) if len(np.unique(y)) > 1 else np.nan,
        "auroc": safe_metric(roc_auc_score, y, score),
        "auprc": safe_metric(average_precision_score, y, score),
    }
    return out


def bootstrap_metrics_resampled(scores: pd.DataFrame, labels: pd.DataFrame, denominator_ids: set[str], denominator_name: str, n_boot: int = 40) -> pd.DataFrame:
    """Deterministic row-resampling bootstrap CIs for the primary model table.

    This complements the lightweight binomial approximation and provides actual
    row-resampled CIs on D5_family_complete without using external unmapped WBM
    rows. Source-union remains not evaluable when Phase 1 marked it incomplete.
    """
    rows: list[dict[str, Any]] = []
    score_sub = scores[scores["row_id"].isin(denominator_ids)].copy()
    for model, sf in score_sub.groupby("model_name", sort=True):
        sf = sf[["row_id", "score_standardized"]].dropna()
        for view in LABEL_VIEWS:
            lf = label_frame(labels, view)
            merged = sf.merge(lf, on="row_id", how="inner")
            status = "ok"
            if view == "source_union" and merged.empty:
                status = "not_evaluable_full_source_union_incomplete"
            if merged.empty or merged["label"].nunique(dropna=True) < 2:
                for metric in PRIMARY_METRICS:
                    rows.append({
                        "denominator": denominator_name,
                        "model_name": model,
                        "label_view": view,
                        "metric": metric,
                        "value": np.nan,
                        "ci_low_95": np.nan,
                        "ci_high_95": np.nan,
                        "bootstrap_replicates": n_boot,
                        "bootstrap_method": "deterministic_row_resampling_phase2_v1",
                        "metric_status": status if merged.empty else "not_evaluable_single_class",
                    })
                continue
            y = merged["label"].astype(bool).astype(int).to_numpy()
            score = merged["score_standardized"].astype(float).to_numpy()
            point = metric_values_from_arrays(y, score)
            seed = int(sha256_text(f"phase2_bootstrap|{denominator_name}|{model}|{view}")[:12], 16) % (2**32 - 1)
            rng = np.random.default_rng(seed)
            reps = {metric: [] for metric in PRIMARY_METRICS}
            n = len(y)
            for _ in range(n_boot):
                idx = rng.integers(0, n, size=n)
                vals = metric_values_from_arrays(y[idx], score[idx])
                for metric in PRIMARY_METRICS:
                    reps[metric].append(vals[metric])
            for metric in PRIMARY_METRICS:
                arr = np.asarray(reps[metric], dtype=float)
                arr = arr[~np.isnan(arr)]
                if len(arr):
                    lo, hi = np.quantile(arr, [0.025, 0.975])
                else:
                    lo = hi = np.nan
                rows.append({
                    "denominator": denominator_name,
                    "model_name": model,
                    "label_view": view,
                    "metric": metric,
                    "value": point.get(metric, np.nan),
                    "ci_low_95": max(0.0, min(1.0, float(lo))) if pd.notna(lo) else np.nan,
                    "ci_high_95": max(0.0, min(1.0, float(hi))) if pd.notna(hi) else np.nan,
                    "bootstrap_replicates": n_boot,
                    "bootstrap_method": "deterministic_row_resampling_phase2_v1",
                    "metric_status": status,
                })
    return pd.DataFrame(rows)


def bootstrap_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    # Lightweight deterministic CIs around already-computed point metrics. Full cluster bootstrap can be enabled later.
    rows = []
    for _, r in metrics.iterrows():
        n = int(r.get("n", 0) or 0)
        for metric in ["f1", "precision", "recall", "balanced_accuracy", "auroc", "auprc"]:
            val = pd.to_numeric(r.get(metric), errors="coerce")
            if n <= 1 or pd.isna(val):
                lo = hi = np.nan
            else:
                se = math.sqrt(max(float(val) * (1 - float(val)), 0) / n)
                lo = max(0.0, float(val) - 1.96 * se)
                hi = min(1.0, float(val) + 1.96 * se)
            rows.append({"denominator": r.get("denominator"), "model_name": r.get("model_name"), "label_view": r.get("label_view"), "metric": metric, "value": val, "ci_low_95": lo, "ci_high_95": hi, "bootstrap_method": "deterministic_binomial_approximation_phase2_v1"})
    return pd.DataFrame(rows)


def uncertainty_tables(metrics: pd.DataFrame, topk: pd.DataFrame, out_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    metric_long = metrics.melt(id_vars=["denominator", "model_name", "label_view"], value_vars=[m for m in PRIMARY_METRICS if m in metrics], var_name="metric", value_name="metric_value")
    top_long = topk.copy()
    top_long["metric"] = "stable_yield@" + top_long["K"].astype(str)
    top_long = top_long.rename(columns={"stable_yield_at_k": "metric_value"})[["denominator", "model_name", "label_view", "metric", "metric_value"]]
    all_long = pd.concat([metric_long, top_long], ignore_index=True).dropna(subset=["metric_value"])
    for (den, model, metric), sub in all_long.groupby(["denominator", "model_name", "metric"]):
        if sub["label_view"].nunique() >= 2:
            rows.append({"denominator": den, "model_name": model, "metric": metric, "label_view_band": float(sub["metric_value"].max() - sub["metric_value"].min()), "min_over_label_views": float(sub["metric_value"].min()), "max_over_label_views": float(sub["metric_value"].max()), "n_label_views": int(sub["label_view"].nunique())})
    band = pd.DataFrame(rows)
    spread_rows = []
    for (den, view, metric), sub in all_long.groupby(["denominator", "label_view", "metric"]):
        if sub["model_name"].nunique() >= 2:
            spread_rows.append({"denominator": den, "label_view": view, "metric": metric, "model_spread": float(sub["metric_value"].max() - sub["metric_value"].min()), "n_models": int(sub["model_name"].nunique())})
    spread = pd.DataFrame(spread_rows)
    ratio_rows = []
    for _, b in band.iterrows():
        same = spread[(spread["denominator"].eq(b["denominator"])) & (spread["metric"].eq(b["metric"]))]
        model_spread = same["model_spread"].median() if len(same) else np.nan
        ratio = float(b["label_view_band"] / model_spread) if pd.notna(model_spread) and model_spread != 0 else np.nan
        ratio_rows.append({**b.to_dict(), "reference_model_spread_median": model_spread, "uncertainty_dominance_ratio": ratio, "label_choice_dominates_model_choice": bool(pd.notna(ratio) and ratio > 1)})
    ratio = pd.DataFrame(ratio_rows)
    mdir = ensure_dir(out_dir / "model_metrics")
    band.to_csv(mdir / "label_view_band_vs_model_spread.csv", index=False)
    ratio.to_csv(mdir / "model_margin_to_label_uncertainty_ratio.csv", index=False)
    return band, ratio


def rank_inversions(rankings: pd.DataFrame, inventory: pd.DataFrame, out_dir: Path) -> dict[str, pd.DataFrame]:
    inv_rows = []
    top_rows = []
    for (den, metric), sub in rankings.groupby(["denominator", "metric"]):
        views = sorted(sub["label_view"].unique())
        ranks = {v: sub[sub["label_view"].eq(v)].set_index("model_name")["rank"].to_dict() for v in views}
        values = {v: sub[sub["label_view"].eq(v)].set_index("model_name")["metric_value"].to_dict() for v in views}
        for a, b in itertools.combinations(views, 2):
            common = sorted(set(ranks[a]) & set(ranks[b]))
            pair_inv = 0
            examples = []
            for x, y in itertools.combinations(common, 2):
                if (ranks[a][x] - ranks[a][y]) * (ranks[b][x] - ranks[b][y]) < 0:
                    pair_inv += 1
                    if len(examples) < 5:
                        examples.append(f"{x}<->{y}")
            if common:
                top_a = min(common, key=lambda m: ranks[a][m])
                top_b = min(common, key=lambda m: ranks[b][m])
                row = {"denominator": den, "metric": metric, "label_view_a": a, "label_view_b": b, "common_model_n": len(common), "rank_inversion_count": pair_inv, "top_model_a": top_a, "top_model_b": top_b, "top_model_inversion": top_a != top_b, "example_inversions": ";".join(examples)}
                inv_rows.append(row)
                if top_a != top_b:
                    top_rows.append(row)
    inv = pd.DataFrame(inv_rows)
    top = pd.DataFrame(top_rows, columns=inv.columns if len(inv) else [])
    family_map = dict(zip(inventory["model_name"], inventory["model_family"]))
    fam_rank = rankings.copy()
    fam_rank["model_family"] = fam_rank["model_name"].map(family_map)
    fam = fam_rank.groupby(["denominator", "label_view", "metric", "model_family"], as_index=False)["metric_value"].max()
    fam["rank"] = fam.groupby(["denominator", "label_view", "metric"])["metric_value"].rank(method="min", ascending=False).astype(int)
    fam_inv = []
    for (den, metric), sub in fam.groupby(["denominator", "metric"]):
        for a, b in itertools.combinations(sorted(sub["label_view"].unique()), 2):
            ra = sub[sub.label_view.eq(a)].set_index("model_family")["rank"].to_dict()
            rb = sub[sub.label_view.eq(b)].set_index("model_family")["rank"].to_dict()
            common = sorted(set(ra) & set(rb))
            count = sum(1 for x, y in itertools.combinations(common, 2) if (ra[x] - ra[y]) * (rb[x] - rb[y]) < 0)
            fam_inv.append({"denominator": den, "metric": metric, "label_view_a": a, "label_view_b": b, "family_rank_inversion_count": count, "common_family_n": len(common)})
    family_inv = pd.DataFrame(fam_inv)
    budget = inv[inv["metric"].str.startswith("stable_yield@", na=False)].copy() if len(inv) else pd.DataFrame()
    rdir = ensure_dir(out_dir / "rank_inversions")
    inv.to_csv(rdir / "all_rank_inversions.csv", index=False)
    top.to_csv(rdir / "top_model_inversions.csv", index=False)
    family_inv.to_csv(rdir / "family_level_inversions.csv", index=False)
    budget.to_csv(rdir / "budget_dependent_inversions.csv", index=False)
    inv.to_csv(rdir / "label_dependent_inversions.csv", index=False)
    return {"all": inv, "top": top, "family": family_inv, "budget": budget}


def build_pairwise_complete_margins(phase1: Path, out_dir: Path, scores: pd.DataFrame, denominators: dict[str, pd.DataFrame], inventory: pd.DataFrame) -> pd.DataFrame:
    """Evaluate model-pair margins on each pair's D5_pairwise_complete overlap.

    The main leaderboard uses full/family/max-coverage denominators. This table
    preserves the explicit pairwise-complete denominator requested for rank-
    inversion and margin analysis without shrinking every model comparison to a
    single all-model intersection.
    """
    labels, _ = load_phase1_labels(phase1)
    pairwise = denominators.get("pairwise", pd.DataFrame())
    mdir = ensure_dir(out_dir / "model_metrics")
    rdir = ensure_dir(out_dir / "rank_inversions")
    margin_rows: list[dict[str, Any]] = []
    inversion_rows: list[dict[str, Any]] = []
    if pairwise.empty:
        empty = pd.DataFrame()
        empty.to_csv(mdir / "pairwise_complete_model_margins.csv", index=False)
        empty.to_csv(rdir / "pairwise_complete_label_dependent_inversions.csv", index=False)
        return empty
    scored_models = set(inventory[inventory["score_status"].eq("scored")]["model_name"])
    for (model_a, model_b), pg in pairwise.groupby(["model_a", "model_b"], sort=True):
        if model_a not in scored_models or model_b not in scored_models:
            continue
        ids = set(pg["row_id"])
        pair_scores = scores[scores["model_name"].isin([model_a, model_b]) & scores["row_id"].isin(ids)].copy()
        if pair_scores.empty:
            continue
        m, t, _ = compute_metrics_for(pair_scores, labels, ids, "D5_pairwise_complete")
        metric_cols = [c for c in PRIMARY_METRICS if c in m.columns]
        metric_long = m.melt(
            id_vars=["denominator", "model_name", "label_view", "n", "metric_status"],
            value_vars=metric_cols,
            var_name="metric",
            value_name="metric_value",
        )
        top_frames = []
        top_metric_map = {
            "precision_at_k": "precision@",
            "recall_at_k": "recall@",
            "stable_yield_at_k": "stable_yield@",
            "uncertain_fraction_at_k": "uncertain_fraction@",
            "DAF_at_k": "DAF@",
            "false_positive_burden_at_k": "false_positive_burden@",
        }
        for col, prefix in top_metric_map.items():
            if col not in t.columns:
                continue
            tmp = t[["denominator", "model_name", "label_view", "K", "n_ranked", "metric_status", col]].copy()
            tmp["metric"] = prefix + tmp["K"].astype(str)
            tmp = tmp.rename(columns={col: "metric_value", "n_ranked": "n"})
            top_frames.append(tmp[["denominator", "model_name", "label_view", "n", "metric_status", "metric", "metric_value"]])
        all_long = pd.concat([metric_long] + top_frames, ignore_index=True) if top_frames else metric_long
        for (view, metric), sub in all_long.groupby(["label_view", "metric"], sort=True):
            vals = sub.set_index("model_name")
            va = pd.to_numeric(vals.loc[model_a, "metric_value"], errors="coerce") if model_a in vals.index else np.nan
            vb = pd.to_numeric(vals.loc[model_b, "metric_value"], errors="coerce") if model_b in vals.index else np.nan
            na = pd.to_numeric(vals.loc[model_a, "n"], errors="coerce") if model_a in vals.index else 0
            nb = pd.to_numeric(vals.loc[model_b, "n"], errors="coerce") if model_b in vals.index else 0
            status_a = vals.loc[model_a, "metric_status"] if model_a in vals.index else "missing_score"
            status_b = vals.loc[model_b, "metric_status"] if model_b in vals.index else "missing_score"
            margin = float(va - vb) if pd.notna(va) and pd.notna(vb) else np.nan
            if pd.isna(margin):
                winner = "not_evaluable"
            elif margin > 0:
                winner = model_a
            elif margin < 0:
                winner = model_b
            else:
                winner = "tie"
            margin_rows.append({
                "denominator": "D5_pairwise_complete",
                "model_a": model_a,
                "model_b": model_b,
                "label_view": view,
                "metric": metric,
                "pairwise_n": int(min(na, nb)) if pd.notna(na) and pd.notna(nb) else 0,
                "metric_value_a": va,
                "metric_value_b": vb,
                "margin_a_minus_b": margin,
                "winner": winner,
                "metric_status_a": status_a,
                "metric_status_b": status_b,
            })
    margins = pd.DataFrame(margin_rows)
    if not margins.empty:
        margins.to_csv(mdir / "pairwise_complete_model_margins.csv", index=False)
        margins.to_csv(rdir / "pairwise_complete_model_margins.csv", index=False)
        evaluable = margins.dropna(subset=["margin_a_minus_b"]).copy()
        evaluable = evaluable[evaluable["winner"].ne("tie")]
        for (model_a, model_b, metric), sub in evaluable.groupby(["model_a", "model_b", "metric"], sort=True):
            views = sorted(sub["label_view"].unique())
            values = sub.set_index("label_view")["margin_a_minus_b"].to_dict()
            winners = sub.set_index("label_view")["winner"].to_dict()
            for va, vb in itertools.combinations(views, 2):
                ma = values.get(va, np.nan)
                mb = values.get(vb, np.nan)
                if pd.notna(ma) and pd.notna(mb) and ma * mb < 0:
                    inversion_rows.append({
                        "denominator": "D5_pairwise_complete",
                        "model_a": model_a,
                        "model_b": model_b,
                        "metric": metric,
                        "label_view_a": va,
                        "label_view_b": vb,
                        "margin_a": ma,
                        "margin_b": mb,
                        "winner_a": winners.get(va),
                        "winner_b": winners.get(vb),
                    })
    else:
        margins.to_csv(mdir / "pairwise_complete_model_margins.csv", index=False)
        margins.to_csv(rdir / "pairwise_complete_model_margins.csv", index=False)
    pair_inv = pd.DataFrame(inversion_rows)
    pair_inv.to_csv(rdir / "pairwise_complete_label_dependent_inversions.csv", index=False)
    pair_inv.to_csv(mdir / "pairwise_complete_label_dependent_inversions.csv", index=False)
    return margins


def build_model_evaluation(phase1: Path, out_dir: Path, scores: pd.DataFrame, denominators: dict[str, pd.DataFrame], inventory: pd.DataFrame) -> dict[str, pd.DataFrame]:
    labels, _ = load_phase1_labels(phase1)
    ids = {
        "D5_full_complete": set(denominators["full"]["row_id"]),
        "D5_family_complete": set(denominators["family"]["row_id"]),
        "D5_max_coverage_union": set(scores["row_id"]),
    }
    metrics_all = []
    topk_all = []
    rankings_all = []
    for den_name, den_ids in ids.items():
        m, t, r = compute_metrics_for(scores, labels, den_ids, den_name)
        metrics_all.append(m)
        topk_all.append(t)
        rankings_all.append(r)
    metrics = pd.concat(metrics_all, ignore_index=True)
    topk = pd.concat(topk_all, ignore_index=True)
    rankings = pd.concat(rankings_all, ignore_index=True)
    mdir = ensure_dir(out_dir / "model_metrics")
    metrics.to_csv(mdir / "metrics_by_model_label_view.csv", index=False)
    bootstrap_metrics(metrics).to_csv(mdir / "metrics_by_model_label_view_bootstrap.csv", index=False)
    bootstrap_resampled = bootstrap_metrics_resampled(scores, labels, ids["D5_family_complete"], "D5_family_complete")
    bootstrap_resampled.to_csv(mdir / "metrics_by_model_label_view_bootstrap_resampled.csv", index=False)
    topk.to_csv(mdir / "topk_by_model_label_view.csv", index=False)
    rankings.to_csv(mdir / "model_rankings_by_label_view.csv", index=False)
    # compatibility copy requested in plan
    rank_inversions(rankings, inventory, out_dir)["all"].to_csv(mdir / "rank_inversions_by_metric.csv", index=False)
    band, ratio = uncertainty_tables(metrics, topk, out_dir)
    pairwise_margins = build_pairwise_complete_margins(phase1, out_dir, scores, denominators, inventory)
    return {"metrics": metrics, "topk": topk, "rankings": rankings, "band": band, "ratio": ratio, "pairwise_margins": pairwise_margins, "bootstrap_resampled": bootstrap_resampled}


def build_generative(phase1: Path, out_dir: Path) -> dict[str, pd.DataFrame]:
    labels_all, base = load_phase1_labels(phase1)
    gen_dir = ensure_dir(out_dir / "generative")
    # Candidate consequence needs all_source_native in addition to the model-facing views.
    gen_label_views = LABEL_VIEWS + ["all_source_native"]
    labels = pd.read_parquet(phase1 / "labels_by_view.parquet")
    labels = labels[labels["label_view"].isin(gen_label_views)].copy()

    search_rows = []
    inventory_rows = []
    for gen, note in GENERATOR_SEARCH_TARGETS.items():
        installed = False
        try:
            import importlib.util
            installed = importlib.util.find_spec(gen.lower()) is not None
        except Exception:
            installed = False
        status = "not_run_missing_official_checkpoint_or_local_generation_artifact"
        search_rows.append({"pipeline_name": gen, "pipeline_type": "true_generator", "local_package_detected": installed, "search_status": status, "evidence": note})
        inventory_rows.append({"pipeline_name": gen, "pipeline_type": "true_generator", "status": status, "candidate_n": 0, "matched_n": 0, "claim_scope": "attempt_record_only_not_evidence"})

    candidate_frames: list[pd.DataFrame] = []

    # Phase 2 is primarily about model-facing discovery consequence, not just
    # one hand-picked CHGNet candidate file. Treat the top-ranked rows from each
    # real SourceAware-scored model as public-safe screening pipelines. These are
    # screening consequences, not true generated-material validation.
    score_path = out_dir / "model_scores" / "all_model_scores_long.parquet"
    if score_path.exists():
        score_rows = pd.read_parquet(score_path)
        real_scores = score_rows[score_rows.get("score_kind", pd.Series(dtype=str)).eq("real_model_proxy_score")].copy()
        for model, mf in real_scores.groupby("model_name", sort=True):
            top = mf.sort_values(["score_standardized", "row_id"], ascending=[False, True], kind="mergesort").head(5000).copy()
            if top.empty:
                continue
            model_slug = slug_token(model)
            pipeline = f"{model_slug}_screened_sourceaware_top5000"
            top["pipeline_name"] = pipeline
            top["pipeline_type"] = "screening_pipeline_not_true_generator"
            top["candidate_id"] = [f"{model_slug.upper()}-SCREEN-{i:05d}" for i in range(1, len(top) + 1)]
            top["is_duplicate"] = top.duplicated("row_id", keep="first")
            top["predicted_e_above_hull"] = np.nan
            clean = top[["candidate_id", "pipeline_name", "pipeline_type", "mp_id", "formula", "chemical_system", "score_standardized", "predicted_e_above_hull", "is_duplicate"]].copy()
            clean["candidate_source"] = str(score_path)
            candidate_frames.append(clean)
            search_rows.append({
                "pipeline_name": pipeline,
                "pipeline_type": "screening_pipeline_not_true_generator",
                "local_package_detected": True,
                "search_status": "constructed_from_sourceaware_model_score_top5000",
                "evidence": f"{score_path}::{model}",
            })
    else:
        search_rows.append({
            "pipeline_name": "sourceaware_model_score_screeners",
            "pipeline_type": "screening_pipeline_not_true_generator",
            "local_package_detected": False,
            "search_status": "not_found",
            "evidence": str(score_path),
        })

    if CANDIDATE_SCORES.exists():
        cand = pd.read_csv(CANDIDATE_SCORES, low_memory=False)
        cand = cand.rename(columns={"material_id": "mp_id"})
        cand["pipeline_name"] = "CHGNet_screened_public_hull_top5000"
        cand["pipeline_type"] = "screening_pipeline_not_true_generator"
        cand["candidate_id"] = [f"CHGSCREEN-{i:05d}" for i in range(1, len(cand) + 1)]
        cand["duplicate_key"] = cand["mp_id"].astype(str)
        cand["is_duplicate"] = cand.duplicated("duplicate_key", keep="first")
        cand["score_standardized"] = pd.to_numeric(cand.get("score"), errors="coerce")
        chg_clean = cand[["candidate_id", "pipeline_name", "pipeline_type", "mp_id", "formula", "chemical_system", "score_standardized", "predicted_e_above_hull", "is_duplicate"]].copy()
        chg_clean["candidate_source"] = str(CANDIDATE_SCORES)
        candidate_frames.append(chg_clean)
        search_rows.append({"pipeline_name": "CHGNet_screened_public_hull_top5000", "pipeline_type": "screening_pipeline_not_true_generator", "local_package_detected": True, "search_status": "found_existing_public_safe_screening_table", "evidence": str(CANDIDATE_SCORES)})
    else:
        search_rows.append({"pipeline_name": "CHGNet_screened_public_hull_top5000", "pipeline_type": "screening_pipeline_not_true_generator", "local_package_detected": False, "search_status": "not_found", "evidence": str(CANDIDATE_SCORES)})

    if MATTERGEN_SMOKE_CANDIDATES.exists():
        mg = parse_extxyz_formulas(MATTERGEN_SMOKE_CANDIDATES)
        if len(mg):
            mg["pipeline_name"] = "MatterGen_hf_base_smoke_unconditional"
            mg["pipeline_type"] = "true_generator"
            mg["mp_id"] = pd.NA
            mg["score_standardized"] = -np.arange(1, len(mg) + 1, dtype=float)
            mg["predicted_e_above_hull"] = np.nan
            mg["is_duplicate"] = mg.duplicated(["formula", "chemical_system"], keep="first")
            mg_clean = mg[["candidate_id", "pipeline_name", "pipeline_type", "mp_id", "formula", "chemical_system", "score_standardized", "predicted_e_above_hull", "is_duplicate"]].copy()
            mg_clean["candidate_source"] = str(MATTERGEN_SMOKE_CANDIDATES)
            candidate_frames.append(mg_clean)
            search_rows.append({"pipeline_name": "MatterGen_hf_base_smoke_unconditional", "pipeline_type": "true_generator", "local_package_detected": True, "search_status": "completed_hf_base_smoke_generation_unmatched_to_sourceaware_exact_denominator", "evidence": str(MATTERGEN_SMOKE_CANDIDATES)})
    else:
        search_rows.append({"pipeline_name": "MatterGen_hf_base_smoke_unconditional", "pipeline_type": "true_generator", "local_package_detected": False, "search_status": "not_found", "evidence": str(MATTERGEN_SMOKE_CANDIDATES)})

    if PGCGM_CANDIDATES.exists():
        pg = pd.read_csv(PGCGM_CANDIDATES, low_memory=False)
        pg = pg.copy()
        pg["pipeline_name"] = "PGCGM_public_safe_generated_pool"
        pg["pipeline_type"] = "available_crystal_generation_pipeline"
        pg["mp_id"] = pd.NA
        pg["chemical_system"] = pg.get("elements", pd.Series(dtype=str)).astype(str).str.replace("|", "-", regex=False)
        pg.loc[pg["chemical_system"].isin(["nan", "None", "<NA>"]), "chemical_system"] = pd.NA
        pg["score_standardized"] = -pd.to_numeric(pg.get("raw_pool_rank"), errors="coerce")
        pg["predicted_e_above_hull"] = np.nan
        pg["is_duplicate"] = pg.get("duplicate_status", "").astype(str).ne("unique_structure_sha256")
        pg_clean = pg[["candidate_id", "pipeline_name", "pipeline_type", "mp_id", "formula", "chemical_system", "score_standardized", "predicted_e_above_hull", "is_duplicate"]].copy()
        pg_clean["candidate_source"] = str(PGCGM_CANDIDATES)
        candidate_frames.append(pg_clean)
        search_rows.append({"pipeline_name": "PGCGM_public_safe_generated_pool", "pipeline_type": "available_crystal_generation_pipeline", "local_package_detected": True, "search_status": "found_public_safe_generated_candidate_pool_without_sourceaware_exact_ids", "evidence": str(PGCGM_CANDIDATES)})
    else:
        search_rows.append({"pipeline_name": "PGCGM_public_safe_generated_pool", "pipeline_type": "available_crystal_generation_pipeline", "local_package_detected": False, "search_status": "not_found", "evidence": str(PGCGM_CANDIDATES)})

    clean_cols = ["candidate_id", "pipeline_name", "pipeline_type", "mp_id", "formula", "candidate_reduced_formula", "chemical_system", "score_standardized", "predicted_e_above_hull", "is_duplicate", "candidate_source"]
    cand_clean = pd.concat(candidate_frames, ignore_index=True) if candidate_frames else pd.DataFrame(columns=clean_cols)
    cand_clean["candidate_reduced_formula"] = cand_clean.get("formula", pd.Series(dtype=object)).map(normalize_formula)
    for col in clean_cols:
        if col not in cand_clean:
            cand_clean[col] = pd.NA
    cand_clean = cand_clean[clean_cols]
    cand_clean.to_parquet(gen_dir / "generated_candidates_clean.parquet", index=False)

    base_match = base[["row_id", "mp_id", "formula", "structure_hash", "source_native_mp_ehull", "source_native_mattergen_ehull", "source_native_alexandria_ehull", "common_pool_mp_ehull", "common_pool_alexandria_ehull"]].copy()
    base_match["sourceaware_reduced_formula"] = base_match["formula"].map(normalize_formula)
    formula_counts = base_match.groupby("sourceaware_reduced_formula", dropna=True).agg(
        formula_sourceaware_row_count=("row_id", "nunique"),
        formula_sourceaware_mp_examples=("mp_id", lambda x: ";".join(map(str, list(x.dropna().head(5))))),
    ).reset_index().rename(columns={"sourceaware_reduced_formula": "candidate_reduced_formula"})

    matched = cand_clean.merge(base_match.drop(columns=["formula"]), on="mp_id", how="left")
    matched["matched_to_sourceaware"] = matched["row_id"].notna()
    matched = matched.merge(formula_counts, on="candidate_reduced_formula", how="left")
    matched["formula_sourceaware_row_count"] = pd.to_numeric(matched["formula_sourceaware_row_count"], errors="coerce").fillna(0).astype(int)
    matched["formula_overlap_with_sourceaware"] = matched["formula_sourceaware_row_count"].gt(0)
    matched["formula_support_status"] = np.select(
        [matched["matched_to_sourceaware"].astype(bool), matched["formula_overlap_with_sourceaware"].astype(bool)],
        ["exact_sourceaware_structure_label_match", "formula_only_overlap_no_label_assignment"],
        default="no_formula_overlap_no_label_assignment",
    )
    ehull_cols = ["source_native_mp_ehull", "source_native_mattergen_ehull", "source_native_alexandria_ehull", "common_pool_mp_ehull", "common_pool_alexandria_ehull"]
    if len(matched):
        matched["near_threshold_25meV"] = matched[ehull_cols].apply(pd.to_numeric, errors="coerce").abs().le(0.025).any(axis=1)
    else:
        matched["near_threshold_25meV"] = []
    matched.to_parquet(gen_dir / "generated_candidates_matched_to_sourceaware.parquet", index=False)
    matched[["candidate_id", "pipeline_name", "formula", "candidate_reduced_formula", "chemical_system", "matched_to_sourceaware", "formula_overlap_with_sourceaware", "formula_sourceaware_row_count", "formula_support_status", "formula_sourceaware_mp_examples"]].to_csv(gen_dir / "generated_candidate_formula_support.csv", index=False)

    label_rows = []
    for _, c in matched.iterrows():
        rid = c.get("row_id")
        sub = labels[labels["row_id"].eq(rid)] if pd.notna(rid) else pd.DataFrame()
        for view in gen_label_views:
            lv = sub[sub["label_view"].eq(view)] if len(sub) else pd.DataFrame()
            label_rows.append({
                "candidate_id": c["candidate_id"],
                "pipeline_name": c["pipeline_name"],
                "pipeline_type": c["pipeline_type"],
                "row_id": rid,
                "label_view": view,
                "label": lv["label"].iloc[0] if len(lv) else pd.NA,
                "is_uncertain": lv["is_uncertain"].iloc[0] if len(lv) else pd.NA,
                "is_evaluable": bool(len(lv) and bool(lv["is_evaluable"].iloc[0])),
                "matched_to_sourceaware": bool(c["matched_to_sourceaware"]),
            })
    cand_labels = pd.DataFrame(label_rows)
    cand_labels.to_parquet(gen_dir / "generated_candidate_labels_by_view.parquet", index=False)

    view_summary_rows = []
    topk_rows = []
    if len(cand_clean):
        for pipeline, sub in matched.groupby("pipeline_name"):
            ptype = str(sub["pipeline_type"].iloc[0])
            if pipeline == "CHGNet_screened_public_hull_top5000":
                status = "complete_screening_consequence"
                claim_scope = "public_sourceaware_screening_consequence_not_homogeneous_dft_validation"
            elif ptype == "screening_pipeline_not_true_generator":
                status = "complete_screening_consequence"
                claim_scope = "public_sourceaware_model_score_screening_consequence_not_homogeneous_dft_validation"
            elif pipeline == "PGCGM_public_safe_generated_pool":
                status = "complete_generated_pool_unmatched_to_sourceaware_exact_denominator"
                claim_scope = "public_safe_generated_candidate_pool_no_homogeneous_dft_validation_no_exact_sourceaware_label_assignment"
            elif pipeline == "MatterGen_hf_base_smoke_unconditional":
                status = "complete_true_generator_smoke_unmatched_to_sourceaware_exact_denominator"
                claim_scope = "public_safe_true_generator_smoke_no_homogeneous_dft_validation_no_exact_sourceaware_label_assignment"
            else:
                status = "complete_candidate_consequence"
                claim_scope = "public_sourceaware_candidate_consequence_not_homogeneous_dft_validation"
            inventory_rows.append({"pipeline_name": pipeline, "pipeline_type": ptype, "status": status, "candidate_n": int(len(sub)), "matched_n": int(sub["matched_to_sourceaware"].sum()), "claim_scope": claim_scope})
    for (pipeline, view), sub in cand_labels.groupby(["pipeline_name", "label_view"]):
        evaluable = sub[sub["is_evaluable"].astype(bool)].copy()
        stable = int(evaluable["label"].astype(bool).sum()) if len(evaluable) else 0
        view_summary_rows.append({"pipeline_name": pipeline, "label_view": view, "candidate_n": int(sub["candidate_id"].nunique()), "matched_n": int(sub["matched_to_sourceaware"].sum()), "evaluable_n": int(len(evaluable)), "stable_n": stable, "stable_yield": float(stable / len(evaluable)) if len(evaluable) else np.nan, "source_uncertain_fraction": float(evaluable["is_uncertain"].astype(bool).mean()) if len(evaluable) else np.nan, "unmatched_fraction": float(1 - sub["matched_to_sourceaware"].mean()) if len(sub) else np.nan})
        ranked_ids = matched[matched["pipeline_name"].eq(pipeline)].sort_values("score_standardized", ascending=False, kind="mergesort")["candidate_id"].tolist()
        for k in K_GRID:
            ids = set(ranked_ids[: min(k, len(ranked_ids))])
            top = sub[sub["candidate_id"].isin(ids)]
            ev = top[top["is_evaluable"].astype(bool)]
            topk_rows.append({"pipeline_name": pipeline, "label_view": view, "K": k, "K_effective": len(ids), "evaluable_n": len(ev), "stable_yield": float(ev["label"].astype(bool).mean()) if len(ev) else np.nan, "uncertain_fraction": float(ev["is_uncertain"].astype(bool).mean()) if len(ev) else np.nan, "unmatched_fraction": float(1 - top["matched_to_sourceaware"].mean()) if len(top) else np.nan})
    view_summary = pd.DataFrame(view_summary_rows)
    topk = pd.DataFrame(topk_rows)

    # Wide per-pipeline consequence table with the metrics requested in the Phase 2 goal.
    consequence_rows = []
    for pipeline, sub in matched.groupby("pipeline_name") if len(matched) else []:
        labels_p = cand_labels[cand_labels["pipeline_name"].eq(pipeline)]
        def yield_for(view: str) -> float:
            v = labels_p[(labels_p["label_view"].eq(view)) & (labels_p["is_evaluable"].astype(bool))]
            return float(v["label"].astype(bool).mean()) if len(v) else np.nan
        uncertain_view = labels_p[(labels_p["label_view"].eq("uncertain")) & (labels_p["is_evaluable"].astype(bool))]
        consequence_rows.append({
            "pipeline_name": pipeline,
            "pipeline_type": str(sub["pipeline_type"].iloc[0]),
            "candidate_n": int(len(sub)),
            "matched_n": int(sub["matched_to_sourceaware"].sum()),
            "apparent_stable_yield": yield_for("mp_native"),
            "mp_native_stable_yield": yield_for("mp_native"),
            "alex_pbe_native_stable_yield": yield_for("alex_pbe_native"),
            "all_source_native_stable_yield": yield_for("all_source_native"),
            "consensus_stable_yield": yield_for("consensus"),
            "audit_view_stable_yield": yield_for("audit_view"),
            "source_uncertain_fraction": float(uncertain_view["label"].astype(bool).mean()) if len(uncertain_view) else np.nan,
            "near_threshold_fraction": float(sub["near_threshold_25meV"].astype(bool).mean()) if len(sub) else np.nan,
            "duplicate_fraction": float(sub["is_duplicate"].astype(bool).mean()) if len(sub) else np.nan,
            "unmatched_fraction": float(1 - sub["matched_to_sourceaware"].mean()) if len(sub) else np.nan,
            "formula_support_fraction": float(sub["formula_overlap_with_sourceaware"].astype(bool).mean()) if len(sub) else np.nan,
            "formula_only_support_fraction": float((sub["formula_overlap_with_sourceaware"].astype(bool) & ~sub["matched_to_sourceaware"].astype(bool)).mean()) if len(sub) else np.nan,
            "unsupported_no_formula_overlap_fraction": float((~sub["formula_overlap_with_sourceaware"].astype(bool)).mean()) if len(sub) else np.nan,
            "claim_scope": "public_safe_true_generator_smoke_no_homogeneous_dft_validation_no_exact_sourceaware_label_assignment" if pipeline == "MatterGen_hf_base_smoke_unconditional" else ("public_safe_generated_candidate_pool_no_homogeneous_dft_validation_no_exact_sourceaware_label_assignment" if pipeline == "PGCGM_public_safe_generated_pool" else "public_sourceaware_candidate_consequence_not_homogeneous_dft_validation"),
        })
    consequence = pd.DataFrame(consequence_rows)

    inventory = pd.DataFrame(inventory_rows)
    search = pd.DataFrame(search_rows)
    inventory.to_csv(gen_dir / "generated_candidate_inventory.csv", index=False)
    search.to_csv(gen_dir / "candidate_source_search_audit.csv", index=False)
    view_summary.to_csv(gen_dir / "generated_stable_yield_by_model_label_view.csv", index=False)
    consequence.to_csv(gen_dir / "generated_pipeline_consequence_summary.csv", index=False)
    view_summary.groupby("pipeline_name", as_index=False).agg(source_uncertain_fraction=("source_uncertain_fraction", "max"), matched_n=("matched_n", "max")).to_csv(gen_dir / "generated_uncertain_fraction_by_model.csv", index=False)
    topk.to_csv(gen_dir / "generated_topk_consequence.csv", index=False)
    formula_support = pd.read_csv(gen_dir / "generated_candidate_formula_support.csv") if (gen_dir / "generated_candidate_formula_support.csv").exists() else pd.DataFrame()
    return {"inventory": inventory, "search": search, "clean": cand_clean, "matched": matched, "formula_support": formula_support, "labels": cand_labels, "summary": view_summary, "consequence": consequence, "topk": topk}


def build_leaderboard(out_dir: Path, inventory: pd.DataFrame, metrics: pd.DataFrame, topk: pd.DataFrame, ratio: pd.DataFrame) -> pd.DataFrame:
    lb_dir = ensure_dir(out_dir / "leaderboard")
    cards_dir = ensure_dir(lb_dir / "leaderboard_model_cards")
    primary = topk[(topk["denominator"].eq("D5_family_complete")) & (topk["K"].eq(1000))].copy()
    pivot = primary.pivot_table(index="model_name", columns="label_view", values="stable_yield_at_k", aggfunc="first")
    # Keep explicit columns for every requested Phase 2 label view, including
    # full source-union labels when the Phase 1 hull reconstruction is incomplete
    # and therefore not numerically rankable.
    pivot = pivot.reindex(columns=LABEL_VIEWS)
    ranks = pivot.rank(ascending=False, method="min").reindex(columns=LABEL_VIEWS).add_prefix("rank_")
    lb = pivot.add_prefix("stable_yield_@").join(ranks, how="outer").reset_index()
    inv = inventory.set_index("model_name")
    lb["family"] = lb["model_name"].map(inv["model_family"].to_dict())
    lb["coverage_n"] = lb["model_name"].map(inv["coverage_n"].to_dict())
    rank_cols = [c for c in lb.columns if c.startswith("rank_")]
    lb["rank_stability_score"] = lb[rank_cols].max(axis=1) - lb[rank_cols].min(axis=1)
    band_map = ratio[(ratio["denominator"].eq("D5_family_complete")) & (ratio["metric"].eq("stable_yield@1000"))].set_index("model_name")["label_view_band"].to_dict()
    lb["label_uncertainty_band_stable_yield@1000"] = lb["model_name"].map(band_map)
    unc = primary[primary["label_view"].eq("audit_view")].set_index("model_name")["uncertain_fraction_at_k"].to_dict()
    lb["topK_uncertain_burden_audit_view@1000"] = lb["model_name"].map(unc)
    lb.to_csv(lb_dir / "sourceaware_leaderboard_alpha.csv", index=False)
    md = ["# SourceAware leaderboard alpha", "", "Primary alpha rank: consensus stable_yield@1000 on D5_family_complete.", "", lb.to_markdown(index=False)]
    (lb_dir / "sourceaware_leaderboard_alpha.md").write_text("\n".join(md), encoding="utf-8")
    lb_by_model = lb.set_index("model_name") if "model_name" in lb else pd.DataFrame()
    for _, inv_row in inventory.iterrows():
        model = inv_row["model_name"]
        safe = str(model).lower().replace(" ", "_").replace("/", "_").replace("-", "_")
        m = metrics[metrics["model_name"].eq(model)]
        lb_row = lb_by_model.loc[model] if len(lb_by_model) and model in lb_by_model.index else pd.Series(dtype=object)
        sourceaware_scored = inv_row.get("score_status") == "scored"
        content = [
            f"# {model}",
            "",
            f"Family: {inv_row.get('model_family')}",
            f"Model role: {inv_row.get('model_role')}",
            f"Score status: {inv_row.get('score_status')}",
            f"Coverage: {inv_row.get('coverage_n')}",
            f"Missing: {inv_row.get('missing_n')}",
            f"Source of score: {inv_row.get('source_of_score')}",
            f"External WBM rows audited: {inv_row.get('external_score_rows_n', 0)}",
            f"External score status: {inv_row.get('external_score_status', 'not_applicable')}",
            f"Included in primary leaderboard: {inv_row.get('include_in_primary_leaderboard')}",
            "",
            "Known caveat: Phase 2 labels are source-aware benchmark diagnostics, not homogeneous DFT referee truth. External WBM artifacts without exact SourceAware row mapping are not used for label-view metrics.",
            "",
        ]
        if sourceaware_scored and len(lb_row):
            content.extend([
                "## Leaderboard alpha summary",
                "",
                f"Rank stability score: {lb_row.get('rank_stability_score')}",
                f"Label uncertainty band stable_yield@1000: {lb_row.get('label_uncertainty_band_stable_yield@1000')}",
                f"Top-K uncertain burden audit_view@1000: {lb_row.get('topK_uncertain_burden_audit_view@1000')}",
                "",
            ])
        else:
            content.extend([
                "## Leaderboard alpha summary",
                "",
                "Not evaluated in SourceAware label-view leaderboard because exact SourceAware row scores are unavailable or the row is an external target audit.",
                "",
            ])
        content.extend(["## Label-view metrics", "", m.head(20).to_markdown(index=False) if len(m) else "No SourceAware label-view metrics for this inventory row."])
        failure = inv_row.get("failure_reason") if "failure_reason" in inventory.columns else None
        if pd.notna(failure):
            content.extend(["", "## Failure / exclusion reason", "", str(failure)])
        (cards_dir / f"{safe}.md").write_text("\n".join(content), encoding="utf-8")
    return lb


def build_figures(out_dir: Path, metrics: pd.DataFrame, topk: pd.DataFrame, rankings: pd.DataFrame, ratio: pd.DataFrame, inversions: dict[str, pd.DataFrame], gen: dict[str, pd.DataFrame]) -> None:
    fd = ensure_dir(out_dir / "figure_source_data")
    figs = ensure_dir(out_dir / "figures")
    fig1 = ratio[ratio["metric"].isin(["f1", "auprc", "stable_yield@1000"])].copy()
    fig1.to_csv(fd / "fig1_leaderboard_bands.csv", index=False)
    ratio.to_csv(fd / "fig2_uncertainty_vs_spread.csv", index=False)
    inversions["all"].to_csv(fd / "fig3_rank_inversions.csv", index=False)
    topk.to_csv(fd / "fig4_topk_heatmap.csv", index=False)
    # Fig. 5 needs the consequence-level stable/uncertain/unsupported fields,
    # not only one row per label view.
    fig5_df = gen.get("consequence", gen["summary"])
    fig5_df.to_csv(fd / "fig5_generated_consequence.csv", index=False)
    workflow = {
        "inputs": ["outputs/phase1_v2 labels", "model scores", "generated/screened candidates"],
        "steps": ["standardize scores", "evaluate label views", "rank inversions", "leaderboard alpha", "candidate consequence"],
        "guardrail": "not homogeneous DFT validation",
    }
    workflow_nodes = pd.DataFrame([
        {"node_id": "A", "stage": "input", "label": "Frozen Phase 1 label views", "detail": "source-native, common-pool, source-union status, consensus, audit"},
        {"node_id": "B", "stage": "input", "label": "Model scores", "detail": "SourceAware-scored models plus Matbench artifact audit"},
        {"node_id": "C", "stage": "input", "label": "Candidate pools", "detail": "screened candidates and generated-pool audit"},
        {"node_id": "D", "stage": "analysis", "label": "Standardize denominators", "detail": "D5 full/family/pairwise/max-coverage"},
        {"node_id": "E", "stage": "analysis", "label": "Evaluate label views", "detail": "metrics, top-K yield, uncertainty burden"},
        {"node_id": "F", "stage": "output", "label": "Leaderboard bands", "detail": "rank stability and label uncertainty"},
        {"node_id": "G", "stage": "output", "label": "Candidate consequence", "detail": "stable, uncertain, unsupported, unmatched"},
        {"node_id": "H", "stage": "guardrail", "label": "Not DFT referee truth", "detail": "diagnostic labels remain source-aware benchmark views"},
    ])
    workflow_nodes.to_csv(fd / "fig6_workflow.csv", index=False)
    (fd / "fig6_workflow.json").write_text(json.dumps(workflow, indent=2), encoding="utf-8")
    if plt is None:
        (figs / "README.md").write_text("matplotlib unavailable; figure source data generated.\n", encoding="utf-8")
        return

    def save_fig(fig, name: str) -> None:
        fig.tight_layout()
        fig.savefig(figs / f"{name}.svg", bbox_inches="tight")
        fig.savefig(figs / f"{name}.pdf", bbox_inches="tight")
        plt.close(fig)

    # Fig. 1: Source-aware model leaderboard bands.
    f1 = fig1.dropna(subset=["label_view_band"]).copy()
    f1 = f1[f1["denominator"].eq("D5_family_complete")].sort_values("label_view_band", ascending=True).tail(30)
    if not f1.empty:
        labels = f1["model_name"].astype(str) + " | " + f1["metric"].astype(str)
        fig, ax = plt.subplots(figsize=(8.5, max(3.2, 0.25 * len(f1))))
        ax.barh(labels, pd.to_numeric(f1["label_view_band"], errors="coerce").fillna(0), color="#4C78A8")
        ax.set_xlabel("Label-view band (max - min)")
        ax.set_ylabel("Model and metric")
        ax.set_title("Fig. 1  Source-aware label views turn point estimates into bands")
        ax.grid(axis="x", alpha=0.25)
        save_fig(fig, "fig1_leaderboard_bands")

    # Fig. 2: Label uncertainty versus model spread.
    f2 = ratio.dropna(subset=["uncertainty_dominance_ratio"]).copy()
    f2 = f2[f2["denominator"].eq("D5_family_complete")].sort_values("uncertainty_dominance_ratio", ascending=True).tail(30)
    if not f2.empty:
        labels = f2["model_name"].astype(str) + " | " + f2["metric"].astype(str)
        vals = pd.to_numeric(f2["uncertainty_dominance_ratio"], errors="coerce").fillna(0)
        fig, ax = plt.subplots(figsize=(8.5, max(3.2, 0.25 * len(f2))))
        ax.barh(labels, vals, color=["#F58518" if v > 1 else "#54A24B" for v in vals])
        ax.axvline(1.0, color="black", linestyle="--", linewidth=1, label="label band = model spread")
        ax.set_xlabel("Uncertainty dominance ratio")
        ax.set_ylabel("Model and metric")
        ax.set_title("Fig. 2  Label uncertainty versus model spread")
        ax.legend(loc="lower right", frameon=False)
        ax.grid(axis="x", alpha=0.25)
        save_fig(fig, "fig2_uncertainty_vs_spread")

    # Fig. 3: Rank inversions across label views.
    inv = inversions["all"].copy()
    if not inv.empty:
        inv["rank_inversion_count"] = pd.to_numeric(inv["rank_inversion_count"], errors="coerce").fillna(0)
        f3 = inv.sort_values("rank_inversion_count", ascending=True).tail(25).copy()
        labels = f3["metric"].astype(str) + "\n" + f3["label_view_a"].astype(str) + " ↔ " + f3["label_view_b"].astype(str)
        fig, ax = plt.subplots(figsize=(9.0, max(3.5, 0.32 * len(f3))))
        ax.barh(labels, f3["rank_inversion_count"], color="#B279A2")
        ax.set_xlabel("Pairwise model-rank inversions")
        ax.set_ylabel("Metric and label-view comparison")
        ax.set_title("Fig. 3  Rank inversions across source-aware label views")
        ax.grid(axis="x", alpha=0.25)
        save_fig(fig, "fig3_rank_inversions")

    # Fig. 4: Top-K discovery consequence heatmap.
    f4 = topk[(topk["denominator"].eq("D5_family_complete")) & (topk["K"].isin([100, 1000, 5000]))].copy()
    f4 = f4[f4["label_view"].isin(["mp_native", "alex_pbe_native", "common_pool", "consensus", "audit_view", "uncertain"])]
    if not f4.empty:
        f4["column"] = f4["label_view"].astype(str) + "@" + f4["K"].astype(str)
        mat = f4.pivot_table(index="model_name", columns="column", values="stable_yield_at_k", aggfunc="first")
        order = f4[f4["label_view"].eq("consensus") & f4["K"].eq(1000)].set_index("model_name")["stable_yield_at_k"].sort_values(ascending=False).index.tolist()
        mat = mat.reindex(index=[m for m in order if m in mat.index]).dropna(axis=1, how="all")
        if not mat.empty:
            fig, ax = plt.subplots(figsize=(max(8.5, 0.45 * len(mat.columns)), max(4.5, 0.32 * len(mat))))
            arr = mat.to_numpy(dtype=float)
            im = ax.imshow(arr, aspect="auto", interpolation="nearest", vmin=0, vmax=1, cmap="viridis")
            ax.set_xticks(range(len(mat.columns)))
            ax.set_xticklabels(mat.columns, rotation=45, ha="right")
            ax.set_yticks(range(len(mat.index)))
            ax.set_yticklabels(mat.index)
            ax.set_title("Fig. 4  Top-K stable-yield consequences across label views")
            cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
            cbar.set_label("stable_yield@K")
            save_fig(fig, "fig4_topk_heatmap")

    # Fig. 5: Generated-candidate consequence.
    f5 = fig5_df.copy()
    if not f5.empty:
        cols = ["apparent_stable_yield", "consensus_stable_yield", "audit_view_stable_yield", "source_uncertain_fraction", "unmatched_fraction"]
        present = [c for c in cols if c in f5.columns]
        plot = f5.set_index("pipeline_name")[present].apply(pd.to_numeric, errors="coerce")
        fig, ax = plt.subplots(figsize=(9.0, max(3.5, 0.55 * len(plot))))
        x = np.arange(len(plot.index))
        width = 0.15 if len(present) else 0.8
        colors = ["#4C78A8", "#54A24B", "#72B7B2", "#E45756", "#9D755D"]
        for i, col in enumerate(present):
            ax.bar(x + (i - (len(present) - 1) / 2) * width, plot[col].fillna(0), width=width, label=col, color=colors[i % len(colors)])
        ax.set_xticks(x)
        ax.set_xticklabels(plot.index, rotation=20, ha="right")
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("Fraction among candidates/evaluable matches")
        ax.set_title("Fig. 5  Generated and screened candidate consequence")
        ax.legend(frameon=False, ncol=2)
        ax.grid(axis="y", alpha=0.25)
        save_fig(fig, "fig5_generated_consequence")

    # Fig. 6: SourceAware leaderboard alpha workflow.
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.axis("off")
    positions = {
        "A": (0.08, 0.72), "B": (0.08, 0.45), "C": (0.08, 0.18),
        "D": (0.38, 0.60), "E": (0.58, 0.60), "F": (0.80, 0.72), "G": (0.80, 0.38), "H": (0.58, 0.18),
    }
    for _, row in workflow_nodes.iterrows():
        x, y = positions[row["node_id"]]
        fc = {"input": "#DDEEFF", "analysis": "#E7F4E4", "output": "#FFF0D6", "guardrail": "#FDE0DD"}.get(row["stage"], "white")
        ax.text(x, y, f"{row['label']}\n{row['detail']}", ha="center", va="center", fontsize=9,
                bbox={"boxstyle": "round,pad=0.45", "facecolor": fc, "edgecolor": "#555555", "linewidth": 1})
    arrows = [("A", "D"), ("B", "D"), ("C", "D"), ("D", "E"), ("E", "F"), ("E", "G"), ("E", "H"), ("H", "F"), ("H", "G")]
    for a, b in arrows:
        ax.annotate("", xy=positions[b], xytext=positions[a], arrowprops={"arrowstyle": "->", "color": "#555555", "lw": 1.2, "shrinkA": 25, "shrinkB": 25})
    ax.set_title("Fig. 6  SourceAware leaderboard alpha workflow", fontsize=13)
    save_fig(fig, "fig6_workflow")

    (figs / "README.md").write_text("# Phase 2 figures\n\nSVG/PDF previews and CSV/JSON source data generated by `sourceaware.phase2`. Figures are benchmark diagnostics, not homogeneous DFT referee-truth claims.\n", encoding="utf-8")


def write_key_findings(out_dir: Path, inventory: pd.DataFrame, evals: dict[str, pd.DataFrame], inversions: dict[str, pd.DataFrame], gen: dict[str, pd.DataFrame]) -> None:
    """Write quantitative, manuscript-facing Phase 2 findings with guardrails."""
    ratio = evals["ratio"].copy()
    topk = evals["topk"].copy()
    metrics = evals["metrics"].copy()
    pairwise_margins = evals.get("pairwise_margins", pd.DataFrame()).copy()
    consequence = gen.get("consequence", pd.DataFrame()).copy()
    gen_inv = gen.get("inventory", pd.DataFrame()).copy()
    audit_rows: list[dict[str, Any]] = []

    scored = inventory[inventory["score_status"].eq("scored")]
    real = scored[scored["model_role"].eq("real_model")]
    external_rows = int(pd.to_numeric(inventory.get("external_score_rows_n", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
    audit_rows.append({
        "finding_id": "model_matrix_scope",
        "finding": "Phase 2 evaluates a SourceAware-scored model/baseline matrix and separately audits unmapped Matbench Discovery WBM artifacts.",
        "primary_number": len(scored),
        "secondary_number": len(real),
        "evidence": f"{len(scored)} SourceAware-scored entries including baselines; {len(real)} real SourceAware-scored models; {external_rows} external WBM prediction rows audited but excluded from label-view metrics without exact mapping.",
        "claim_scope": "benchmark_evaluation_scope_not_full_matbench_leaderboard",
        "guardrail": "Unmapped WBM predictions are inventory/provenance evidence only, not SourceAware metric evidence.",
    })

    dom = ratio[pd.to_numeric(ratio.get("uncertainty_dominance_ratio", pd.Series(dtype=float)), errors="coerce") > 1].copy()
    dom_metrics = sorted(dom["metric"].dropna().astype(str).unique())
    top_dom = dom.sort_values("uncertainty_dominance_ratio", ascending=False).head(5) if not dom.empty else pd.DataFrame()
    audit_rows.append({
        "finding_id": "label_uncertainty_dominates_some_model_margins",
        "finding": "For many model/metric combinations, the label-view band is larger than the reference model spread.",
        "primary_number": len(dom),
        "secondary_number": len(dom_metrics),
        "evidence": f"{len(dom)} rows have uncertainty_dominance_ratio > 1 across {len(dom_metrics)} metrics; top examples: " + "; ".join(f"{r.model_name}:{r.metric}={float(r.uncertainty_dominance_ratio):.2f}" for _, r in top_dom.iterrows()),
        "claim_scope": "supports_label_view_uncertainty_as_model_facing_output",
        "guardrail": "Dominance ratios are computed across benchmark label views and do not identify physical-truth labels.",
    })

    stable_band = ratio[ratio["metric"].astype(str).str.startswith("stable_yield@", na=False)].copy()
    max_band = float(pd.to_numeric(stable_band.get("label_view_band", pd.Series(dtype=float)), errors="coerce").max()) if not stable_band.empty else np.nan
    audit_rows.append({
        "finding_id": "topk_yield_is_label_view_dependent",
        "finding": "Top-K stable-yield estimates change across source-aware label views.",
        "primary_number": max_band,
        "secondary_number": int(stable_band["metric"].nunique()) if not stable_band.empty else 0,
        "evidence": f"Maximum stable_yield@K label-view band is {max_band:.3f} across K metrics {sorted(stable_band['metric'].unique()) if not stable_band.empty else []}.",
        "claim_scope": "supports_topk_discovery_consequence",
        "guardrail": "Top-K stable-yield bands are benchmark-view estimates, not prospective synthesis or DFT validation outcomes.",
    })

    all_inv = inversions.get("all", pd.DataFrame())
    top_inv = inversions.get("top", pd.DataFrame())
    pair_inv_path = out_dir / "rank_inversions" / "pairwise_complete_label_dependent_inversions.csv"
    pair_inv = pd.read_csv(pair_inv_path) if pair_inv_path.exists() else pd.DataFrame()
    audit_rows.append({
        "finding_id": "rank_interpretation_changes",
        "finding": "Model rank interpretation changes under source-aware label views, including pairwise-complete label-dependent winner flips.",
        "primary_number": len(all_inv),
        "secondary_number": len(pair_inv),
        "evidence": f"{len(all_inv)} aggregate label-view rank-comparison rows; {len(top_inv)} top-model inversion rows in aggregate rankings; {len(pair_inv)} pairwise-complete label-dependent winner flips.",
        "claim_scope": "supports_rank_instability_and_pairwise_margin_claims",
        "guardrail": "Rank inversions are reported as label-view diagnostics; if a leading model is robust in a subtable, that should be reported rather than overclaimed.",
    })

    source_union_status = metrics[metrics["label_view"].eq("source_union")]["metric_status"].astype(str).unique().tolist() if "label_view" in metrics else []
    audit_rows.append({
        "finding_id": "source_union_incomplete_is_explicit",
        "finding": "Full source-union rows are explicitly marked incomplete/not evaluable rather than replaced by a weaker exact-match union.",
        "primary_number": int(metrics[metrics["label_view"].eq("source_union")].shape[0]) if "label_view" in metrics else 0,
        "secondary_number": int(topk[topk["label_view"].eq("source_union")].shape[0]) if "label_view" in topk else 0,
        "evidence": f"metric statuses for source_union: {source_union_status}; source_union topK rows are present with not-evaluable status.",
        "claim_scope": "supports_no_silent_source_union_substitution_guardrail",
        "guardrail": "source_union is a diagnostic status when full reconstruction is incomplete, not a relabeled exact-match baseline.",
    })

    screeners = consequence[consequence.get("pipeline_type", pd.Series(dtype=str)).eq("screening_pipeline_not_true_generator")].copy() if not consequence.empty else pd.DataFrame()
    if not screeners.empty:
        screeners["apparent_minus_audit"] = pd.to_numeric(screeners["apparent_stable_yield"], errors="coerce") - pd.to_numeric(screeners["audit_view_stable_yield"], errors="coerce")
        best = screeners.sort_values("apparent_minus_audit", ascending=False).iloc[0]
        apparent = float(best.get("apparent_stable_yield", np.nan))
        audit_yield = float(best.get("audit_view_stable_yield", np.nan))
        uncertain = float(best.get("source_uncertain_fraction", np.nan))
        unmatched = float(best.get("unmatched_fraction", np.nan))
        primary = float(best.get("apparent_minus_audit", np.nan))
        evidence = f"{len(screeners)} screening pipelines evaluated; largest apparent-to-audit drop is {primary:.3f} for {best.get('pipeline_name')} (apparent/mp_native={apparent:.3f}, audit-view={audit_yield:.3f}, source-uncertain={uncertain:.3f}, unmatched={unmatched:.3f})."
    else:
        evidence = "No matched screening consequence row found."
        primary = np.nan
        uncertain = np.nan
    audit_rows.append({
        "finding_id": "screened_candidate_claims_reclassify_under_audit_view",
        "finding": "A screened-candidate stable-claim rate changes materially under audit/uncertainty-aware label views.",
        "primary_number": primary,
        "secondary_number": uncertain,
        "evidence": evidence,
        "claim_scope": "supports_screened_candidate_consequence_not_generator_validation",
        "guardrail": "This is public-source-aware candidate consequence, not homogeneous DFT validation.",
    })

    completed_true = int(((gen_inv.get("pipeline_type", pd.Series(dtype=str)) == "true_generator") & gen_inv.get("status", pd.Series(dtype=str)).astype(str).str.startswith("complete")).sum()) if not gen_inv.empty else 0
    formula_support_path = out_dir / "generative" / "generated_candidate_formula_support.csv"
    formula_support = pd.read_csv(formula_support_path) if formula_support_path.exists() else pd.DataFrame()
    formula_only = int((formula_support.get("formula_support_status", pd.Series(dtype=str)) == "formula_only_overlap_no_label_assignment").sum()) if not formula_support.empty else 0
    audit_rows.append({
        "finding_id": "generated_candidate_support_is_mostly_unmatched",
        "finding": "Generated pools can be ingested, but unsupported/formula-only cases remain separated from exact label assignment.",
        "primary_number": completed_true,
        "secondary_number": formula_only,
        "evidence": f"Completed true-generator/smoke pipelines: {completed_true}; generated/candidate formula-support rows: {len(formula_support)}; formula-only overlaps without label assignment: {formula_only}.",
        "claim_scope": "supports_generated_candidate_pipeline_ingestion_and_guardrailed_consequence",
        "guardrail": "Formula-only overlap is support/coverage evidence only and is never converted to a stable/unstable SourceAware label.",
    })

    findings = pd.DataFrame(audit_rows)
    findings.to_csv(out_dir / "phase2_key_findings.csv", index=False)
    serializable = []
    for row in audit_rows:
        serializable.append({k: (None if pd.isna(v) else v) for k, v in row.items()})
    (out_dir / "phase2_key_findings.json").write_text(json.dumps(serializable, indent=2), encoding="utf-8")
    md = ["# Phase 2 key findings", "", "These findings summarize what the regenerated Phase 2 artifacts support. Each row includes an explicit claim scope and guardrail.", "", findings.to_markdown(index=False)]
    (out_dir / "phase2_key_findings.md").write_text("\n".join(md), encoding="utf-8")


def write_requirement_audit(out_dir: Path, inventory: pd.DataFrame, denominators: dict[str, pd.DataFrame], evals: dict[str, pd.DataFrame], inversions: dict[str, pd.DataFrame], gen: dict[str, pd.DataFrame]) -> None:
    """Write an explicit requirement-by-requirement Phase 2 audit.

    This is intentionally stricter than the green test suite: it records both
    completed artifacts and scoped/guardrailed partials such as external WBM
    predictions without SourceAware row mapping or generated pools without exact
    structure-label matches.
    """
    out_dir = ensure_dir(out_dir)
    files = lambda *parts: str(Path(*parts))
    scored = inventory[inventory["score_status"].eq("scored")]
    real = scored[scored["model_role"].eq("real_model")]
    external_downloaded = int((pd.to_numeric(inventory.get("external_score_rows_n", pd.Series(dtype=int)), errors="coerce").fillna(0) > 0).sum())
    external_rows = int(pd.to_numeric(inventory.get("external_score_rows_n", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
    figshare_unavailable = int(inventory.get("external_score_status", pd.Series(dtype=str)).astype(str).str.contains("figshare_download_unavailable", na=False).sum())
    metrics = evals["metrics"]
    topk = evals["topk"]
    ratio = evals["ratio"]
    gen_inv = gen["inventory"]
    consequence = gen["consequence"]
    formula_support = gen.get("formula_support", pd.DataFrame())
    figure_files_ok = all((out_dir / "figures" / f"fig{i}_{name}.{ext}").exists() for i, name in [
        (1, "leaderboard_bands"), (2, "uncertainty_vs_spread"), (3, "rank_inversions"), (4, "topk_heatmap"), (5, "generated_consequence"), (6, "workflow")
    ] for ext in ["svg", "pdf"])
    rows = [
        {
            "requirement_id": "1_model_score_inventory",
            "status": "complete_with_scope_guardrails",
            "evidence": f"{len(inventory)} inventory rows; {len(scored)} SourceAware-scored entries including baselines; {len(real)} real SourceAware-scored models; {external_downloaded} external WBM tables and {external_rows} WBM rows audited; {figshare_unavailable} Figshare targets unavailable in this environment",
            "primary_artifacts": "outputs/phase2_v1/model_scores/model_score_inventory.csv; outputs/phase2_v1/model_scores/all_model_scores_long.parquet; outputs/phase2_v1/model_scores/all_model_scores_wide.parquet; outputs/phase2_v1/model_scores/matbench_external_score_audit.csv",
            "guardrail": "External WBM rows use WBM IDs and are not used for SourceAware label-view metrics without exact mapping.",
        },
        {
            "requirement_id": "2_model_denominators",
            "status": "complete",
            "evidence": f"D5_full={len(denominators['full'])}; D5_family={len(denominators['family'])}; D5_pairwise_rows={len(denominators['pairwise'])}; D5_pairwise_margin_rows={len(evals.get('pairwise_margins', pd.DataFrame()))}; D5_maxcov_rows={len(denominators['maxcov'])}",
            "primary_artifacts": "outputs/phase2_v1/denominators/denominator_d5_full_complete.parquet; denominator_d5_family_complete.parquet; denominator_d5_pairwise_complete.parquet; denominator_d5_max_coverage_by_model.parquet; model_denominator_audit.csv; outputs/phase2_v1/model_metrics/pairwise_complete_model_margins.csv",
            "guardrail": "D5 definitions are model-coverage denominators, not physical-truth labels.",
        },
        {
            "requirement_id": "3_model_evaluation_label_views",
            "status": "complete_for_sourceaware_scored_models",
            "evidence": f"metrics rows={len(metrics)}; topK rows={len(topk)}; row-resampled bootstrap rows={len(evals.get('bootstrap_resampled', pd.DataFrame()))}; label views={','.join(sorted(metrics.label_view.unique()))}; K={','.join(map(str, sorted(topk.K.unique())))}",
            "primary_artifacts": "outputs/phase2_v1/model_metrics/metrics_by_model_label_view.csv; topk_by_model_label_view.csv; metrics_by_model_label_view_bootstrap.csv; metrics_by_model_label_view_bootstrap_resampled.csv",
            "guardrail": "source_union rows are explicit not-evaluable rows when Phase 1 full-source-union reconstruction is incomplete.",
        },
        {
            "requirement_id": "4_label_uncertainty_vs_model_spread",
            "status": "complete",
            "evidence": f"ratio rows={len(ratio)}; dominance_ratio_gt_1={(pd.to_numeric(ratio.get('uncertainty_dominance_ratio', pd.Series(dtype=float)), errors='coerce') > 1).sum()}",
            "primary_artifacts": "outputs/phase2_v1/model_metrics/label_view_band_vs_model_spread.csv; model_margin_to_label_uncertainty_ratio.csv",
            "guardrail": "Dominance ratios compare benchmark-label views; they do not adjudicate DFT truth.",
        },
        {
            "requirement_id": "5_rank_inversion_analysis",
            "status": "complete",
            "evidence": f"all inversions rows={len(inversions['all'])}; top-model inversion rows={len(inversions['top'])}; family rows={len(inversions['family'])}; budget rows={len(inversions['budget'])}",
            "primary_artifacts": "outputs/phase2_v1/rank_inversions/all_rank_inversions.csv; top_model_inversions.csv; family_level_inversions.csv; budget_dependent_inversions.csv",
            "guardrail": "Reported inversions are empirical rank diagnostics under label views; no unsupported claim that a definitive best model is overturned.",
        },
        {
            "requirement_id": "6_generative_candidate_consequence",
            "status": "partial_guardrailed_but_artifact_complete",
            "evidence": f"candidate pipelines={len(gen_inv)}; completed true-generator/smoke={int(((gen_inv['pipeline_type']=='true_generator') & gen_inv['status'].str.startswith('complete')).sum())}; screening completed={int((gen_inv['status']=='complete_screening_consequence').sum())}; consequence rows={len(consequence)}; formula-support rows={len(formula_support)}",
            "primary_artifacts": "outputs/phase2_v1/generative/generated_candidate_inventory.csv; generated_candidates_clean.parquet; generated_candidates_matched_to_sourceaware.parquet; generated_candidate_labels_by_view.parquet; generated_stable_yield_by_model_label_view.csv; generated_candidate_formula_support.csv; generated_pipeline_consequence_summary.csv",
            "guardrail": "Generated pools without exact SourceAware structure matches remain unmatched/unsupported; formula-only overlap is not label assignment; no homogeneous DFT validation is claimed.",
        },
        {
            "requirement_id": "7_leaderboard_alpha",
            "status": "complete",
            "evidence": f"leaderboard rows={len(pd.read_csv(out_dir / 'leaderboard' / 'sourceaware_leaderboard_alpha.csv'))}; inventory model cards={len(list((out_dir / 'leaderboard' / 'leaderboard_model_cards').glob('*.md')))}",
            "primary_artifacts": "outputs/phase2_v1/leaderboard/sourceaware_leaderboard_alpha.csv; sourceaware_leaderboard_alpha.md; leaderboard_model_cards/*.md",
            "guardrail": "Leaderboard ranks are alpha benchmark-view bands, not final physical-truth rankings.",
        },
        {
            "requirement_id": "8_figures",
            "status": "complete" if figure_files_ok else "incomplete",
            "evidence": "Fig. 1-6 SVG/PDF files and CSV/JSON source data generated" if figure_files_ok else "One or more Fig. 1-6 SVG/PDF files missing",
            "primary_artifacts": "outputs/phase2_v1/figure_source_data/fig1_*.csv ... fig6_workflow.csv/json; outputs/phase2_v1/figures/fig1_*.svg/pdf ... fig6_*.svg/pdf",
            "guardrail": "Figures visualize benchmark diagnostics and candidate support, not homogeneous DFT validation.",
        },
        {
            "requirement_id": "9_tests_reproducibility",
            "status": "complete",
            "evidence": "pytest suite includes Phase 2 tests for scores, denominators, metrics, rank inversions, generated candidates, figures and manifest; manifest includes SHA256, row counts and column counts",
            "primary_artifacts": "tests/test_phase2_*.py; outputs/phase2_v1/manifest_phase2_v1.json; outputs/phase2_v1/tests_report.md",
            "guardrail": "Regeneration command: python -m sourceaware.phase2.cli build-all --phase1 outputs/phase1_v2 --out outputs/phase2_v1 --external-cache /home/waas/paper_experiments/phase2_external",
        },
    ]
    audit = pd.DataFrame(rows)
    audit.to_csv(out_dir / "phase2_requirement_audit.csv", index=False)
    md = ["# Phase 2 requirement audit", "", "This audit records evidence and scope guardrails for the Phase 2 objective. `partial_guardrailed` rows are intentionally not rewritten as full physical-truth completion.", "", audit.to_markdown(index=False)]
    (out_dir / "phase2_requirement_audit.md").write_text("\n".join(md), encoding="utf-8")


def write_manifest(out_dir: Path) -> None:
    records = []
    for p in sorted(out_dir.rglob("*")):
        if p.is_file() and p.name != "manifest_phase2_v1.json":
            rows = cols = None
            try:
                if p.suffix == ".parquet":
                    df = pd.read_parquet(p)
                    rows, cols = len(df), len(df.columns)
                elif p.suffix == ".csv":
                    df = pd.read_csv(p, low_memory=False)
                    rows, cols = len(df), len(df.columns)
            except Exception:
                pass
            
            try:
                rel = str(p.resolve().relative_to(ROOT))
            except Exception:
                rel = str(p)
            records.append({"path": rel, "sha256": sha256_file(p), "bytes": p.stat().st_size, "rows": rows, "columns": cols})
    payload = {"phase": "phase2_v1", "framing": "full model-facing and generative-candidate consequence layer; not homogeneous DFT referee truth", "file_count": len(records), "files": records}
    (out_dir / "manifest_phase2_v1.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_tests_report(out_dir: Path, inventory: pd.DataFrame, gen_inv: pd.DataFrame, ratio: pd.DataFrame, inversions: dict[str, pd.DataFrame]) -> None:
    scored = inventory[inventory["score_status"].eq("scored")]
    real = scored[scored["model_role"].eq("real_model")]
    external_downloaded = int((pd.to_numeric(inventory.get("external_score_rows_n", pd.Series(dtype=int)), errors="coerce").fillna(0) > 0).sum())
    external_rows = int(pd.to_numeric(inventory.get("external_score_rows_n", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
    external_figshare_attempted = int(inventory.get("external_score_status", pd.Series(dtype=str)).astype(str).str.contains("figshare_download_unavailable", na=False).sum())
    text = f"""# Phase 2 tests and acceptance report

- Scored SourceAware entries including baselines: {len(scored)}
- Real SourceAware-scored models: {len(real)}
- SourceAware scored model families represented: {scored['model_family'].nunique()}
- Matbench Discovery external WBM score tables downloaded: {external_downloaded}
- Matbench Discovery external WBM rows collected: {external_rows}
- Matbench Discovery Figshare target artifacts audited but unavailable here: {external_figshare_attempted}
- True generator/smoke pipelines completed: {int(((gen_inv['pipeline_type'] == 'true_generator') & (gen_inv['status'].str.startswith('complete'))).sum())}
- Available generated-candidate pools completed/audited: {int((gen_inv['status'] == 'complete_generated_pool_unmatched_to_sourceaware_exact_denominator').sum())}
- Screening/candidate consequence pipelines completed: {int((gen_inv['status'] == 'complete_screening_consequence').sum())}
- Any uncertainty dominance ratio > 1: {bool((pd.to_numeric(ratio.get('uncertainty_dominance_ratio', pd.Series(dtype=float)), errors='coerce') > 1).any())}
- Top-model inversions found: {len(inversions['top'])}

Guardrail: Phase 2 reports source-aware benchmark consequences and candidate-consequence diagnostics. It is not homogeneous DFT validation and does not provide physical-truth stability labels. External Matbench/WBM predictions are collected as ecosystem coverage and remain excluded from SourceAware label-view claims unless exact mapping is supplied.
"""
    (out_dir / "tests_report.md").write_text(text, encoding="utf-8")


def build_all(phase1: Path = PHASE1, out_dir: Path = PHASE2, external_cache: Path = Path("/home/waas/paper_experiments/phase2_external")) -> None:
    ensure_dir(out_dir)
    scores, inventory = build_model_scores(phase1, out_dir, external_cache)
    den = build_denominators(phase1, out_dir, scores, inventory)
    evals = build_model_evaluation(phase1, out_dir, scores, den, inventory)
    inversions = rank_inversions(evals["rankings"], inventory, out_dir)
    gen = build_generative(phase1, out_dir)
    build_leaderboard(out_dir, inventory, evals["metrics"], evals["topk"], evals["ratio"])
    build_figures(out_dir, evals["metrics"], evals["topk"], evals["rankings"], evals["ratio"], inversions, gen)
    write_tests_report(out_dir, inventory, gen["inventory"], evals["ratio"], inversions)
    write_key_findings(out_dir, inventory, evals, inversions, gen)
    write_requirement_audit(out_dir, inventory, den, evals, inversions, gen)
    write_manifest(out_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build SourceAware-Stability Phase 2 outputs")
    sub = parser.add_subparsers(dest="cmd", required=True)
    build = sub.add_parser("build-all")
    build.add_argument("--phase1", type=Path, default=PHASE1)
    build.add_argument("--out", type=Path, default=PHASE2)
    build.add_argument("--external-cache", type=Path, default=Path("/home/waas/paper_experiments/phase2_external"))
    args = parser.parse_args(argv)
    if args.cmd == "build-all":
        ensure_dir(args.external_cache)
        build_all(args.phase1, args.out, args.external_cache)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
