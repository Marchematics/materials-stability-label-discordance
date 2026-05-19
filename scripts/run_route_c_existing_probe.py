from __future__ import annotations

import csv
import hashlib
import math
import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import balanced_accuracy_score, f1_score, precision_score


ROOT = Path(__file__).resolve().parents[1]
SRC = Path("/home/waas/paper_experiments/github/Certified-Open-Vocabulary-MOT")
OUT = ROOT / "outputs" / "milestones" / "materials_label_discordance_preregistration"
MATCHES = SRC / "outputs/milestones/materials_alex_mp_a1_a2_validation/table_alex_mp_a2_candidate_matches.csv"
STEP1 = Path("/home/waas/paper_experiments/private/materials_prospective_dft_followup_chgnet_v2/wbm_raw/step_1.json.bz2")
STEP_DIR = Path("/home/waas/paper_experiments/private/wbm_raw_full")


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


def score_m3gnet(material_ids: set[str], exact: pd.DataFrame) -> pd.DataFrame:
    sys.path.insert(0, str(SRC / "scripts"))
    from build_materials_alex_mp_a1_a2_validation import load_wbm_structures  # noqa: PLC0415

    import matgl  # noqa: PLC0415

    structures = load_wbm_structures(material_ids, step1=STEP1, step_dir=STEP_DIR)
    model_name = "M3GNet-Eform-MP-2018.6.1"
    model = matgl.load_model(model_name)

    rows: list[dict[str, object]] = []
    for idx, row in enumerate(exact.sort_values("material_id").itertuples(index=False), start=1):
        material_id = str(row.material_id)
        structure = structures.get(material_id)
        if structure is None:
            rows.append(
                {
                    "material_id": material_id,
                    "formula": row.formula,
                    "model": "M3GNet",
                    "score_status": "failed_missing_wbm_structure",
                    "energy_per_atom": "",
                    "score": "",
                    "score_type": "formation_energy_per_atom_lower_is_more_stable",
                    "model_identifier": model_name,
                }
            )
            continue
        try:
            pred = model.predict_structure(structure)
            energy = float(pred)
            status = "scored" if math.isfinite(energy) and abs(energy) < 1e6 else "failed_nonfinite_or_nonphysical"
        except Exception as exc:  # noqa: BLE001
            energy = math.nan
            status = f"failed_{type(exc).__name__}"
        rows.append(
            {
                "material_id": material_id,
                "formula": row.formula,
                "model": "M3GNet",
                "score_status": status,
                "energy_per_atom": energy if math.isfinite(energy) else "",
                "score": energy if math.isfinite(energy) else "",
                "score_type": "formation_energy_per_atom_lower_is_more_stable",
                "model_identifier": model_name,
            }
        )
        if idx % 25 == 0:
            print(f"M3GNet scored {idx}/{len(exact)} exact-match structures", flush=True)
    return pd.DataFrame(rows)


def metric_rows(scores: pd.DataFrame, exact: pd.DataFrame) -> list[dict[str, object]]:
    labels = exact.set_index("material_id")[["wbm_stable_DFT", "alex_stable_exact"]].copy()
    labels.index = labels.index.astype(str)
    rows: list[dict[str, object]] = []
    for model, sdf in scores[scores["score_status"].eq("scored")].groupby("model"):
        sdf = sdf.copy()
        sdf["material_id"] = sdf["material_id"].astype(str)
        common = sorted(set(sdf["material_id"]) & set(labels.index))
        if not common:
            continue
        sub = sdf.set_index("material_id").loc[common].copy()
        n = len(sub)
        predicted_positive_n = max(math.ceil(0.05 * n), 20)
        predicted_positive = set(sub.sort_values("score", ascending=True).head(predicted_positive_n).index)
        y_pred = [mid in predicted_positive for mid in common]
        for source, col in [("WBM", "wbm_stable_DFT"), ("alex-mp", "alex_stable_exact")]:
            y_true = [bool(v) for v in labels.loc[common, col].tolist()]
            rows.append(
                {
                    "model": model,
                    "label_source": source,
                    "n_common": n,
                    "predicted_positive_rule": "top_max_5_percent_or_20_by_frozen_score",
                    "predicted_positive_n": predicted_positive_n,
                    "stable_positive_n": int(sum(y_true)),
                    "stable_class_F1_primary": f1_score(y_true, y_pred, zero_division=0),
                    "balanced_accuracy_coprimary": balanced_accuracy_score(y_true, y_pred),
                    "precision_discovery": precision_score(y_true, y_pred, zero_division=0),
                    "discovered_stable_count": int(sum(yt and yp for yt, yp in zip(y_true, y_pred, strict=True))),
                    "score_col": f"score_{model.lower().replace('-', '_')}",
                }
            )
    return rows


def ranking_summary(metrics: pd.DataFrame) -> dict[str, object]:
    pivot = metrics.pivot(index="model", columns="label_source", values="stable_class_F1_primary")
    required_models = ["CHGNet", "MACE-MP", "M3GNet"]
    eligible = [m for m in required_models if m in pivot.index and not pivot.loc[m].isna().any()]
    if len(eligible) < 3:
        return {
            "endpoint": "route_c_existing_probe_alternative_frontier_ranking",
            "models_required": "|".join(required_models),
            "models_eligible": "|".join(eligible),
            "n_common_floor": 200,
            "status": "reduced_panel_or_incomplete",
            "top_model_flip": False,
            "ordering_flip": False,
            "max_abs_F1_delta": "",
            "go_no_go": "NO_GO_route_c_existing_probe_model_gate_incomplete",
            "claim_scope": "diagnostic_only_not_full_route_c_primary",
        }
    wbm_order = list(pivot.loc[eligible].sort_values("WBM", ascending=False).index)
    alex_order = list(pivot.loc[eligible].sort_values("alex-mp", ascending=False).index)
    top_model_flip = wbm_order[0] != alex_order[0]
    ordering_flip = wbm_order != alex_order
    max_abs = float((pivot.loc[eligible, "WBM"] - pivot.loc[eligible, "alex-mp"]).abs().max())
    pass_gate = (top_model_flip or ordering_flip) and max_abs >= 0.05
    return {
        "endpoint": "route_c_existing_probe_alternative_frontier_ranking",
        "models_required": "|".join(required_models),
        "models_eligible": "|".join(eligible),
        "n_common_floor": 200,
        "status": "run_existing_probe_not_full_mp_alex_route_c",
        "top_model_flip": bool(top_model_flip),
        "ordering_flip": bool(ordering_flip),
        "max_abs_F1_delta": max_abs,
        "go_no_go": "PASS_existing_probe_ranking_flip_diagnostic" if pass_gate else "NO_GO_existing_probe_no_material_F1_ranking_flip",
        "claim_scope": "existing_WBM_vs_alex_probe_only; not full MP-vs-Alex Route C primary",
    }


def write_closeout(summary: dict[str, object], metrics: pd.DataFrame, scores: pd.DataFrame) -> None:
    text = f"""# Route C Existing-Probe Diagnostic

## Status

```text
completed diagnostic
not full MP-vs-Alex Route C primary
Route B remains blocked and unconsumed
```

## What Was Run

The alternative-frontier Route C panel was evaluated on the existing
WBM/Matbench-vs-alex exact-structure denominator. This uses the same 270
exact-structure matched rows as the earlier discordance probe.

This is not the full Route C rescue because the full MP API-derived snapshot
denominator was not exported in this run. It is a same-denominator model-panel
diagnostic only.

## Model Panel

```text
CHGNet
MACE-MP
M3GNet-Eform-MP-2018.6.1 via MatGL
```

M3GNet was selected as the third model before computing Route C ranking
outcomes because it is locally executable through MatGL in this environment.

## Lead Result

```text
models eligible: {summary['models_eligible']}
top model flip: {summary['top_model_flip']}
ordering flip: {summary['ordering_flip']}
max absolute stable-F1 delta: {summary['max_abs_F1_delta']}
go/no-go: {summary['go_no_go']}
claim scope: {summary['claim_scope']}
```

## Claim Boundary

This result may be cited only as an existing-probe diagnostic. It cannot reopen
the NMI discordance line by itself because the preregistered Route C full
snapshot denominator has not been constructed. A full Route C result still
requires:

```text
MP API-derived records vs independently downloaded alex-mp snapshot
strict StructureMatcher denominator
n_common >= 200
CHGNet / MACE-MP / frozen third model on the same denominator
discordance >= 0.40
alternative-frontier stable-F1 ranking flip
```
"""
    (OUT / "ROUTE_C_EXISTING_PROBE_EXPERIMENT.md").write_text(text, encoding="utf-8")


def main() -> None:
    exact = pd.read_csv(MATCHES)
    exact = exact[exact["match_confidence"].eq("exact_structure_match")].copy()
    exact["material_id"] = exact["material_id"].astype(str)
    material_ids = set(exact["material_id"])

    base_scores = pd.read_csv(OUT / "table_frontier_model_scores.csv")
    base_scores = base_scores[base_scores["model"].isin(["CHGNet", "MACE-MP"])].copy()
    m3gnet_scores = score_m3gnet(material_ids, exact)
    scores = pd.concat([base_scores, m3gnet_scores], ignore_index=True)
    scores.to_csv(OUT / "table_route_c_existing_probe_model_scores.csv", index=False)

    metrics = pd.DataFrame(metric_rows(scores, exact))
    metrics.to_csv(OUT / "table_route_c_existing_probe_ranking_metrics.csv", index=False)

    summary = ranking_summary(metrics)
    pd.DataFrame([summary]).to_csv(OUT / "table_route_c_existing_probe_flip_summary.csv", index=False)
    write_closeout(summary, metrics, scores)
    write_manifest()


if __name__ == "__main__":
    main()
