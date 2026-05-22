from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from chgnet.model.model import CHGNet
from pymatgen.core import Composition, Structure
from sklearn.metrics import average_precision_score, f1_score, precision_score, roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "outputs" / "milestones" / "materials_label_discordance_full_mp_alex_43984"
OUT = ROOT / "outputs" / "milestones" / "model_facing_benchmark_sensitivity_check"
MP_STRUCTURE_CACHE = Path(
    "/home/waas/paper_experiments/github/discordance-/outputs/milestones/"
    "materials_label_discordance_full_mp_alex_43984/mp_records_summary_structures.jsonl"
)

SAMPLE_SEED = 20260523
N_TARGET = 5000
BATCH_SIZE = int(os.environ.get("CHGNET_BATCH_SIZE", "64"))
BOOTSTRAP_SEED = 20260524
N_BOOTSTRAP = 2000


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


def reduced_formula(formula: str) -> str:
    try:
        return Composition(str(formula)).reduced_formula
    except Exception:
        return str(formula)


def load_full_denominator() -> pd.DataFrame:
    df = pd.read_csv(FULL / "table_full_mp_alex_structure_matches.csv")
    df = df[df["match_status"].eq("strict_structure_match")].copy()
    df["mp_e_above_hull"] = pd.to_numeric(df["mp_e_above_hull"], errors="coerce")
    df["alex_e_above_hull"] = pd.to_numeric(df["alex_e_above_hull"], errors="coerce")
    df["mp_stable"] = df["mp_stable_exact"].astype(str).str.lower().eq("true")
    df["alex_stable"] = df["alex_stable_exact"].astype(str).str.lower().eq("true")
    df["discordant"] = df["mp_stable"] != df["alex_stable"]
    df["target_reduced_formula"] = df["formula"].map(reduced_formula)
    return df.reset_index(drop=True)


def load_scoring_sample() -> pd.DataFrame:
    df = load_full_denominator()
    df = df.sort_values("material_id").sample(n=N_TARGET, random_state=SAMPLE_SEED).sort_values("material_id")
    return df.reset_index(drop=True)


def load_structure_cache(material_ids: set[str]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    with MP_STRUCTURE_CACHE.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            mid = str(row.get("material_id"))
            if mid in material_ids and row.get("structure"):
                records[mid] = row
    return records


def element_set(df: pd.DataFrame) -> set[str]:
    elements: set[str] = set()
    for formula in df["target_reduced_formula"]:
        try:
            elements.update(str(el) for el in Composition(str(formula)).elements)
        except Exception:
            continue
    return elements


def fetch_element_reference_structures(elements: set[str]) -> dict[str, Structure]:
    from mp_api.client import MPRester

    api_key = os.environ.get("MP_API_KEY")
    if not api_key:
        raise RuntimeError("MP_API_KEY is required; source /root/.mp_api_env before running.")
    refs: dict[str, Structure] = {}
    with MPRester(api_key) as mpr:
        for idx, el in enumerate(sorted(elements), start=1):
            docs = mpr.materials.summary.search(
                chemsys=el,
                fields=["material_id", "energy_above_hull", "structure"],
            )
            candidates = [d for d in docs if getattr(d, "structure", None) is not None]
            if not candidates:
                continue
            candidates.sort(key=lambda d: float(getattr(d, "energy_above_hull", 1e9) or 1e9))
            refs[el] = candidates[0].structure
            print(f"Element reference {idx}/{len(elements)} {el}: {candidates[0].material_id}", flush=True)
            time.sleep(0.05)
    missing = sorted(elements - set(refs))
    if missing:
        raise RuntimeError(f"Missing MP elemental reference structures: {missing}")
    return refs


def predict_energy_per_atom(model: CHGNet, structures: list[Structure], labels: list[str]) -> dict[str, float]:
    out: dict[str, float] = {}
    for start in range(0, len(structures), BATCH_SIZE):
        batch = structures[start : start + BATCH_SIZE]
        batch_labels = labels[start : start + BATCH_SIZE]
        with torch.no_grad():
            preds = model.predict_structure(batch, task="e", batch_size=BATCH_SIZE)
        if isinstance(preds, dict):
            preds = [preds]
        for label, pred in zip(batch_labels, preds):
            val = pred["e"]
            out[label] = float(np.asarray(val).item())
        print(f"CHGNet scored {min(start + BATCH_SIZE, len(structures))}/{len(structures)}", flush=True)
    return out


def score_subset(df: pd.DataFrame) -> pd.DataFrame:
    ids = set(df["material_id"].astype(str))
    records = load_structure_cache(ids)
    if len(records) != len(df):
        missing = sorted(ids - set(records))[:10]
        raise RuntimeError(f"Missing structures in cache: {len(ids) - len(records)} examples={missing}")

    refs = fetch_element_reference_structures(element_set(df))
    model = CHGNet.load()
    structures: list[Structure] = []
    labels: list[str] = []
    for el, struct in refs.items():
        labels.append(f"element::{el}")
        structures.append(struct)
    for mid in df["material_id"].astype(str):
        labels.append(f"target::{mid}")
        structures.append(Structure.from_dict(records[mid]["structure"]))

    energies = predict_energy_per_atom(model, structures, labels)
    element_energy = {label.split("::", 1)[1]: energy for label, energy in energies.items() if label.startswith("element::")}
    rows = []
    for row in df.itertuples(index=False):
        comp = Composition(str(row.target_reduced_formula))
        element_ref = 0.0
        for el, amt in comp.items():
            element_ref += float(amt) / comp.num_atoms * element_energy[str(el)]
        energy = energies[f"target::{row.material_id}"]
        formation_proxy = energy - element_ref
        rows.append(
            {
                "material_id": row.material_id,
                "formula": row.formula,
                "chemical_system": row.chemical_system,
                "model": "CHGNet",
                "model_version": "CHGNet.load()",
                "energy_per_atom": energy,
                "formation_energy_proxy": formation_proxy,
                "score": -formation_proxy,
                "score_type": "negative_chgnet_formation_energy_proxy_higher_is_more_stable",
                "mp_stable": row.mp_stable,
                "alex_stable": row.alex_stable,
                "source_agreement": not bool(row.discordant),
                "mp_e_above_hull": row.mp_e_above_hull,
                "alex_e_above_hull": row.alex_e_above_hull,
            }
        )
    score_df = pd.DataFrame(rows)
    score_df.to_csv(OUT / "candidate_scores_chgnet_5000.csv", index=False)
    pd.DataFrame(
        [
            {
                "model": "CHGNet",
                "n_scored": len(score_df),
                "n_target": N_TARGET,
                "sample_seed": SAMPLE_SEED,
                "batch_size": BATCH_SIZE,
                "device": "cuda" if torch.cuda.is_available() else "cpu",
                "mp_structure_cache": str(MP_STRUCTURE_CACHE),
                "mp_structure_cache_sha256": sha256_file(MP_STRUCTURE_CACHE),
                "claim_scope": "model_facing_sensitivity_check_not_leaderboard",
            }
        ]
    ).to_csv(OUT / "table_chgnet_scored_subset_manifest.csv", index=False)
    return score_df


def threshold_metrics(score_df: pd.DataFrame, label_col: str, denominator: str) -> dict[str, object]:
    df = score_df.copy()
    y = df[label_col].astype(bool)
    score = df["score"].astype(float)
    if y.nunique() < 2:
        auc = ""
        auprc = ""
    else:
        auc = float(roc_auc_score(y, score))
        auprc = float(average_precision_score(y, score))
    cutoff = score.median()
    pred = score >= cutoff
    return {
        "model": "CHGNet",
        "denominator": denominator,
        "label_source": label_col,
        "n": int(len(df)),
        "positive_rate": float(y.mean()),
        "auroc": auc,
        "auprc": auprc,
        "median_threshold_precision": float(precision_score(y, pred, zero_division=0)),
        "median_threshold_f1": float(f1_score(y, pred, zero_division=0)),
        "claim_scope": "model_facing_sensitivity_check_not_leaderboard",
    }


def safe_auc(y: pd.Series, score: pd.Series) -> tuple[float | str, float | str]:
    y = y.astype(bool)
    if y.nunique() < 2:
        return "", ""
    return float(roc_auc_score(y, score)), float(average_precision_score(y, score))


def write_score_direction_sanity(score_df: pd.DataFrame) -> None:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    random_score = pd.Series(rng.normal(size=len(score_df)), index=score_df.index)
    score_defs = {
        "raw_CHGNet_formation_energy_proxy_as_higher_stability_score": -score_df["score"],
        "negative_CHGNet_formation_energy_proxy_as_higher_stability_score": score_df["score"],
        "random_ranking_baseline": random_score,
    }
    rows = []
    for score_name, score in score_defs.items():
        for label_col in ["mp_stable", "alex_stable"]:
            auroc, auprc = safe_auc(score_df[label_col], score)
            rows.append(
                {
                    "score_variant": score_name,
                    "label_source": label_col,
                    "n": int(len(score_df)),
                    "positive_rate": float(score_df[label_col].astype(bool).mean()),
                    "auroc": auroc,
                    "auprc": auprc,
                    "interpretation": (
                        "direction_sanity_only_not_model_selection; raw formation energy is not a composition-aware hull-distance predictor"
                    ),
                    "claim_scope": "model_facing_sensitivity_check_not_leaderboard",
                }
            )
    pd.DataFrame(rows).to_csv(OUT / "table_chgnet_score_direction_sanity.csv", index=False)


def precision_at_k(score_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    rankings = score_df.sort_values(["score", "material_id"], ascending=[False, True])
    for label_col in ["mp_stable", "alex_stable"]:
        for k in [100, 300, 500, 1000, 2000]:
            sub = rankings.head(k)
            rows.append(
                {
                    "model": "CHGNet",
                    "denominator": "full_sample_5000",
                    "label_source": label_col,
                    "K": k,
                    "precision_at_K": float(sub[label_col].astype(bool).mean()),
                    "stable_n_at_K": int(sub[label_col].astype(bool).sum()),
                    "discordant_fraction_at_K": float((sub["mp_stable"].astype(bool) != sub["alex_stable"].astype(bool)).mean()),
                    "claim_scope": "model_facing_sensitivity_check_not_leaderboard",
                }
            )
    agreement = rankings[rankings["source_agreement"].astype(bool)].copy()
    for k in [100, 300, 500, 1000, 2000]:
        if len(agreement) < k:
            continue
        sub = agreement.head(k)
        rows.append(
            {
                "model": "CHGNet",
                "denominator": "source_agreement_only",
                "label_source": "agreement_stable",
                "K": k,
                "precision_at_K": float(sub["mp_stable"].astype(bool).mean()),
                "stable_n_at_K": int(sub["mp_stable"].astype(bool).sum()),
                "discordant_fraction_at_K": 0.0,
                "claim_scope": "model_facing_sensitivity_check_not_leaderboard",
            }
        )
    return pd.DataFrame(rows)


def write_topk_discordance_decomposition(score_df: pd.DataFrame) -> None:
    ranked = score_df.sort_values(["score", "material_id"], ascending=[False, True])
    rows = []
    for k in [100, 300, 500, 1000, 2000]:
        sub = ranked.head(k)
        both_stable = sub["mp_stable"].astype(bool) & sub["alex_stable"].astype(bool)
        mp_only = sub["mp_stable"].astype(bool) & ~sub["alex_stable"].astype(bool)
        alex_only = ~sub["mp_stable"].astype(bool) & sub["alex_stable"].astype(bool)
        both_unstable = ~sub["mp_stable"].astype(bool) & ~sub["alex_stable"].astype(bool)
        rows.append(
            {
                "model": "CHGNet",
                "K": k,
                "both_stable_n": int(both_stable.sum()),
                "mp_only_stable_n": int(mp_only.sum()),
                "alex_only_stable_n": int(alex_only.sum()),
                "both_unstable_n": int(both_unstable.sum()),
                "mp_stable_n": int(sub["mp_stable"].astype(bool).sum()),
                "alex_stable_n": int(sub["alex_stable"].astype(bool).sum()),
                "mp_minus_alex_stable_n": int(sub["mp_stable"].astype(bool).sum())
                - int(sub["alex_stable"].astype(bool).sum()),
                "source_discordant_n": int((mp_only | alex_only).sum()),
                "source_discordant_fraction": float((mp_only | alex_only).mean()),
                "claim_scope": "model_facing_sensitivity_check_not_leaderboard",
            }
        )
    pd.DataFrame(rows).to_csv(OUT / "table_topk_discordance_decomposition.csv", index=False)


def write_sample_representativeness(score_df: pd.DataFrame) -> None:
    full = load_full_denominator()
    score_df = score_df.copy()
    full["n_elements"] = full["formula"].map(lambda f: len(Composition(str(f)).elements))
    score_df["n_elements"] = score_df["formula"].map(lambda f: len(Composition(str(f)).elements))
    rows = []
    for name, df in {"full_denominator": full, "chgnet_5000_sample": score_df}.items():
        rows.append(
            {
                "comparison": name,
                "stratum": "overall",
                "n": int(len(df)),
                "mp_stable_rate": float(df["mp_stable"].astype(bool).mean()),
                "alex_stable_rate": float(df["alex_stable"].astype(bool).mean()),
                "discordance_rate": float((df["mp_stable"].astype(bool) != df["alex_stable"].astype(bool)).mean()),
                "median_n_sites": float(pd.to_numeric(df.get("num_sites", pd.Series(dtype=float)), errors="coerce").median())
                if "num_sites" in df.columns
                else "",
                "median_n_elements": float(df["n_elements"].median()),
                "claim_scope": "sample_representativeness_audit",
            }
        )
        for n_el, sub in df.groupby("n_elements"):
            rows.append(
                {
                    "comparison": name,
                    "stratum": f"n_elements={int(n_el)}",
                    "n": int(len(sub)),
                    "mp_stable_rate": float(sub["mp_stable"].astype(bool).mean()),
                    "alex_stable_rate": float(sub["alex_stable"].astype(bool).mean()),
                    "discordance_rate": float((sub["mp_stable"].astype(bool) != sub["alex_stable"].astype(bool)).mean()),
                    "median_n_sites": "",
                    "median_n_elements": int(n_el),
                    "claim_scope": "sample_representativeness_audit",
                }
            )
    pd.DataFrame(rows).to_csv(OUT / "table_chgnet_sample_representativeness.csv", index=False)


def write_precision_shift_bootstrap(score_df: pd.DataFrame) -> None:
    ranked = score_df.sort_values(["score", "material_id"], ascending=[False, True]).reset_index(drop=True)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    rows = []
    for k in [100, 300, 500, 1000, 2000]:
        top = ranked.head(k).reset_index(drop=True)
        obs = float(top["mp_stable"].astype(bool).mean() - top["alex_stable"].astype(bool).mean())
        mp_n = int(top["mp_stable"].astype(bool).sum())
        alex_n = int(top["alex_stable"].astype(bool).sum())
        shifts = []
        idx = np.arange(k)
        for _ in range(N_BOOTSTRAP):
            sample_idx = rng.choice(idx, size=k, replace=True)
            boot = top.iloc[sample_idx]
            shifts.append(float(boot["mp_stable"].astype(bool).mean() - boot["alex_stable"].astype(bool).mean()))
        lo, hi = np.quantile(shifts, [0.025, 0.975])
        rows.append(
            {
                "model": "CHGNet",
                "K": k,
                "mp_stable_n": mp_n,
                "alex_stable_n": alex_n,
                "observed_mp_minus_alex_precision_shift": obs,
                "bootstrap_ci_low": float(lo),
                "bootstrap_ci_high": float(hi),
                "n_bootstrap": N_BOOTSTRAP,
                "bootstrap_seed": BOOTSTRAP_SEED,
                "claim_scope": "uncertainty_for_model_facing_sensitivity_check",
            }
        )
    pd.DataFrame(rows).to_csv(OUT / "table_precision_shift_bootstrap.csv", index=False)


def write_metrics(score_df: pd.DataFrame) -> None:
    write_score_direction_sanity(score_df)
    write_topk_discordance_decomposition(score_df)
    write_sample_representativeness(score_df)
    write_precision_shift_bootstrap(score_df)
    rows = [
        threshold_metrics(score_df, "mp_stable", "full_sample_5000"),
        threshold_metrics(score_df, "alex_stable", "full_sample_5000"),
    ]
    agreement = score_df[score_df["source_agreement"].astype(bool)].copy()
    rows.append(threshold_metrics(agreement, "mp_stable", "source_agreement_only"))
    metrics = pd.DataFrame(rows)
    mp = metrics[metrics["label_source"].eq("mp_stable") & metrics["denominator"].eq("full_sample_5000")].iloc[0]
    alex = metrics[metrics["label_source"].eq("alex_stable") & metrics["denominator"].eq("full_sample_5000")].iloc[0]
    metrics["delta_vs_alex_auroc"] = ""
    metrics["delta_vs_alex_auprc"] = ""
    full_mp_mask = metrics["label_source"].eq("mp_stable") & metrics["denominator"].eq("full_sample_5000")
    metrics.loc[full_mp_mask, "delta_vs_alex_auroc"] = float(mp["auroc"]) - float(alex["auroc"])
    metrics.loc[full_mp_mask, "delta_vs_alex_auprc"] = float(mp["auprc"]) - float(alex["auprc"])
    metrics.to_csv(OUT / "table_model_metric_source_sensitivity.csv", index=False)

    pk = precision_at_k(score_df)
    mp_pk = pk[pk["denominator"].eq("full_sample_5000") & pk["label_source"].eq("mp_stable")][
        ["K", "precision_at_K"]
    ].rename(columns={"precision_at_K": "mp_precision_at_K"})
    alex_pk = pk[pk["denominator"].eq("full_sample_5000") & pk["label_source"].eq("alex_stable")][
        ["K", "precision_at_K"]
    ].rename(columns={"precision_at_K": "alex_precision_at_K"})
    shift = mp_pk.merge(alex_pk, on="K")
    shift["metric_shift_mp_minus_alex"] = shift["mp_precision_at_K"] - shift["alex_precision_at_K"]
    shift["model"] = "CHGNet"
    shift["claim_scope"] = "model_facing_sensitivity_check_not_leaderboard"
    pk.to_csv(OUT / "table_precision_at_k_source_sensitivity.csv", index=False)
    shift.to_csv(OUT / "table_precision_at_k_metric_shift.csv", index=False)


def write_closeout() -> None:
    manifest = pd.read_csv(OUT / "table_chgnet_scored_subset_manifest.csv")
    sanity = pd.read_csv(OUT / "table_chgnet_score_direction_sanity.csv")
    metrics = pd.read_csv(OUT / "table_model_metric_source_sensitivity.csv")
    pk = pd.read_csv(OUT / "table_precision_at_k_source_sensitivity.csv")
    shift = pd.read_csv(OUT / "table_precision_at_k_metric_shift.csv")
    decomp = pd.read_csv(OUT / "table_topk_discordance_decomposition.csv")
    representativeness = pd.read_csv(OUT / "table_chgnet_sample_representativeness.csv")
    bootstrap = pd.read_csv(OUT / "table_precision_shift_bootstrap.csv")
    (OUT / "MODEL_FACING_BENCHMARK_SENSITIVITY_CHECK.md").write_text(
        "# Model-Facing Benchmark Sensitivity Check\n\n"
        "This completed diagnostic uses one real model ranking, CHGNet, on a deterministic 5,000-structure subset of the 43,139 strict MP-Alex denominator. "
        "Scores are negative CHGNet formation-energy proxies constructed from CHGNet structure energies and MP elemental reference structures. "
        "The result is not a leaderboard and does not compare multiple models; it checks whether the label-source effect observed in the oracle/source-label analysis also appears under a real ranking.\n\n"
        "The score-direction sanity check is intentionally reported before interpretation. "
        "The raw formation-energy proxy direction has AUROC above 0.5 on this subset, while the negative-formation direction used for the frozen ranking has AUROC below 0.5. "
        "This is not promoted as a model-quality result: raw CHGNet formation-energy proxies are not composition-aware hull-distance predictors, and this diagnostic is used only to measure label-source sensitivity under a real, reproducible ranking.\n\n"
        "## Scoring Manifest\n\n"
        f"{manifest.to_markdown(index=False)}\n\n"
        "## Threshold-Free Metrics\n\n"
        f"{metrics.to_markdown(index=False)}\n\n"
        "## Score-Direction Sanity Check\n\n"
        f"{sanity.to_markdown(index=False)}\n\n"
        "## Precision at K\n\n"
        f"{pk.to_markdown(index=False)}\n\n"
        "## MP-minus-Alex Precision Shift\n\n"
        f"{shift.to_markdown(index=False)}\n\n"
        "## Top-K Discordance Decomposition\n\n"
        f"{decomp.to_markdown(index=False)}\n\n"
        "## Precision-Shift Bootstrap\n\n"
        f"{bootstrap.to_markdown(index=False)}\n\n"
        "## Sample Representativeness\n\n"
        f"{representativeness.to_markdown(index=False)}\n",
        encoding="utf-8",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    score_path = OUT / "candidate_scores_chgnet_5000.csv"
    if score_path.exists():
        print(f"Reusing existing score table: {score_path}", flush=True)
        score_df = pd.read_csv(score_path)
    else:
        df = load_scoring_sample()
        score_df = score_subset(df)
    write_metrics(score_df)
    write_closeout()
    write_manifest()


if __name__ == "__main__":
    main()
