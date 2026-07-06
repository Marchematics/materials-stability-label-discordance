from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "phase2_v1"


def test_phase2_requirement_audit_records_scope_and_evidence():
    audit_path = OUT / "phase2_requirement_audit.csv"
    assert audit_path.exists()
    audit = pd.read_csv(audit_path)
    required_ids = {
        "1_model_score_inventory",
        "2_model_denominators",
        "3_model_evaluation_label_views",
        "4_label_uncertainty_vs_model_spread",
        "5_rank_inversion_analysis",
        "6_generative_candidate_consequence",
        "7_leaderboard_alpha",
        "8_figures",
        "9_tests_reproducibility",
    }
    assert required_ids == set(audit.requirement_id)
    assert {"status", "evidence", "primary_artifacts", "guardrail"}.issubset(audit.columns)
    gen = audit[audit.requirement_id.eq("6_generative_candidate_consequence")].iloc[0]
    assert "partial_guardrailed" in gen.status
    assert "formula-only overlap is not label assignment" in gen.guardrail
    assert "homogeneous DFT" in " ".join(audit.guardrail.astype(str))
    assert (OUT / "phase2_requirement_audit.md").exists()
