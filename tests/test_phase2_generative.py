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
    mg5k = inv[inv.pipeline_name.eq("MatterGen_pilot_5k_public_safe_formulas")].iloc[0]
    assert int(mg5k.candidate_n) == 5000
    assert int(mg5k.matched_n) == 0
    assert "formula" in mg5k.claim_scope
    screening = inv[inv.status.eq("complete_screening_consequence")]
    assert len(screening) >= 3
    assert {"alignn_ff_screened_sourceaware_top5000", "mace_mp_screened_sourceaware_top5000", "m3gnet_screened_sourceaware_top5000"}.issubset(set(screening.pipeline_name))
    assert "PGCGM_public_safe_generated_pool" in set(inv.pipeline_name)
    pg = inv[inv.pipeline_name.eq("PGCGM_public_safe_generated_pool")].iloc[0]
    assert int(pg.candidate_n) == 3000
    assert int(pg.matched_n) == 0
    matched = pd.read_parquet(OUT / "generative" / "generated_candidates_matched_to_sourceaware.parquet")
    assert len(matched) >= 33002
    assert matched.matched_to_sourceaware.sum() >= 24000
    pg_matched = matched[matched.pipeline_name.eq("PGCGM_public_safe_generated_pool")]
    assert len(pg_matched) == 3000
    assert pg_matched.matched_to_sourceaware.sum() == 0
    mg_matched = matched[matched.pipeline_name.eq("MatterGen_hf_base_smoke_unconditional")]
    assert len(mg_matched) == 2
    assert mg_matched.matched_to_sourceaware.sum() == 0
    mg5k_matched = matched[matched.pipeline_name.eq("MatterGen_pilot_5k_public_safe_formulas")]
    assert len(mg5k_matched) == 5000
    assert mg5k_matched.matched_to_sourceaware.sum() == 0
    assert mg5k_matched.formula_overlap_with_sourceaware.any()
    labels = pd.read_parquet(OUT / "generative" / "generated_candidate_labels_by_view.parquet")
    assert {"mp_native", "all_source_native", "consensus", "audit_view"}.issubset(set(labels.label_view))
    consequence = pd.read_csv(OUT / "generative" / "generated_pipeline_consequence_summary.csv")
    required = {"apparent_stable_yield", "all_source_native_stable_yield", "consensus_stable_yield", "audit_view_stable_yield", "source_uncertain_fraction", "near_threshold_fraction", "duplicate_fraction", "unmatched_fraction"}
    assert required.issubset(consequence.columns)
    assert consequence.consensus_stable_yield.notna().any()
    screened_consequence = consequence[consequence.pipeline_type.eq("screening_pipeline_not_true_generator")]
    assert len(screened_consequence) >= 3
    assert screened_consequence.audit_view_stable_yield.notna().all()
    pg_cons = consequence[consequence.pipeline_name.eq("PGCGM_public_safe_generated_pool")].iloc[0]
    assert float(pg_cons.unmatched_fraction) == 1.0
    assert 0 < float(pg_cons.formula_support_fraction) < 0.1
    mg_cons = consequence[consequence.pipeline_name.eq("MatterGen_hf_base_smoke_unconditional")].iloc[0]
    assert float(mg_cons.unmatched_fraction) == 1.0
    assert float(mg_cons.unsupported_no_formula_overlap_fraction) == 1.0
    mg5k_cons = consequence[consequence.pipeline_name.eq("MatterGen_pilot_5k_public_safe_formulas")].iloc[0]
    assert float(mg5k_cons.unmatched_fraction) == 1.0
    assert 0 < float(mg5k_cons.formula_support_fraction) < 0.1
    support = pd.read_csv(OUT / "generative" / "generated_candidate_formula_support.csv")
    assert {"formula_support_status", "formula_sourceaware_row_count", "formula_sourceaware_mp_examples"}.issubset(support.columns)
    assert "formula_only_overlap_no_label_assignment" in set(support.formula_support_status)
    fig5 = pd.read_csv(OUT / "figure_source_data" / "fig5_generated_consequence.csv")
    assert required.issubset(fig5.columns)
    search = pd.read_csv(OUT / "generative" / "candidate_source_search_audit.csv")
    assert {"MatterGen", "FlowMM", "DiffCSP", "CDVAE", "CrystalFlow"}.issubset(set(search.pipeline_name))
    assert {"public_source_url", "candidate_artifact_status", "exact_sourceaware_mapping_status", "guardrail"}.issubset(search.columns)
    named = search[search.pipeline_name.isin(["MatterGen", "FlowMM", "DiffCSP", "CDVAE", "CrystalFlow"])]
    assert named.public_source_url.notna().all()
    assert named.guardrail.str.contains("not label assignment", regex=False).all()


def test_phase2_generated_candidate_artifact_provenance_is_public_safe():
    prov = pd.read_csv(OUT / "generative" / "generated_candidate_artifact_provenance.csv")
    assert len(prov) >= 8
    required = {
        "pipeline_name",
        "artifact_role",
        "artifact_kind",
        "path_scope",
        "publishable_path",
        "exists",
        "committed_to_public_repo",
        "row_count",
        "structure_count",
        "sha256",
        "label_assignment_status",
        "guardrail",
    }
    assert required.issubset(prov.columns)
    assert "private_local_not_committed" in set(prov.path_scope)
    private = prov[prov.path_scope.eq("private_local_not_committed")]
    assert private.publishable_path.str.contains("<redacted_private_path>", regex=False).all()
    assert not private.committed_to_public_repo.astype(bool).any()
    assert private.guardrail.str.contains("not committed", case=False).any()
    public_mg = prov[prov.publishable_path.str.endswith("mattergen_pilot_5k_public_safe_formulas.csv", na=False)].iloc[0]
    assert int(public_mg.row_count) == 5000
    assert public_mg.label_assignment_status == "formula_only_overlap_no_label_assignment"
    consistency = prov[prov.artifact_kind.eq("count_consistency_audit")].iloc[0]
    assert int(consistency.row_count) == 5000
    assert int(consistency.structure_count) == 5000
    assert consistency.label_assignment_status == "count_consistent_no_label_assignment"
    assert "does not create SourceAware stable/unstable labels" in consistency.guardrail
