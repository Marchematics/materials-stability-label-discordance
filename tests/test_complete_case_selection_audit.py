from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "evidence_strengthening_v1" / "complete_case_audit"


def test_complete_case_audit_preserves_declared_d2_d5_m1_counts() -> None:
    summary = json.loads((OUT / "complete_case_selection_summary.json").read_text())
    assert summary["D2_three_source_exact_rows"] == 36_802
    assert summary["D5_archived_four_score_rows"] == 36_801
    assert summary["M1_all_view_common_support_rows"] == 31_872
    assert summary["D5_excluded_from_M1_rows"] == 4_929
    assert summary["D5_archived_four_score_rows"] == summary["M1_all_view_common_support_rows"] + summary["D5_excluded_from_M1_rows"]
