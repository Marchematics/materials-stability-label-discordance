#!/usr/bin/env python3
"""Backfill decomposition-simplex evidence into LOSO exclusion audits.

The ranking builder now emits these fields directly. This utility upgrades already
computed primary and matching-sensitivity audits without recomputing hulls.
"""
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "outputs" / "referee_revision_v3"
MODELS = {
    "alignn_ff": "ALIGNN-FF",
    "chgnet": "CHGNet",
    "m3gnet": "M3GNet",
    "mace_mp": "MACE-MP",
}


def upgrade(directory: Path, slug: str, model: str) -> dict:
    audit_path = directory / f"loso_exclusion_audit_{slug}.parquet"
    if directory == BASE:
        score_path = directory / f"batch_relative_signed_reference_hull_scores_{model}.parquet"
    else:
        score_path = directory / f"batch_relative_signed_reference_hull_scores_{model}.parquet"
    audit = pd.read_parquet(audit_path)
    scores = pd.read_parquet(score_path, columns=[
        "row_id", "score_status", "decomposition_simplex_json"
    ]).rename(columns={"row_id": "candidate_row_id"})
    drop = [c for c in [
        "decomposition_simplex_json", "decomposition_simplex_phase_ids_json",
        "excluded_rows_in_decomposition_simplex_json",
        "decomposition_simplex_excludes_equivalence_class", "score_status"
    ] if c in audit.columns]
    audit = audit.drop(columns=drop).merge(scores, on="candidate_row_id", how="left", validate="one_to_one")

    phase_ids = []
    overlaps = []
    passes = []
    for row in audit.itertuples(index=False):
        simplex = json.loads(row.decomposition_simplex_json)
        ids = sorted(str(value["phase_id"]) for value in simplex)
        excluded = set(json.loads(row.excluded_row_ids_json))
        overlap = sorted(excluded.intersection(ids))
        phase_ids.append(json.dumps(ids))
        overlaps.append(json.dumps(overlap))
        passes.append(not overlap and row.score_status == "ok")
    audit["decomposition_simplex_phase_ids_json"] = phase_ids
    audit["excluded_rows_in_decomposition_simplex_json"] = overlaps
    audit["decomposition_simplex_excludes_equivalence_class"] = passes
    audit["exclusion_verified"] = (
        audit["all_equivalence_class_members_excluded"].astype(bool)
        & audit["decomposition_simplex_excludes_equivalence_class"].astype(bool)
        & audit["score_status"].eq("ok")
    )
    audit.to_parquet(audit_path, index=False)
    return {
        "setting": "primary" if directory == BASE else directory.name,
        "model_name": model,
        "row_n": int(len(audit)),
        "score_ok_n": int(audit["score_status"].eq("ok").sum()),
        "simplex_exclusion_pass_n": int(audit["decomposition_simplex_excludes_equivalence_class"].sum()),
        "full_exclusion_verified_n": int(audit["exclusion_verified"].sum()),
        "simplex_overlap_n": int((~audit["decomposition_simplex_excludes_equivalence_class"]).sum()),
    }


def main() -> None:
    rows = []
    for slug, model in MODELS.items():
        rows.append(upgrade(BASE, slug, model))
    for setting in ("tight", "default", "loose"):
        directory = BASE / "matching_sensitivity" / setting
        for slug, model in MODELS.items():
            rows.append(upgrade(directory, slug, model))
    out = pd.DataFrame(rows)
    if not (
        out["row_n"].eq(out["score_ok_n"]).all()
        and out["row_n"].eq(out["simplex_exclusion_pass_n"]).all()
        and out["row_n"].eq(out["full_exclusion_verified_n"]).all()
    ):
        raise RuntimeError(out.to_string(index=False))
    out.to_csv(BASE / "loso_exclusion_audit_summary.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
