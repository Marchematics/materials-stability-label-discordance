from __future__ import annotations

import csv
import hashlib
import math
import os
import sys
import zipfile
from io import StringIO
from pathlib import Path

import pandas as pd
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.core import Structure
from pymatgen.io.ase import AseAtomsAdaptor
from sklearn.metrics import balanced_accuracy_score, f1_score, precision_score


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "milestones" / "materials_label_discordance_preregistration"
ALEX_ZIP = Path("/home/waas/paper_experiments/private/mattergen_repo/data-release/alex-mp/alex_mp_20.zip")
ALIGNN_MODEL_PATH = Path("/root/alignn_ff_models/v12.2.2024_dft_3d_307k")


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


def load_alex_candidates(limit: int = 1200) -> pd.DataFrame:
    frames = []
    with zipfile.ZipFile(ALEX_ZIP) as zf:
        for name in ["alex_mp_20/val.csv", "alex_mp_20/train.csv"]:
            with zf.open(name) as f:
                df = pd.read_csv(
                    f,
                    usecols=["material_id", "reduced_formula", "chemical_system", "num_sites", "cif", "energy_above_hull"],
                )
            frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df["is_mp_queryable_id"] = df["material_id"].astype(str).str.startswith("mp-")
    excluded = df[~df["is_mp_queryable_id"]].copy()
    if not excluded.empty:
        excluded[["material_id", "reduced_formula", "chemical_system", "num_sites", "energy_above_hull"]].head(5000).to_csv(
            OUT / "table_route_b_full_snapshot_excluded_non_mp_ids.csv",
            index=False,
        )
    df = df[df["is_mp_queryable_id"]].drop(columns=["is_mp_queryable_id"])
    df = df.drop_duplicates("material_id").sort_values("material_id").head(limit).copy()
    df["alex_stable_exact"] = df["energy_above_hull"].astype(float) <= 0.0
    return df


def filter_mp_queryable_alex_candidates(alex: pd.DataFrame) -> pd.DataFrame:
    alex = alex.copy()
    alex["is_mp_queryable_id"] = alex["material_id"].astype(str).str.startswith("mp-")
    excluded = alex[~alex["is_mp_queryable_id"]].copy()
    if not excluded.empty:
        excluded[["material_id", "reduced_formula", "chemical_system", "num_sites", "energy_above_hull"]].to_csv(
            OUT / "table_route_b_full_snapshot_excluded_non_mp_ids.csv",
            index=False,
        )
    return alex[alex["is_mp_queryable_id"]].drop(columns=["is_mp_queryable_id"]).copy()


def fetch_mp_records(material_ids: list[str]) -> dict[str, object]:
    from mp_api.client import MPRester

    api_key = os.environ.get("MP_API_KEY")
    if not api_key:
        raise RuntimeError("MP_API_KEY environment variable is required; credentials are not read from files.")
    records = {}
    with MPRester(api_key) as mpr:
        for i in range(0, len(material_ids), 100):
            chunk = material_ids[i : i + 100]
            docs = mpr.materials.summary.search(
                material_ids=chunk,
                fields=["material_id", "formula_pretty", "energy_above_hull", "structure"],
            )
            for doc in docs:
                records[str(doc.material_id)] = doc
            print(f"fetched MP records {min(i+100, len(material_ids))}/{len(material_ids)}", flush=True)
    return records


def build_denominator(alex: pd.DataFrame, mp_records: dict[str, object]) -> pd.DataFrame:
    matcher = StructureMatcher(
        ltol=0.2,
        stol=0.3,
        angle_tol=5,
        primitive_cell=True,
        scale=True,
        attempt_supercell=True,
    )
    rows = []
    for row in alex.itertuples(index=False):
        mid = str(row.material_id)
        doc = mp_records.get(mid)
        if doc is None:
            rows.append(
                {
                    "material_id": mid,
                    "match_status": "missing_mp_record",
                    "formula": row.reduced_formula,
                    "mp_e_above_hull": "",
                    "alex_e_above_hull": row.energy_above_hull,
                    "mp_stable_exact": "",
                    "alex_stable_exact": bool(row.alex_stable_exact),
                    "structure_match": False,
                }
            )
            continue
        try:
            alex_structure = Structure.from_str(row.cif, fmt="cif")
            mp_structure = doc.structure
            matched = matcher.fit(mp_structure, alex_structure)
        except Exception as exc:  # noqa: BLE001
            matched = False
            rows.append(
                {
                    "material_id": mid,
                    "match_status": f"match_error_{type(exc).__name__}",
                    "formula": row.reduced_formula,
                    "mp_e_above_hull": getattr(doc, "energy_above_hull", ""),
                    "alex_e_above_hull": row.energy_above_hull,
                    "mp_stable_exact": bool(getattr(doc, "energy_above_hull", math.inf) <= 0),
                    "alex_stable_exact": bool(row.alex_stable_exact),
                    "structure_match": matched,
                }
            )
            continue
        rows.append(
            {
                "material_id": mid,
                "match_status": "strict_structure_match" if matched else "structure_mismatch",
                "formula": row.reduced_formula,
                "mp_e_above_hull": float(doc.energy_above_hull) if doc.energy_above_hull is not None else "",
                "alex_e_above_hull": float(row.energy_above_hull),
                "mp_stable_exact": bool((doc.energy_above_hull or 0) <= 0),
                "alex_stable_exact": bool(row.alex_stable_exact),
                "structure_match": matched,
            }
        )
    return pd.DataFrame(rows)


def score_models(alex: pd.DataFrame, denom: pd.DataFrame) -> pd.DataFrame:
    from alignn.ff.ff import AlignnAtomwiseCalculator
    from chgnet.model.model import CHGNet
    from mace.calculators import mace_mp
    import torch

    ids = set(denom[denom["match_status"].eq("strict_structure_match")]["material_id"].astype(str))
    alex = alex[alex["material_id"].astype(str).isin(ids)].copy()
    chgnet = CHGNet.load()
    mace = mace_mp(model="small", device="cuda" if torch.cuda.is_available() else "cpu", default_dtype="float32")
    alignn = AlignnAtomwiseCalculator(path=str(ALIGNN_MODEL_PATH), device="cpu")

    score_path = OUT / "table_route_b_full_snapshot_model_scores.csv"
    fieldnames = ["material_id", "model", "score_status", "score"]
    completed_ids: set[str] = set()
    if score_path.exists():
        existing = pd.read_csv(score_path)
        if not existing.empty and set(fieldnames).issubset(existing.columns):
            counts = existing.groupby("material_id")["model"].nunique()
            completed_ids = set(counts[counts >= 3].index.astype(str))
            print(f"resuming Route B scoring; completed structures: {len(completed_ids)}", flush=True)
    if not score_path.exists():
        with score_path.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=fieldnames).writeheader()

    rows = []
    for idx, row in enumerate(alex.sort_values("material_id").itertuples(index=False), start=1):
        mid = str(row.material_id)
        if mid in completed_ids:
            continue
        candidate_rows = []
        try:
            structure = Structure.from_str(row.cif, fmt="cif")
        except Exception as exc:  # noqa: BLE001
            for model in ["ALIGNN-FF", "CHGNet", "MACE-MP"]:
                candidate_rows.append({"material_id": mid, "model": model, "score_status": f"failed_parse_{type(exc).__name__}", "score": ""})
            with score_path.open("a", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=fieldnames).writerows(candidate_rows)
            rows.extend(candidate_rows)
            continue
        try:
            atoms = AseAtomsAdaptor.get_atoms(structure)
            atoms.calc = alignn
            score = float(atoms.get_potential_energy()) / max(1, len(atoms))
            candidate_rows.append({"material_id": mid, "model": "ALIGNN-FF", "score_status": "scored", "score": score})
        except Exception as exc:  # noqa: BLE001
            candidate_rows.append({"material_id": mid, "model": "ALIGNN-FF", "score_status": f"failed_{type(exc).__name__}", "score": ""})
        try:
            pred = chgnet.predict_structure(structure)
            candidate_rows.append({"material_id": mid, "model": "CHGNet", "score_status": "scored", "score": float(pred["e"])})
        except Exception as exc:  # noqa: BLE001
            candidate_rows.append({"material_id": mid, "model": "CHGNet", "score_status": f"failed_{type(exc).__name__}", "score": ""})
        try:
            atoms = AseAtomsAdaptor.get_atoms(structure)
            atoms.calc = mace
            score = float(atoms.get_potential_energy()) / max(1, len(atoms))
            candidate_rows.append({"material_id": mid, "model": "MACE-MP", "score_status": "scored", "score": score})
        except Exception as exc:  # noqa: BLE001
            candidate_rows.append({"material_id": mid, "model": "MACE-MP", "score_status": f"failed_{type(exc).__name__}", "score": ""})
        with score_path.open("a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=fieldnames).writerows(candidate_rows)
        rows.extend(candidate_rows)
        if idx % 25 == 0:
            print(f"scored Route B structures {idx}/{len(alex)}", flush=True)
    return pd.read_csv(score_path)


def compute_metrics(denom: pd.DataFrame, scores: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    labels = denom[denom["match_status"].eq("strict_structure_match")].set_index("material_id")
    rows = []
    for model, sdf in scores[scores["score_status"].eq("scored")].groupby("model"):
        common = sorted(set(sdf["material_id"].astype(str)) & set(labels.index.astype(str)))
        if not common:
            continue
        sub = sdf.set_index("material_id").loc[common]
        n = len(common)
        pred_n = max(math.ceil(0.05 * n), 20)
        pred_pos = set(sub.sort_values("score", ascending=True).head(pred_n).index)
        y_pred = [mid in pred_pos for mid in common]
        for source, col in [("MP", "mp_stable_exact"), ("alex-mp", "alex_stable_exact")]:
            y_true = [bool(v) for v in labels.loc[common, col].tolist()]
            rows.append(
                {
                    "model": model,
                    "label_source": source,
                    "n_common": n,
                    "predicted_positive_rule": "top_max_5_percent_or_20_by_frozen_score",
                    "predicted_positive_n": pred_n,
                    "stable_positive_n": int(sum(y_true)),
                    "stable_class_F1_primary": f1_score(y_true, y_pred, zero_division=0),
                    "balanced_accuracy_coprimary": balanced_accuracy_score(y_true, y_pred),
                    "precision_discovery": precision_score(y_true, y_pred, zero_division=0),
                    "discovered_stable_count": int(sum(yt and yp for yt, yp in zip(y_true, y_pred, strict=True))),
                }
            )
    metrics = pd.DataFrame(rows)
    pivot = metrics.pivot(index="model", columns="label_source", values="stable_class_F1_primary")
    eligible = [m for m in ["ALIGNN-FF", "CHGNet", "MACE-MP"] if m in pivot.index and not pivot.loc[m].isna().any()]
    discordance = (labels["mp_stable_exact"].astype(bool) != labels["alex_stable_exact"].astype(bool)).mean()
    if len(eligible) == 3:
        mp_order = list(pivot.loc[eligible].sort_values("MP", ascending=False).index)
        alex_order = list(pivot.loc[eligible].sort_values("alex-mp", ascending=False).index)
        top_flip = mp_order[0] != alex_order[0]
        ordering_flip = mp_order != alex_order
        max_delta = float((pivot.loc[eligible, "MP"] - pivot.loc[eligible, "alex-mp"]).abs().max())
    else:
        top_flip = False
        ordering_flip = False
        max_delta = math.nan
    pass_gate = len(labels) >= 200 and discordance >= 0.40 and (top_flip or ordering_flip) and max_delta >= 0.05
    summary = pd.DataFrame(
        [
            {
                "endpoint": "route_b_full_snapshot_rescue",
                "n_common": len(labels),
                "discordance_rate": discordance,
                "models_eligible": "|".join(eligible),
                "top_model_flip": top_flip,
                "ordering_flip": ordering_flip,
                "max_abs_F1_delta": max_delta,
                "go_no_go": "PASS_reopen_NMI_line" if pass_gate else "NO_GO_keep_NMI_line_closed",
                "claim_scope": "diagnostic_until_ALIGNN_FF_clean_hash_match_and_source_archive_PASS",
            }
        ]
    )
    return metrics, summary


def main() -> None:
    alex = load_alex_candidates(limit=int(os.environ.get("ROUTE_B_ALEX_LIMIT", "1200")))
    ids = alex["material_id"].astype(str).tolist()
    try:
        mp_records = fetch_mp_records(ids)
    except Exception as exc:  # noqa: BLE001
        OUT.mkdir(parents=True, exist_ok=True)
        with (OUT / "table_route_b_full_snapshot_data_access_failure.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["stage", "status", "error_type", "message"])
            writer.writeheader()
            writer.writerow({"stage": "mp_api_fetch", "status": "failed", "error_type": type(exc).__name__, "message": str(exc)[:500]})
        (OUT / "ROUTE_B_FULL_SNAPSHOT_RESCUE_CLOSEOUT.md").write_text(
            "# Route B Full Snapshot Rescue\n\nStatus: blocked at MP API data-access gate.\n\n"
            "The runner requires `MP_API_KEY` in the environment and does not read credentials from files.\n",
            encoding="utf-8",
        )
        write_manifest()
        raise
    denom = build_denominator(alex, mp_records)
    denom.to_csv(OUT / "table_route_b_full_snapshot_matches.csv", index=False)
    scores = score_models(alex, denom)
    scores.to_csv(OUT / "table_route_b_full_snapshot_model_scores.csv", index=False)
    metrics, summary = compute_metrics(denom, scores)
    metrics.to_csv(OUT / "table_route_b_full_snapshot_ranking_metrics.csv", index=False)
    summary.to_csv(OUT / "table_route_b_full_snapshot_summary.csv", index=False)
    (OUT / "ROUTE_B_FULL_SNAPSHOT_RESCUE_CLOSEOUT.md").write_text(
        "# Route B Full Snapshot Rescue\n\n"
        f"Status: completed diagnostic.\n\n{summary.to_markdown(index=False)}\n",
        encoding="utf-8",
    )
    write_manifest()


if __name__ == "__main__":
    main()
