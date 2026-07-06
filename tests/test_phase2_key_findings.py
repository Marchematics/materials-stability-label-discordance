from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "phase2_v1"


def test_phase2_key_findings_support_claim_scope_and_guardrails():
    path = OUT / "phase2_key_findings.csv"
    assert path.exists()
    findings = pd.read_csv(path)
    required = {
        "model_matrix_scope",
        "label_uncertainty_dominates_some_model_margins",
        "topk_yield_is_label_view_dependent",
        "rank_interpretation_changes",
        "source_union_incomplete_is_explicit",
        "screened_candidate_claims_reclassify_under_audit_view",
        "generated_candidate_support_is_mostly_unmatched",
    }
    assert required.issubset(set(findings.finding_id))
    assert {"finding", "evidence", "claim_scope", "guardrail"}.issubset(findings.columns)
    dom = findings[findings.finding_id.eq("label_uncertainty_dominates_some_model_margins")].iloc[0]
    assert float(dom.primary_number) > 0
    rank = findings[findings.finding_id.eq("rank_interpretation_changes")].iloc[0]
    assert float(rank.secondary_number) > 0
    cand = findings[findings.finding_id.eq("screened_candidate_claims_reclassify_under_audit_view")].iloc[0]
    assert float(cand.primary_number) > 0
    assert "not homogeneous DFT validation" in " ".join(findings.guardrail.astype(str))
    assert (OUT / "phase2_key_findings.md").exists()
    payload = json.loads((OUT / "phase2_key_findings.json").read_text())
    assert len(payload) == len(findings)
