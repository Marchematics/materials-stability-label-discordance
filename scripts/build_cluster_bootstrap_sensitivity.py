#!/usr/bin/env python3
"""Quantify endpoint and model comparisons under three cluster definitions.

The analysis uses the 31,872-row M1 fixed score-and-label support.  It draws
clusters with replacement, retains paired labels and scores within each draw,
and writes both replicate-level paired differences and percentile intervals.
Chemical systems, reduced formulae, and a symmetry/composition prototype key
provide three dependence structures for the sensitivity analysis.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer


ROOT = Path(__file__).resolve().parents[1]
M1 = ROOT / "outputs" / "repaired_model_evaluation_v1" / "fixed_support" / "denominator_all_view_common_support.parquet"
D2 = ROOT / "outputs" / "phase1_v2" / "denominator_d2_triple_single_match.parquet"
MP_STRUCTURE_CACHE = Path("/home/waas/paper_experiments/github/discordance-/outputs/milestones/materials_label_discordance_full_mp_alex_43984/mp_records_summary_structures.jsonl")
MODELS = ("ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP")
LABEL_PAIRS = (("mp_native", "alex_pbe_native"), ("mp_native", "common_pool"), ("mp_native", "audit_view"))
MODEL_PAIRS = tuple((MODELS[i], MODELS[j]) for i in range(len(MODELS)) for j in range(i + 1, len(MODELS)))
K = 1000


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=ROOT / "outputs" / "evidence_strengthening_v1" / "cluster_bootstrap_sensitivity")
    p.add_argument("--replicates", type=int, default=5000)
    p.add_argument("--seed", type=int, default=20260717)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--prototype-cache", type=Path, default=None)
    return p.parse_args()


def _prototype_keys(frame: pd.DataFrame, cache_path: Path) -> pd.DataFrame:
    """Construct a reproducible chemistry/symmetry prototype proxy from MP structures."""
    needed = dict(zip(frame["mp_id"].astype(str), frame["row_id"].astype(str)))
    found: dict[str, str] = {}
    with cache_path.open() as handle:
        for line in handle:
            record = json.loads(line)
            mp_id = str(record.get("material_id"))
            if mp_id not in needed:
                continue
            try:
                structure = Structure.from_dict(record["structure"])
                sga = SpacegroupAnalyzer(structure, symprec=0.1, angle_tolerance=5.0)
                spg = int(sga.get_space_group_number())
                anon = structure.composition.anonymized_formula.replace(" ", "")
                found[needed[mp_id]] = f"sg{spg}|{anon}|n{len(structure)}"
            except Exception:
                found[needed[mp_id]] = "unclassified"
            if len(found) == len(needed):
                break
    result = frame[["row_id"]].copy()
    result["prototype_proxy"] = result["row_id"].map(found).fillna("unclassified")
    return result


def load_frame(args: argparse.Namespace) -> tuple[pd.DataFrame, Path]:
    m1 = pd.read_parquet(M1)
    d2 = pd.read_parquet(D2, columns=["row_id", "mp_id", "reduced_formula"])
    frame = m1.merge(d2, on="row_id", how="left", validate="one_to_one")
    if frame["mp_id"].isna().any():
        raise ValueError("M1 rows missing D2 MP identifiers")
    cache = args.prototype_cache or (args.out / "prototype_assignments.parquet")
    if cache.exists():
        proto = pd.read_parquet(cache)
    else:
        if not MP_STRUCTURE_CACHE.exists():
            raise FileNotFoundError(MP_STRUCTURE_CACHE)
        proto = _prototype_keys(frame, MP_STRUCTURE_CACHE)
        args.out.mkdir(parents=True, exist_ok=True)
        proto.to_parquet(cache, index=False)
    frame = frame.merge(proto, on="row_id", how="left", validate="one_to_one")
    frame["prototype_proxy"] = frame["prototype_proxy"].fillna("unclassified")
    return frame, cache


def weighted_auprc(weights: np.ndarray, scores: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """AP for cluster-frequency weights with score ties evaluated as score groups."""
    order = np.argsort(-scores, kind="mergesort")
    sorted_scores = scores[order]
    starts = np.r_[0, np.flatnonzero(np.diff(sorted_scores)) + 1]
    w = weights[:, order]
    total = np.add.reduceat(w, starts, axis=1)
    positive = np.add.reduceat(w * labels[order][None, :], starts, axis=1)
    cumulative_total = np.cumsum(total, axis=1)
    cumulative_positive = np.cumsum(positive, axis=1)
    all_positive = cumulative_positive[:, -1]
    value = np.full(len(weights), np.nan, dtype=float)
    usable = all_positive > 0
    value[usable] = (positive[usable] * (cumulative_positive[usable] / cumulative_total[usable])).sum(axis=1) / all_positive[usable]
    return value


def weighted_fixed_topk_yield(weights: np.ndarray, scores: np.ndarray, labels: np.ndarray, k: int) -> np.ndarray:
    """Yield in the observed top-K set under paired cluster-frequency resampling."""
    order = np.argsort(-scores, kind="mergesort")[:k]
    selected = weights[:, order]
    denom = selected.sum(axis=1)
    numer = (selected * labels[order][None, :]).sum(axis=1)
    return np.divide(numer, denom, out=np.full(len(weights), np.nan), where=denom > 0)


def unweighted_metric(scores: np.ndarray, labels: np.ndarray, metric: str) -> float:
    weights = np.ones((1, len(scores)), dtype=float)
    if metric == "auprc":
        return float(weighted_auprc(weights, scores, labels)[0])
    return float(weighted_fixed_topk_yield(weights, scores, labels, K)[0])


def pair_specs() -> list[dict]:
    specs = []
    for model in MODELS:
        for a, b in LABEL_PAIRS:
            for metric in ("auprc", "stable_yield_at_1000"):
                specs.append({"comparison_type": "label_view", "model_a": model, "model_b": model,
                              "label_a": a, "label_b": b, "metric": metric})
    for a, b in MODEL_PAIRS:
        for metric in ("auprc", "stable_yield_at_1000"):
            specs.append({"comparison_type": "model", "model_a": a, "model_b": b,
                          "label_a": "audit_view", "label_b": "audit_view", "metric": metric})
    return specs


def run_scheme(frame: pd.DataFrame, scheme: str, replicates: int, seed: int, batch_size: int) -> pd.DataFrame:
    clusters, cluster_id = np.unique(frame[scheme].astype(str).to_numpy(), return_inverse=True)
    rng = np.random.default_rng(seed + {"chemical_system": 11, "reduced_formula": 23, "prototype_proxy": 37}[scheme])
    specifications = pair_specs()
    observed: dict[tuple[str, str, str], float] = {}
    for spec in specifications:
        metric = spec["metric"]
        a = unweighted_metric(frame[spec["model_a"]].to_numpy(float), frame[spec["label_a"]].to_numpy(int), metric)
        b = unweighted_metric(frame[spec["model_b"]].to_numpy(float), frame[spec["label_b"]].to_numpy(int), metric)
        observed[(spec["model_a"], spec["model_b"], spec["label_a"] + "|" + spec["label_b"] + "|" + metric)] = a - b
    rows = []
    for start in range(0, replicates, batch_size):
        n_batch = min(batch_size, replicates - start)
        sampled = rng.integers(0, len(clusters), size=(n_batch, len(clusters)))
        cluster_weights = np.zeros((n_batch, len(clusters)), dtype=np.uint16)
        rr = np.repeat(np.arange(n_batch), len(clusters))
        np.add.at(cluster_weights, (rr, sampled.ravel()), 1)
        weights = cluster_weights[:, cluster_id].astype(np.float32)
        cached: dict[tuple[str, str, str], np.ndarray] = {}
        def metric_values(model: str, label: str, metric: str) -> np.ndarray:
            key = (model, label, metric)
            if key not in cached:
                score = frame[model].to_numpy(float)
                y = frame[label].to_numpy(int)
                cached[key] = weighted_auprc(weights, score, y) if metric == "auprc" else weighted_fixed_topk_yield(weights, score, y, K)
            return cached[key]
        for spec in specifications:
            a = metric_values(spec["model_a"], spec["label_a"], spec["metric"])
            b = metric_values(spec["model_b"], spec["label_b"], spec["metric"])
            delta = a - b
            for i, value in enumerate(delta):
                rows.append({"cluster_scheme": scheme, "replicate": start + i, **spec,
                             "estimate_a": float(a[i]), "estimate_b": float(b[i]), "paired_difference": float(value)})
    result = pd.DataFrame(rows)
    result["observed_paired_difference"] = [observed[(r.model_a, r.model_b, r.label_a + "|" + r.label_b + "|" + r.metric)] for r in result.itertuples(index=False)]
    result["cluster_n"] = len(clusters)
    result["row_n"] = len(frame)
    return result


def summarise(raw: pd.DataFrame) -> pd.DataFrame:
    group = ["cluster_scheme", "comparison_type", "model_a", "model_b", "label_a", "label_b", "metric", "cluster_n", "row_n"]
    rows = []
    for keys, x in raw.groupby(group, sort=False):
        d = x["paired_difference"].to_numpy(float)
        rows.append(dict(zip(group, keys)) | {
            "observed_paired_difference": float(x["observed_paired_difference"].iloc[0]),
            "bootstrap_mean_difference": float(d.mean()),
            "ci_2_5": float(np.quantile(d, 0.025)), "ci_97_5": float(np.quantile(d, 0.975)),
            "winner_probability_model_a_or_label_a": float((d > 0).mean()),
            "tie_probability": float((d == 0).mean()), "replicates": int(len(d)),
        })
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    frame, proto_cache = load_frame(args)
    required = [*MODELS, "mp_native", "alex_pbe_native", "common_pool", "audit_view", "chemical_system", "reduced_formula", "prototype_proxy"]
    if frame[required].isna().any().any():
        raise ValueError("M1 analysis frame contains missing values")
    raw = pd.concat([run_scheme(frame, scheme, args.replicates, args.seed, args.batch_size)
                     for scheme in ("chemical_system", "reduced_formula", "prototype_proxy")], ignore_index=True)
    raw.to_parquet(args.out / "paired_cluster_bootstrap_replicates.parquet", index=False)
    raw.to_csv(args.out / "paired_cluster_bootstrap_replicates.csv", index=False)
    summary = summarise(raw)
    summary.to_csv(args.out / "paired_cluster_bootstrap_summary.csv", index=False)
    metadata = {"input": str(M1), "row_n": len(frame), "models": list(MODELS), "label_pairs": [list(x) for x in LABEL_PAIRS],
                "model_pairs": [list(x) for x in MODEL_PAIRS], "metrics": ["AUPRC", f"stable_yield_at_{K}"],
                "K": K, "replicates": args.replicates, "seed": args.seed, "cluster_schemes": ["chemical_system", "reduced_formula", "prototype_proxy"],
                "prototype_definition": "space-group number at symprec=0.1 and angle_tolerance=5.0, anonymized composition, and site count",
                "prototype_assignments": str(proto_cache)}
    (args.out / "cluster_bootstrap_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"wrote {len(raw):,} paired bootstrap replicates to {args.out}")


if __name__ == "__main__":
    main()
