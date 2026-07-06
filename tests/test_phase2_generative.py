from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "phase2_v1"


def test_phase2_generative_outputs_are_honest_about_scope():
    inv = pd.read_csv(OUT / "generative" / "generated_candidate_inventory.csv")
    assert {"MatterGen", "FlowMM", "DiffCSP", "CDVAE", "CrystalFlow"}.issubset(set(inv.pipeline_name))
    true = inv[inv.pipeline_type.eq("true_generator")]
    assert true.status.str.contains("not_run_missing_official_checkpoint").all()
    screening = inv[inv.status.eq("complete_screening_consequence")]
    assert len(screening) >= 1
    matched = pd.read_parquet(OUT / "generative" / "generated_candidates_matched_to_sourceaware.parquet")
    assert matched.matched_to_sourceaware.sum() >= 4000
    labels = pd.read_parquet(OUT / "generative" / "generated_candidate_labels_by_view.parquet")
    assert {"mp_native", "all_source_native", "consensus", "audit_view"}.issubset(set(labels.label_view))
    consequence = pd.read_csv(OUT / "generative" / "generated_pipeline_consequence_summary.csv")
    required = {"apparent_stable_yield", "all_source_native_stable_yield", "consensus_stable_yield", "audit_view_stable_yield", "source_uncertain_fraction", "near_threshold_fraction", "duplicate_fraction", "unmatched_fraction"}
    assert required.issubset(consequence.columns)
    assert consequence.consensus_stable_yield.notna().any()
    search = pd.read_csv(OUT / "generative" / "candidate_source_search_audit.csv")
    assert {"MatterGen", "FlowMM", "DiffCSP", "CDVAE", "CrystalFlow"}.issubset(set(search.pipeline_name))
