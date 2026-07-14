#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
LOG_DIR="outputs/dd_submission_v2/logs"
mkdir -p "$LOG_DIR"

run_logged() {
  local name="$1"; shift
  printf '==> %s\n' "$*" | tee "$LOG_DIR/${name}.log"
  "$@" 2>&1 | tee -a "$LOG_DIR/${name}.log"
}

run_logged benchmark_card python scripts/generate_benchmark_card.py --check
run_logged repaired_figures python scripts/build_repaired_model_figures.py
run_logged repaired_claims python scripts/audit_repaired_model_claims.py
run_logged pytest pytest -q \
  tests/test_phase1_*.py \
  tests/test_repaired_model_evaluation.py \
  tests/test_dd_submission_curves.py
run_logged git_diff_check git diff --check
run_logged repaired_manifest python scripts/build_repaired_release_manifest.py
printf 'PASS\n' > "$LOG_DIR/run_all.status"
