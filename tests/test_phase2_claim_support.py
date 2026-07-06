from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "phase2_v1"


def test_phase2_claim_support_matrix_links_claims_to_guardrailed_evidence():
    path = OUT / "phase2_claim_support_matrix.csv"
    assert path.exists()
    matrix = pd.read_csv(path)
    required = {
        "C1_model_facing_framework",
        "C2_matbench_ecosystem_coverage",
        "C3_label_uncertainty_changes_metrics",
        "C4_rank_interpretation_changes",
        "C5_topk_discovery_consequence",
        "C6_candidate_consequence",
        "C7_source_union_incomplete_guardrail",
    }
    assert required == set(matrix.claim_id)
    assert {
        "claim_text",
        "support_status",
        "primary_evidence",
        "primary_artifacts",
        "manuscript_safe_language",
        "overclaim_to_avoid",
    }.issubset(matrix.columns)
    cand = matrix[matrix.claim_id.eq("C6_candidate_consequence")].iloc[0]
    assert cand.support_status == "partially_supported_guardrailed"
    assert "homogeneous DFT validation" in cand.overclaim_to_avoid
    assert "formula-only" in cand.manuscript_safe_language
    rank = matrix[matrix.claim_id.eq("C4_rank_interpretation_changes")].iloc[0]
    assert "real-model" in rank.primary_evidence
    assert "definitive best model" in rank.overclaim_to_avoid
    assert "physical-truth" in " ".join(matrix.overclaim_to_avoid.astype(str))
    assert (OUT / "phase2_claim_support_matrix.md").exists()
    payload = json.loads((OUT / "phase2_claim_support_matrix.json").read_text())
    assert len(payload) == len(matrix)


def test_phase2_output_readme_documents_regeneration_and_scope_guardrails():
    readme = (OUT / "README.md").read_text()
    assert "python -m sourceaware.phase2.cli build-all" in readme
    assert "pytest -q" in readme
    assert "not homogeneous dft validation" in readme.lower()
    assert "phase2_claim_support_matrix" in readme
    assert "Formula-only overlaps" in readme
