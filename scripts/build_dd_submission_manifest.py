#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def shape(path: Path) -> tuple[int | None, int | None]:
    try:
        if path.suffix == ".csv":
            frame = pd.read_csv(path)
            return len(frame), len(frame.columns)
        if path.suffix == ".parquet":
            frame = pd.read_parquet(path)
            return len(frame), len(frame.columns)
        if path.suffix == ".json":
            payload = json.loads(path.read_text())
            return (len(payload), 1) if isinstance(payload, (dict, list)) else (1, 1)
    except Exception:
        pass
    return None, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out = (ROOT / args.out).resolve() if not args.out.is_absolute() else args.out.resolve()
    files = []
    for path in sorted(args.out.rglob("*")):
        if not path.is_file() or path.name in {
            "manifest_dd_submission_v2.json",
            # This run-time status file is excluded from the immutable data
            # bundle.
            "manuscript_claims_check.json",
        }:
            continue
        rows, columns = shape(path)
        files.append({
            "path": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "rows": rows,
            "columns": columns,
            "sha256": sha(path),
            "generating_script": "scripts/build_submission_figures.py" if "figure" in path.parts else "run_all.sh or cited phase builder",
        })
    manifest = {
        "release": "v2.0.0-dd-submission",
        "evidence_scope": "released source-aware benchmark and model-evaluation outputs",
        "file_count": len(files),
        "files": files,
    }
    (args.out / "manifest_dd_submission_v2.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
