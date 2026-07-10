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

run_logged phase2_check python -m sourceaware.phase2.cli check --phase1 outputs/phase1_v2 --out outputs/phase2_v1
run_logged benchmark_card python scripts/generate_benchmark_card.py --check
run_logged submission_figures python scripts/build_submission_figures.py --check
run_logged manuscript_claims python scripts/audit_manuscript_claims.py --check
run_logged pytest pytest -q
run_logged git_diff_check git diff --check

python scripts/build_dd_submission_manifest.py --out outputs/dd_submission_v2
printf 'PASS\n' > "$LOG_DIR/run_all.status"
