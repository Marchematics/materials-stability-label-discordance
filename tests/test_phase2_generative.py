from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "phase2_v1"


def test_phase2_generative_outputs_are_honest_about_scope():
    inv = pd.read_csv(OUT / "generative" / "generated_candidate_inventory.csv")
    assert {"MatterGen", "FlowMM", "DiffCSP", "CDVAE", "CrystalFlow"}.issubset(set(inv.pipeline_name))
    true = inv[inv.pipeline_type.eq("true_generator")]
    completed_true = true[true.status.str.startswith("complete", na=False)]
    attempted_only = true[~true.status.str.startswith("complete", na=False)]
    assert len(completed_true) >= 1
    assert attempted_only.status.str.contains("not_run_missing_official_checkpoint").all()
    mg = inv[inv.pipeline_name.eq("MatterGen_hf_base_smoke_unconditional")].iloc[0]
    assert int(mg.candidate_n) == 2
    assert int(mg.matched_n) == 0
    screening = inv[inv.status.eq("complete_screening_consequence")]
    assert len(screening) >= 1
    assert "PGCGM_public_safe_generated_pool" in set(inv.pipeline_name)
    pg = inv[inv.pipeline_name.eq("PGCGM_public_safe_generated_pool")].iloc[0]
    assert int(pg.candidate_n) == 3000
    assert int(pg.matched_n) == 0
    matched = pd.read_parquet(OUT / "generative" / "generated_candidates_matched_to_sourceaware.parquet")
    assert len(matched) >= 8002
    assert matched.matched_to_sourceaware.sum() >= 4000
    pg_matched = matched[matched.pipeline_name.eq("PGCGM_public_safe_generated_pool")]
    assert len(pg_matched) == 3000
    assert pg_matched.matched_to_sourceaware.sum() == 0
    mg_matched = matched[matched.pipeline_name.eq("MatterGen_hf_base_smoke_unconditional")]
    assert len(mg_matched) == 2
    assert mg_matched.matched_to_sourceaware.sum() == 0
    labels = pd.read_parquet(OUT / "generative" / "generated_candidate_labels_by_view.parquet")
    assert {"mp_native", "all_source_native", "consensus", "audit_view"}.issubset(set(labels.label_view))
    consequence = pd.read_csv(OUT / "generative" / "generated_pipeline_consequence_summary.csv")
    required = {"apparent_stable_yield", "all_source_native_stable_yield", "consensus_stable_yield", "audit_view_stable_yield", "source_uncertain_fraction", "near_threshold_fraction", "duplicate_fraction", "unmatched_fraction"}
    assert required.issubset(consequence.columns)
    assert consequence.consensus_stable_yield.notna().any()
    pg_cons = consequence[consequence.pipeline_name.eq("PGCGM_public_safe_generated_pool")].iloc[0]
    assert float(pg_cons.unmatched_fraction) == 1.0
    assert 0 < float(pg_cons.formula_support_fraction) < 0.1
    mg_cons = consequence[consequence.pipeline_name.eq("MatterGen_hf_base_smoke_unconditional")].iloc[0]
    assert float(mg_cons.unmatched_fraction) == 1.0
    assert float(mg_cons.unsupported_no_formula_overlap_fraction) == 1.0
    support = pd.read_csv(OUT / "generative" / "generated_candidate_formula_support.csv")
    assert {"formula_support_status", "formula_sourceaware_row_count", "formula_sourceaware_mp_examples"}.issubset(support.columns)
    assert "formula_only_overlap_no_label_assignment" in set(support.formula_support_status)
    fig5 = pd.read_csv(OUT / "figure_source_data" / "fig5_generated_consequence.csv")
    assert required.issubset(fig5.columns)
    search = pd.read_csv(OUT / "generative" / "candidate_source_search_audit.csv")
    assert {"MatterGen", "FlowMM", "DiffCSP", "CDVAE", "CrystalFlow"}.issubset(set(search.pipeline_name))
