#!/usr/bin/env python3
"""Write checksums and tabular dimensions for the M1 archival release."""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import date
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "repaired_model_evaluation_v2"

REQUIRED = (
    "score_construct_validity_audit.csv",
    "endpoint_definition_table.csv",
    "evaluation_support_and_coverage.csv",
    "all_view_common_support_exclusion_audit.csv",
    "metrics_fixed_support.csv",
    "topk_fixed_support.csv",
    "label_bands_cluster_bootstrap.csv",
    "label_bands_cluster_bootstrap_replicates.parquet",
    "paired_metric_values_cluster_bootstrap_replicates.parquet",
    "endpoint_sensitivity_to_model_spread_ratio_bootstrap.csv",
    "endpoint_sensitivity_to_model_spread_ratio_bootstrap_replicates.parquet",
    "paired_label_view_differences_cluster_bootstrap.csv",
    "model_winner_probabilities_cluster_bootstrap.csv",
    "elemental_reference_structures.jsonl",
    "fixed_subsystem_phase_pool_manifest.json",
    "reproducibility/environment_manifest.json",
    "reproducibility/pytest_endpoint_layer_revision.log",
    "reproducibility/figure_regeneration_endpoint_layer_revision.log",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dimensions(path: Path) -> tuple[int | None, int | None]:
    if path.suffix == ".csv":
        frame = pd.read_csv(path)
        return int(len(frame)), int(len(frame.columns))
    if path.suffix == ".parquet":
        frame = pd.read_parquet(path)
        return int(len(frame)), int(len(frame.columns))
    return None, None


def main() -> None:
    reproducibility = OUT / "reproducibility"
    reproducibility.mkdir(parents=True, exist_ok=True)
    environment = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "environment_yml_sha256": sha256(ROOT / "environment.yml"),
        "requirements_lock_sha256": sha256(ROOT / "requirements-lock.txt"),
        "dockerfile_sha256": sha256(ROOT / "Dockerfile"),
    }
    (reproducibility / "environment_manifest.json").write_text(
        json.dumps(environment, indent=2) + "\n", encoding="utf-8"
    )
    missing = [name for name in REQUIRED if not (OUT / name).is_file()]
    if missing:
        raise FileNotFoundError("Required archival artifacts missing: " + ", ".join(missing))
    files = []
    for name in REQUIRED:
        path = OUT / name
        rows, columns = dimensions(path)
        files.append({
            "path": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "rows": rows,
            "columns": columns,
            "sha256": sha256(path),
        })
    for name in ("environment.yml", "requirements-lock.txt", "Dockerfile", "run_all.sh"):
        path = ROOT / name
        files.append({
            "path": name,
            "bytes": path.stat().st_size,
            "rows": None,
            "columns": None,
            "sha256": sha256(path),
        })
    payload = {
        "release_series": "v2.0.4-dd-revision-candidate",
        "analysis": "M1 endpoint-layer fixed-support model evaluation",
        "generated_on": str(date.today()),
        "file_count": len(files),
        "files": files,
    }
    (OUT / "manifest_repaired_model_evaluation_v2.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(OUT / "manifest_repaired_model_evaluation_v2.json")


if __name__ == "__main__":
    main()
