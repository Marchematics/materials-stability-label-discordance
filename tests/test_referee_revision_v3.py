import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "referee_revision_v3"
EVAL = OUT / "evaluation"
MODELS = ("alignn_ff", "chgnet", "m3gnet", "mace_mp")


def test_pool_manifests_precede_evaluation_support() -> None:
    candidate = pd.read_parquet(OUT / "candidate_pool_manifest.parquet")
    reference = pd.read_parquet(OUT / "reference_phase_pool_manifest.parquet")
    mphys = pd.read_parquet(EVAL / "mphys_fixed_support.parquet")
    reference_rows = set(reference.loc[reference.phase_kind.eq("D5_batch_phase"), "row_id"])
    assert len(candidate) == 36_801
    assert set(candidate.row_id) == reference_rows
    assert int(candidate.ranking_eligible.sum()) == 36_681
    assert len(mphys) == 36_650
    assert set(mphys.row_id) < set(candidate.row_id)
    forbidden = {"label", "endpoint", "mp_native", "audit_view", "consensus"}
    assert forbidden.isdisjoint(candidate.columns)
    assert forbidden.isdisjoint(reference.columns)


def test_structural_equivalence_classes_are_bounded_and_consistent() -> None:
    classes = pd.read_parquet(OUT / "structural_equivalence_classes.parquet")
    edges = pd.read_parquet(OUT / "structural_equivalence_edges.parquet")
    by_row = classes.set_index("row_id")["equivalence_class_id"]
    assert len(classes) == 36_801
    assert classes.equivalence_class_id.nunique() == 35_740
    assert classes.equivalence_class_size.max() == 6
    assert (edges.row_id_a.map(by_row) == edges.row_id_b.map(by_row)).all()


def test_every_model_excludes_the_full_target_equivalence_class() -> None:
    for model in MODELS:
        audit = pd.read_parquet(OUT / f"loso_exclusion_audit_{model}.parquet")
        assert len(audit) == 36_681
        assert audit.exclusion_verified.all()
        assert audit.all_equivalence_class_members_excluded.all()
        assert audit.decomposition_simplex_excludes_equivalence_class.all()
        assert audit.excluded_rows_in_decomposition_simplex_json.eq("[]").all()
        assert audit.score_status.eq("ok").all()
        assert (audit.excluded_phase_n >= 1).all()
        assert (audit.excluded_phase_n <= 6).all()

    summary = pd.read_csv(OUT / "loso_exclusion_audit_summary.csv")
    primary = summary[summary.setting.eq("primary")]
    assert len(primary) == 4
    assert int(primary.row_n.sum()) == 146_724
    assert primary.simplex_overlap_n.eq(0).all()
    assert primary.row_n.eq(primary.full_exclusion_verified_n).all()


def test_repaired_rankings_do_not_have_a_dominant_top1000_tie() -> None:
    audit = pd.read_csv(EVAL / "ranking_tie_audit_all_models.csv")
    top1000 = audit[audit.K.eq(1000)]
    assert len(top1000) == 4
    assert (top1000.boundary_tie_n == 1).all()
    assert (top1000.strictly_before_boundary_n == 999).all()
    assert (top1000.largest_tie_block_n <= 4).all()


def test_official_labels_equal_t0_coordinate_endpoints() -> None:
    audit = pd.read_csv(EVAL / "official_vs_coordinate_t0_audit.csv")
    assert len(audit) == 10
    assert audit.mismatch_n.sum() == 0
    assert set(audit.support) == {"D2", "D5_compounds"}


def test_baseline_conflict_identities_are_reproduced() -> None:
    decomposition = pd.read_csv(EVAL / "common_pool_decomposition_threshold_scan.csv")
    row = decomposition[
        decomposition.support.eq("D2")
        & decomposition.threshold_meV_per_atom.eq(0)
    ].iloc[0]
    assert row.n_all_native_complete == 36_802
    assert row.n_reconstructable == 36_770
    assert row.all_native_conflict_n == 5_666
    assert row.reconstructable_native_conflict_n == 5_661
    assert row.unreconstructable_native_conflict_n == 5
    assert row.phase_pool_sensitive_n == 3_659
    assert row.persistent_conflict_n == 2_002
    assert row.hidden_common_pool_conflict_n == 2_895
    assert row.common_pool_conflict_n == 4_897
    assert row.all_native_identity_verified
    assert row.reconstructable_native_identity_verified
    assert row.common_pool_identity_verified


def test_native_threshold_scan_retains_full_d2_denominator() -> None:
    scan = pd.read_csv(EVAL / "endpoint_threshold_scan.csv")
    baseline = scan[
        scan.support.eq("D2_native_full") & scan.threshold_meV_per_atom.eq(0)
    ]
    assert set(baseline.n) == {36_802}
    assert set(baseline.switch_n) == {3_862, 4_244, 5_666}


def test_bootstrap_uncertainties_are_separated_and_complete() -> None:
    metadata = json.loads((OUT / "bootstrap" / "bootstrap_metadata.json").read_text())
    assert metadata["replicates"] == 1000
    assert "model energy prediction uncertainty" in metadata["not_quantified"]
    winner = pd.read_csv(OUT / "bootstrap" / "model_winner_frequencies_cluster_bootstrap.csv")
    assert set(winner.bootstrap_replicates) == {1000}
    conflict_metadata = json.loads(
        (OUT / "bootstrap_conflicts" / "bootstrap_conflict_metadata.json").read_text()
    )
    assert conflict_metadata["replicates"] == 1000


def test_budget_sensitivity_audit_covers_predeclared_k_values() -> None:
    audit = pd.read_csv(EVAL / "budget_sensitivity_audit.csv")
    assert set(audit.K) == {100, 300, 500, 1000, 5000}
    assert set(audit.threshold_meV_per_atom) == {0, 10, 25, 50}
    expected_rows = 5 * 4 * 5 * 4
    assert len(audit) == expected_rows
    assert (audit.boundary_tie_n >= 1).all()
    assert audit.point_stable_hits.notna().all()


def test_common_pool_headers_distinguish_all_and_reconstructable_conflicts() -> None:
    table = pd.read_csv(EVAL / "common_pool_decomposition_threshold_scan.csv")
    required = {
        "all_native_conflict_n",
        "reconstructable_native_conflict_n",
        "unreconstructable_native_conflict_n",
        "phase_pool_sensitive_n",
        "persistent_conflict_n",
        "hidden_common_pool_conflict_n",
        "common_pool_conflict_n",
    }
    assert required.issubset(table.columns)
    assert "native_conflict_n" not in table.columns


def test_matching_sensitivity_reproduces_default_and_bounds_equivalence_classes() -> None:
    sensitivity = OUT / "matching_sensitivity"
    d1 = pd.read_parquet(sensitivity / "d1_pair_survival_by_tolerance.parquet")
    d2 = pd.read_parquet(sensitivity / "d2_pair_survival_by_tolerance.parquet")
    equivalence = pd.read_csv(sensitivity / "equivalence_class_sensitivity.csv").set_index(
        "tolerance"
    )
    assert len(d1) == 43_139
    assert len(d2) == 36_802
    assert int(d1.matched_default.sum()) == 43_139
    assert int(d2.d2_retained_default.sum()) == 36_802
    assert int(d1.matched_tight.sum()) == 42_799
    assert int(d2.d2_retained_tight.sum()) == 35_877
    assert int(d1.matched_loose.sum()) == 43_139
    assert int(d2.d2_retained_loose.sum()) == 36_802
    assert equivalence.loc["tight", "equivalence_class_n"] >= equivalence.loc[
        "default", "equivalence_class_n"
    ] >= equivalence.loc["loose", "equivalence_class_n"]
    assert set(equivalence.largest_class_n) == {6}
    assert (equivalence.failed_pair_comparisons == 0).all()


def test_claim_to_output_map_is_unique_and_resolvable() -> None:
    mapping = pd.read_csv(OUT / "claim_to_output_map.csv")
    assert mapping.claim_id.is_unique
    assert mapping.lock_status.eq("locked_to_unique_machine_readable_source").all()
    assert {
        "A1_MPHYS_SUPPORT",
        "A2_NATIVE_SWITCH_T0_MINIMUM",
        "A2_NATIVE_SWITCH_T0_MAXIMUM",
        "A2_NATIVE_SWITCH_T50_MINIMUM",
        "A2_NATIVE_SWITCH_T50_MAXIMUM",
        "A3_ROBUST_CONFLICT_COUNT",
        "A4_GLOBAL_MACE_WINNER_MIN_FREQUENCY",
        "A5_TOP1000_POINT_WINNER_SET",
        "A6_MP_SELECTION_REGRET_MEDIAN_MINIMUM",
        "A6_MP_SELECTION_REGRET_MEDIAN_MAXIMUM",
        "B1_MATERIALS_BINARY_DISCORDANCE_RATE",
        "B7_MATERIALS_OXYGEN_DISCORDANCE_RATE",
        "R7_MPHYS_RETAINED_N",
        "R8_MPHYS_EXCLUDED_N",
    }.issubset(set(mapping.claim_id))
    for source in mapping.source_file.unique():
        assert (ROOT / source).is_file(), source


def test_matching_sensitivity_recomputes_top1000_without_boundary_ties() -> None:
    sensitivity = OUT / "matching_sensitivity"
    summary = pd.read_csv(sensitivity / "matching_sensitivity_summary.csv")
    decisions = pd.read_csv(sensitivity / "matching_sensitivity_top1000_decisions.csv")
    assert len(decisions) == 15
    assert set(decisions.matching_tolerance) == {"tight", "default", "loose"}
    assert (decisions.maximum_boundary_tie_n_across_models == 1).all()
    default = summary[summary.matching_tolerance.eq("default")].iloc[0]
    assert bool(default.default_ranking_reproduction_verified)
    assert default.default_ranking_max_abs_difference_vs_primary == 0
    assert dict(zip(summary.matching_tolerance, summary.mphys_tolerance_specific_n)) == {
        "tight": 35_745,
        "default": 36_650,
        "loose": 36_650,
    }


def test_source_native_discovery_curves_are_tie_aware_and_match_topk_audit() -> None:
    curves = pd.read_parquet(
        OUT / "figure_sources" / "fig1_tie_aware_source_native_discovery_curves.parquet"
    )
    assert len(curves) == 4 * 3 * 10_000
    assert set(curves.model_name) == {"ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP"}
    assert set(curves.coordinate_endpoint) == {
        "official__mp_source_coordinate",
        "official__alexmp20_source_coordinate",
        "official__alex_pbe_source_coordinate",
    }
    assert set(curves.groupby(["model_name", "coordinate_endpoint"]).K.max()) == {10_000}
    assert curves.boundary_tie_n.max() <= 4

    endpoint_map = {
        "official__mp_source_coordinate": "mp_source_coordinate",
        "official__alexmp20_source_coordinate": "alexmp20_source_coordinate",
        "official__alex_pbe_source_coordinate": "alex_pbe_source_coordinate",
    }
    at_1000 = curves[curves.K.eq(1000)].copy()
    at_1000["coordinate_endpoint"] = at_1000.coordinate_endpoint.map(endpoint_map)
    audited = pd.read_csv(EVAL / "tie_aware_topk_physical_endpoints.csv")
    audited = audited[
        audited.threshold_meV_per_atom.eq(0)
        & audited.K.eq(1000)
        & audited.coordinate_endpoint.isin(endpoint_map.values())
    ]
    merged = at_1000.merge(
        audited[["model_name", "coordinate_endpoint", "expected_stable_hits", "positive_n"]],
        on=["model_name", "coordinate_endpoint"],
        suffixes=("_curve", "_audit"),
        validate="one_to_one",
    )
    assert len(merged) == 12
    assert (
        merged.expected_stable_hits_curve - merged.expected_stable_hits_audit
    ).abs().max() < 1e-10
    assert (merged.positive_n_curve == merged.positive_n_audit).all()


def test_materials_chemistry_figure_source_is_complete_and_descriptive() -> None:
    strata = pd.read_csv(OUT / "figure_sources" / "fig3_materials_chemistry_strata.csv")
    assert set(strata.stratum) == {
        "Unary", "Binary", "Ternary", "Quaternary+", "Transition metal",
        "No transition metal", "Lanthanide", "No lanthanide", "Oxygen",
        "No oxygen", "Halogen", "No halogen",
    }
    assert int(strata.loc[strata.stratum.eq("Binary"), "row_n"].iloc[0]) == 7_259
    assert abs(
        float(strata.loc[strata.stratum.eq("Oxygen"), "discordance_rate"].iloc[0])
        - 928 / 9_308
    ) < 1e-12


def test_mphys_retained_excluded_audit_preserves_the_declared_support_flow() -> None:
    audit_dir = OUT / "mphys_support_exclusion_audit"
    metadata = json.loads((audit_dir / "mphys_retained_excluded_metadata.json").read_text())
    summary = pd.read_csv(audit_dir / "mphys_retained_excluded_summary.csv")
    systems = pd.read_csv(audit_dir / "mphys_retained_excluded_chemical_system_coverage.csv")
    assert metadata["candidate_compound_n"] == 36_681
    assert metadata["mphys_retained_n"] == 36_650
    assert metadata["candidate_excluded_n"] == 31
    assert set(summary.group) == {"Mphys retained", "candidate excluded"}
    assert summary.groupby("group").n_group.first().to_dict() == {
        "Mphys retained": 36_650,
        "candidate excluded": 31,
    }
    assert int(systems.row_n.sum()) == 36_681
    mp_matched_excluded = summary[
        summary.feature.eq("MP matched-pool stable fraction")
        & summary.group.eq("candidate excluded")
    ].iloc[0]
    assert mp_matched_excluded.n_evaluable == 0


def test_source_input_card_exposes_continuous_and_formation_energy_fields() -> None:
    card = pd.read_csv(OUT / "source_input_card" / "source_input_card.csv")
    assert list(card.source) == ["Materials Project", "MatterGen alex-mp-20", "official Alexandria-PBE"]
    assert card.analysis_hull_field.tolist() == [
        "source_native_mp_ehull", "source_native_mattergen_ehull", "source_native_alexandria_ehull",
    ]
    assert card.formation_energy_available.tolist() == [True, False, True]
