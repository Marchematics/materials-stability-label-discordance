#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
python scripts/build_publication_figures.py
pytest -q tests/test_referee_revision_v3.py tests/test_tie_aware_ranking.py
git diff --check
