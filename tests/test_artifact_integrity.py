from pathlib import Path
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MILESTONE = ROOT / "outputs" / "milestones" / "materials_label_discordance_preregistration"
FULL_MILESTONE = ROOT / "outputs" / "milestones" / "materials_label_discordance_full_mp_alex_43984"
ENHANCEMENT = ROOT / "outputs" / "milestones" / "benchmark_reliability_enhancement"
COMMON_HULL = ROOT / "outputs" / "milestones" / "common_hull_mechanism_subset"
BENCHMARK_IMPACT = ROOT / "outputs" / "milestones" / "benchmark_impact_label_source_choice"
MODEL_SENSITIVITY = ROOT / "outputs" / "milestones" / "model_facing_benchmark_sensitivity_check"


def test_no_secret_material_is_committed() -> None:
    texts = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.is_file() and path.stat().st_size < 5_000_000:
            try:
                texts.append(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                continue
    combined = "\n".join(texts)
    credential_like = re.findall(
        r"(?i)(?:api[_-]?key|token|secret|credential)\s*[:=]\s*['\"]?([A-Za-z0-9_-]{16,})",
        combined,
    )
    assert credential_like == []


def test_related_work_positioning_is_context_not_new_experiment() -> None:
    text = (ROOT / "docs" / "RELATED_WORK_POSITIONING.md").read_text(encoding="utf-8")
    bib = (ROOT / "docs" / "bibliography_additions.bib").read_text(encoding="utf-8")

    for required in [
        "JARVIS-Leaderboard",
        "Matbench Discovery",
        "MACE",
        "MP-ALOE",
        "MatterGen",
        "GRACE",
        "Do not claim a new GRACE",
        "Do not claim prospective materials discovery",
    ]:
        assert required in text

    for key in [
        "choudhary2024jarvis_leaderboard",
        "riebesell2025matbench_discovery",
        "batatia2025foundation_mace",
        "deng2025systematic_softening",
        "kuner2025mp_aloe",
        "lysogorskiy2026grace",
        "zou2025thermodynamic_stability",
        "zeni2025mattergen",
    ]:
        assert key in bib

    assert "not a new training-data experiment here" in text
    assert "not evaluated as new experimental rows here" in text


def test_full_mp_alex_43984_denominator_is_completed_and_scoped() -> None:
    summary = pd.read_csv(FULL_MILESTONE / "table_full_mp_alex_denominator_summary.csv").iloc[0]
    assert int(summary["alex_mp_identifier_rows"]) == 43_984
    assert int(summary["mp_records_successfully_queried"]) >= 43_000
    assert int(summary["strict_structure_matches"]) >= 43_000
    assert int(summary["discordant_n"]) == 5_060
    assert 0.10 <= float(summary["discordance_rate"]) <= 0.13
    assert summary["claim_scope"] == "full_43984_MP_identifier_denominator"

    counts = pd.read_csv(FULL_MILESTONE / "table_full_mp_alex_match_status_counts.csv")
    count_map = dict(zip(counts["match_status"], counts["count"]))
    assert int(count_map["strict_structure_match"]) == 43_139
    assert int(count_map["missing_mp_record"]) == 815
    assert int(count_map["structure_mismatch"]) == 30

    manifest = (FULL_MILESTONE / "MANIFEST_SHA256.txt").read_text(encoding="utf-8")
    assert "table_full_mp_alex_structure_matches.csv" in manifest
    assert "mp_records_summary_structures.jsonl" not in manifest


def test_benchmark_reliability_enhancement_keeps_completed_and_protocol_rows_separate() -> None:
    atlas = pd.read_csv(ENHANCEMENT / "table_selection_conditioned_discordance_atlas.csv")
    full = atlas[atlas["selection_condition"].eq("full_denominator")].iloc[0]
    assert int(full["n"]) == 43_139
    assert int(full["discordant_n"]) == 5_060
    assert 0.10 <= float(full["discordance_rate"]) <= 0.13

    mp_stable = atlas[atlas["selection_condition"].eq("MP_exact_stable")].iloc[0]
    assert int(mp_stable["n"]) == 16_872
    assert 0.20 <= float(mp_stable["discordance_rate"]) <= 0.23

    threshold = pd.read_csv(ENHANCEMENT / "table_full_denominator_uncertainty_threshold_sweep.csv")
    five = threshold[threshold["threshold_meV_atom"].eq(5)].iloc[0]
    assert int(five["discordant_captured_n"]) == 5_060
    assert int(five["outside_discordant_n"]) == 0
    assert 0.49 <= float(five["flagged_fraction"]) <= 0.50

    common_hull = pd.read_csv(ENHANCEMENT / "table_common_hull_mechanism_protocol.csv")
    assert set(common_hull["status"]).issubset(
        {"gated_protocol_not_completed", "partial_reporting_burden_only"}
    )
    assert not common_hull["completed_claim_allowed"].astype(bool).any()

    benchmark = pd.read_csv(ENHANCEMENT / "table_benchmark_impact_protocol.csv")
    assert set(benchmark["status"]).issubset(
        {"gated_protocol_not_completed", "protocol_defined_not_completed"}
    )
    assert benchmark["claim_boundary"].str.contains("no full-denominator model leaderboard claim").any()

    card = pd.read_csv(ENHANCEMENT / "table_source_aware_benchmark_card.csv")
    assert "source_discordance_burden" in set(card["card_field"])
    assert "conflict_excluded_metric" in set(card["card_field"])
    conflict = card[card["card_field"].eq("conflict_excluded_metric")].iloc[0]
    assert conflict["status"] == "protocol_only"


def test_common_composition_hull_proxy_is_coverage_boundary_not_mechanism_claim() -> None:
    sample = pd.read_csv(COMMON_HULL / "table_common_hull_mechanism_sample.csv")
    assert len(sample) == 1_500
    assert int(sample["native_discordant"].sum()) == 1_000
    assert int((~sample["native_discordant"].astype(bool)).sum()) == 500

    coverage = pd.read_csv(COMMON_HULL / "table_common_hull_coverage_audit.csv")
    cov = dict(zip(coverage["sample_role"], coverage["common_available_fraction"]))
    assert cov["discordant_mechanism_sample"] < 0.05
    assert cov["concordant_control_sample"] < 0.05

    mechanism = pd.read_csv(COMMON_HULL / "table_common_hull_mechanism_decomposition.csv")
    assert "common_hull_unavailable" in set(mechanism["mechanism_class"])
    unavailable = mechanism[mechanism["mechanism_class"].eq("common_hull_unavailable")]
    assert int(unavailable["n"].sum()) >= 1_400

    closeout = (COMMON_HULL / "COMMON_HULL_MECHANISM_SUBSET_CLOSEOUT.md").read_text(
        encoding="utf-8"
    )
    assert "coverage-boundary result" in closeout
    assert "not a positive mechanism-decomposition result" in closeout
    assert "common-composition competitor-hull proxy" in closeout


def test_benchmark_impact_label_source_choice_is_completed_but_not_model_leaderboard() -> None:
    confusion = pd.read_csv(BENCHMARK_IMPACT / "table_label_confusion_matrix_full_denominator.csv")
    cells = dict(zip(confusion["label_cell"], confusion["n"]))
    assert int(cells["both_stable"]) == 13_244
    assert int(cells["mp_stable_alex_unstable"]) == 3_628
    assert int(cells["mp_unstable_alex_stable"]) == 1_432
    assert int(cells["both_unstable"]) == 24_835
    assert sum(int(v) for v in cells.values()) == 43_139

    transfer = pd.read_csv(BENCHMARK_IMPACT / "table_perfect_source_labeler_cross_evaluation.csv")
    mp_cross = transfer[
        transfer["predictor"].eq("perfect_MP_source_labeler")
        & transfer["evaluation_label_source"].eq("Alexandria_source_native_truth")
    ].iloc[0]
    assert 0.83 <= float(mp_cross["f1"]) <= 0.85
    assert float(mp_cross["delta_from_source_native_f1"]) < -0.15

    interpretation = pd.read_csv(BENCHMARK_IMPACT / "table_metric_shift_interpretation.csv")
    burden = interpretation[interpretation["impact_statement"].eq("binary_label_disagreement_burden")].iloc[0]
    assert 0.11 <= float(burden["value"]) <= 0.12
    mp_loss = interpretation[
        interpretation["impact_statement"].eq("MP_stable_candidates_rejected_by_Alexandria")
    ].iloc[0]
    assert 0.21 <= float(mp_loss["value"]) <= 0.22

    closeout = (BENCHMARK_IMPACT / "BENCHMARK_IMPACT_LABEL_SOURCE_CHOICE_CLOSEOUT.md").read_text(
        encoding="utf-8"
    )
    assert "does not claim a full-denominator ML model leaderboard" in closeout
    assert "source-label transfer limits" in closeout


def test_model_facing_sensitivity_check_has_real_model_large_subset_and_boundaries() -> None:
    manifest = pd.read_csv(MODEL_SENSITIVITY / "table_chgnet_scored_subset_manifest.csv").iloc[0]
    assert manifest["model"] == "CHGNet"
    assert int(manifest["n_scored"]) == 5_000
    assert manifest["device"] in {"cuda", "cpu"}
    assert manifest["claim_scope"] == "model_facing_sensitivity_check_not_leaderboard"

    scores = pd.read_csv(MODEL_SENSITIVITY / "candidate_scores_chgnet_5000.csv")
    assert len(scores) == 5_000
    assert scores["score"].notna().all()
    assert set(["mp_stable", "alex_stable", "source_agreement"]).issubset(scores.columns)

    pk_shift = pd.read_csv(MODEL_SENSITIVITY / "table_precision_at_k_metric_shift.csv")
    assert set([100, 300, 500, 1000, 2000]).issubset(set(pk_shift["K"]))
    k300 = pk_shift[pk_shift["K"].eq(300)].iloc[0]
    assert abs(float(k300["metric_shift_mp_minus_alex"])) >= 0.02
    assert (pk_shift["claim_scope"] == "model_facing_sensitivity_check_not_leaderboard").all()

    sanity = pd.read_csv(MODEL_SENSITIVITY / "table_chgnet_score_direction_sanity.csv")
    assert {
        "raw_CHGNet_formation_energy_proxy_as_higher_stability_score",
        "negative_CHGNet_formation_energy_proxy_as_higher_stability_score",
        "random_ranking_baseline",
    }.issubset(set(sanity["score_variant"]))
    assert {"mp_stable", "alex_stable"}.issubset(set(sanity["label_source"]))

    decomp = pd.read_csv(MODEL_SENSITIVITY / "table_topk_discordance_decomposition.csv")
    k300_decomp = decomp[decomp["K"].eq(300)].iloc[0]
    assert int(k300_decomp["mp_stable_n"]) == 100
    assert int(k300_decomp["alex_stable_n"]) == 87
    assert int(k300_decomp["mp_only_stable_n"]) == 23
    assert int(k300_decomp["alex_only_stable_n"]) == 10

    bootstrap = pd.read_csv(MODEL_SENSITIVITY / "table_precision_shift_bootstrap.csv")
    k300_boot = bootstrap[bootstrap["K"].eq(300)].iloc[0]
    assert float(k300_boot["bootstrap_ci_low"]) <= float(k300["metric_shift_mp_minus_alex"])
    assert float(k300_boot["bootstrap_ci_high"]) >= float(k300["metric_shift_mp_minus_alex"])

    represent = pd.read_csv(MODEL_SENSITIVITY / "table_chgnet_sample_representativeness.csv")
    full = represent[represent["comparison"].eq("full_denominator") & represent["stratum"].eq("overall")].iloc[0]
    sample = represent[represent["comparison"].eq("chgnet_5000_sample") & represent["stratum"].eq("overall")].iloc[0]
    assert int(full["n"]) == 43_139
    assert int(sample["n"]) == 5_000
    assert abs(float(full["discordance_rate"]) - float(sample["discordance_rate"])) < 0.01

    metrics = pd.read_csv(MODEL_SENSITIVITY / "table_model_metric_source_sensitivity.csv")
    assert {"mp_stable", "alex_stable"}.issubset(set(metrics["label_source"]))
    assert (metrics["claim_scope"] == "model_facing_sensitivity_check_not_leaderboard").all()

    closeout = (MODEL_SENSITIVITY / "MODEL_FACING_BENCHMARK_SENSITIVITY_CHECK.md").read_text(
        encoding="utf-8"
    )
    assert "not a leaderboard" in closeout
    assert "one real model ranking" in closeout


def test_minimal_discordance_probe_passes_launch_signal() -> None:
    probe = pd.read_csv(MILESTONE / "table_minimal_discordance_probe.csv")
    row = probe.iloc[0]
    assert int(row["matched_n"]) >= 200
    assert float(row["discordance_rate"]) >= 0.40
    assert str(row["launch_gate_discordance_ge_0_40"]).lower() == "true"


def test_primary_downstream_endpoint_is_not_overclaimed() -> None:
    summary = pd.read_csv(MILESTONE / "table_downstream_ranking_flip_summary.csv")
    primary = summary[summary["endpoint"].eq("primary_frontier_model_ranking")].iloc[0]
    assert primary["status"] == "run"
    assert primary["go_no_go"] == "NO_GO_primary_no_material_F1_ranking_flip"
    assert str(primary["top_model_flip"]).lower() == "false"


def test_route_b_is_one_shot_and_keeps_endpoint_frozen() -> None:
    text = (MILESTONE / "ROUTE_B_ONE_SHOT_RESCUE_PROTOCOL.md").read_text(encoding="utf-8")
    assert "Run this rescue at most once" in text
    assert "stable-class F1" in text
    assert "n_common >= 200" in text
    assert "discordance >= 0.40" in text
    assert "permanently close the NMI discordance" in text

    gate = pd.read_csv(MILESTONE / "table_route_b_rescue_gate.csv")
    assert "one_shot_only" in set(gate["gate"])
    assert "reopen_rule" in set(gate["gate"])
    reopen = gate[gate["gate"].eq("reopen_rule")].iloc[0]
    assert "discordance >= 0.40" in reopen["requirement"]
    assert "stable-F1 ranking flip" in reopen["requirement"]


def test_route_b_readiness_blocks_endpoint_without_alignn_ff() -> None:
    status = pd.read_csv(MILESTONE / "table_route_b_readiness_status.csv")
    alignn = status[status["component"].eq("ALIGNN-FF")].iloc[0]
    assert alignn["status"] == "fail"
    assert "BadZipFile" in alignn["details"]

    endpoint = status[status["component"].eq("Route B primary endpoint")].iloc[0]
    assert endpoint["status"] == "blocked"
    assert "ALIGNN" in endpoint["details"]

    local = status[status["component"].eq("ALIGNN-FF local explicit-path scorer")].iloc[0]
    assert local["status"] == "partial_pass_public_source_pending"
    assert "smoke tests" in local["details"]


def test_alignn_ff_readiness_attempt_records_partial_wbm_predictions() -> None:
    attempts = pd.read_csv(MILESTONE / "table_alignn_ff_readiness_attempts.csv")

    official = attempts[attempts["attempt_type"].eq("official_scorer_download")]
    assert not official.empty
    assert set(official["status"]) == {"blocked_403"}

    pinned = attempts[attempts["attempt_type"].eq("pinned_downloader_repair")]
    assert not pinned.empty
    assert set(pinned["status"]) == {"blocked_403"}

    frozen = attempts[attempts["attempt_id"].eq("alignn_ff_wbm_predictions")].iloc[0]
    assert frozen["status"] == "available"
    assert frozen["sha256_or_response"] == (
        "dc75be97f3bce3ce724680065abf11a19bdc6a3928fdd77ccb42d3f62a02e593"
    )
    assert frozen["route_b_implication"] == (
        "can_support_WBM_intersection_diagnostics_but_does_not_score_full_MP_Alex_snapshot"
    )

    closeout = (MILESTONE / "ALIGNN_FF_READINESS_FIX_ATTEMPT.md").read_text(
        encoding="utf-8"
    )
    assert "not as a" in closeout and "complete fix" in closeout
    assert "No Route B endpoint" in closeout


def test_alignn_ff_pinned_downloader_repair_does_not_clear_gate() -> None:
    downloads = pd.read_csv(MILESTONE / "table_alignn_ff_download_integrity.csv")
    assert not downloads.empty
    remote = downloads[downloads["url_pattern"].ne("local_user_provided_archive")]
    assert set(remote["status_code"].astype(str)) == {"403"}
    assert set(remote["zip_ok"].astype(str).str.lower()) == {"false"}
    assert set(remote["decision"]) == {"blocked_not_model_zip"}
    local = downloads[downloads["url_pattern"].eq("local_user_provided_archive")].iloc[0]
    assert str(local["zip_ok"]).lower() == "true"
    assert local["sha256"] == "ccc5c71e44e0213f8f5261a5e1df43df03129a4ec661a31c7a880cbf48b4e7b5"

    smoke = pd.read_csv(MILESTONE / "table_alignn_ff_smoke_tests.csv")
    zip_row = smoke[smoke["smoke_test"].eq("zip_integrity")].iloc[0]
    assert zip_row["status"] == "fail"
    si = smoke[smoke["smoke_test"].eq("si_unrelaxed_energy_cpu")].iloc[0]
    assert si["status"] == "pass"
    matched = smoke[smoke["smoke_test"].eq("matched_structure_single_cpu")].iloc[0]
    assert matched["status"] == "pass"
    blocked = smoke[smoke["status"].eq("blocked")]
    assert len(blocked) >= 3

    repair = (MILESTONE / "ALIGNN_FF_PINNED_DOWNLOADER_REPAIR.md").read_text(
        encoding="utf-8"
    )
    assert "issue #194" in repair
    assert "local technical scorer smoke gate" in repair


def test_route_c_is_separate_protocol_not_route_b_modification() -> None:
    protocol = (MILESTONE / "ROUTE_C_ALTERNATIVE_FRONTIER_PANEL_PROTOCOL.md").read_text(
        encoding="utf-8"
    )
    assert "Route B remains unconsumed and blocked" in protocol
    assert "Route C is not a continuation of Route B" in protocol
    assert "CHGNet" in protocol
    assert "MACE-MP" in protocol
    assert "SevenNet / MatterSim / Orb / MatGL / M3GNet" in protocol
    assert "stable-class F1" in protocol

    panel = pd.read_csv(MILESTONE / "table_route_c_frontier_panel_protocol.csv")
    assert {"CHGNet", "MACE-MP"}.issubset(set(panel["model"]))
    alignn = panel[panel["model"].eq("ALIGNN-FF")].iloc[0]
    assert alignn["route_c_role"] == "excluded_from_route_c_due_to_readiness_block"

    gates = pd.read_csv(MILESTONE / "table_route_c_go_no_go_gate.csv")
    independence = gates[gates["gate"].eq("route_c_independence")].iloc[0]
    assert independence["current_status"] == "pass_protocol_frozen"
    ranking = gates[gates["gate"].eq("ranking_flip_gate")].iloc[0]
    assert "abs F1 delta >= 0.05" in ranking["requirement"]


def test_route_c_existing_probe_completed_but_not_full_primary() -> None:
    scores = pd.read_csv(MILESTONE / "table_route_c_existing_probe_model_scores.csv")
    assert {"CHGNet", "MACE-MP", "M3GNet"}.issubset(set(scores["model"]))
    assert scores.groupby("model")["material_id"].nunique().min() == 270

    metrics = pd.read_csv(MILESTONE / "table_route_c_existing_probe_ranking_metrics.csv")
    assert set(metrics["label_source"]) == {"WBM", "alex-mp"}
    assert metrics["n_common"].min() == 270

    summary = pd.read_csv(MILESTONE / "table_route_c_existing_probe_flip_summary.csv").iloc[0]
    assert summary["status"] == "run_existing_probe_not_full_mp_alex_route_c"
    assert str(summary["top_model_flip"]).lower() == "false"
    assert str(summary["ordering_flip"]).lower() == "false"
    assert summary["go_no_go"] == "NO_GO_existing_probe_no_material_F1_ranking_flip"
    assert "not full MP-vs-Alex Route C primary" in summary["claim_scope"]


def test_route_b_alignn_ff_provenance_blocks_primary_claim_until_public_source() -> None:
    checklist = pd.read_csv(MILESTONE / "table_route_b_alignn_ff_provenance_checklist.csv")
    archive = checklist[checklist["check_item"].eq("archive_sha256")].iloc[0]
    assert archive["value"] == "ccc5c71e44e0213f8f5261a5e1df43df03129a4ec661a31c7a880cbf48b4e7b5"
    tech = checklist[checklist["check_item"].eq("si_smoke")].iloc[0]
    assert tech["status"] == "pass"

    decision = pd.read_csv(MILESTONE / "table_route_b_alignn_ff_eligibility_decision.csv")
    registry = decision[decision["gate"].eq("public_registry_gate")].iloc[0]
    assert registry["status"] == "pass"
    clean = decision[decision["gate"].eq("clean_download_hash_match")].iloc[0]
    assert clean["status"] == "pending_blocked_403"
    primary = decision[decision["gate"].eq("route_b_primary_evidence_gate")].iloc[0]
    assert primary["status"] == "pending_hash_match"
    assert "do not run one-shot Route B primary claim yet" in primary["decision"]

    note = (MILESTONE / "ROUTE_B_ALIGNN_FF_PROVENANCE_QUALIFICATION.md").read_text(
        encoding="utf-8"
    )
    assert "public registry entry exists" in note
    assert "PENDING_HASH_MATCH" in note


def test_route_b_public_provenance_unlock_requires_clean_hash_match() -> None:
    unlock = pd.read_csv(MILESTONE / "table_route_b_alignn_ff_public_provenance_unlock.csv")
    registry = unlock[unlock["gate"].eq("public_registry")].iloc[0]
    assert registry["status"] == "pass"
    clean = unlock[unlock["gate"].eq("clean_download_hash_match")].iloc[0]
    assert clean["status"] == "pending_blocked_403"
    primary = unlock[unlock["gate"].eq("route_b_primary_evidence_gate")].iloc[0]
    assert primary["status"] == "pending_hash_match"

    text = (MILESTONE / "ROUTE_B_ALIGNN_FF_PUBLIC_PROVENANCE_UNLOCK.md").read_text(
        encoding="utf-8"
    )
    assert "public registry gate: PASS" in text
    assert "clean download hash match: PENDING" in text
    assert "Route B one-shot outcome: unconsumed" in text


def test_route_b_runner_records_data_access_gate_without_credentials() -> None:
    runner = ROOT / "scripts" / "run_route_b_full_snapshot_rescue.py"
    assert runner.exists()
    text = runner.read_text(encoding="utf-8")
    assert "MP_API_KEY environment variable is required" in text
    assert "credentials are not read from files" in text

    failure = pd.read_csv(MILESTONE / "table_route_b_full_snapshot_data_access_failure.csv")
    row = failure.iloc[0]
    assert row["stage"] == "mp_api_fetch"
    assert str(row["status"]).startswith("failed")
    assert row["error_type"] == "RuntimeError"

    closeout = (MILESTONE / "ROUTE_B_FULL_SNAPSHOT_RESCUE_CLOSEOUT.md").read_text(
        encoding="utf-8"
    )
    assert (
        "blocked at MP API data-access gate" in closeout
        or "Status: completed diagnostic" in closeout
    )


def test_route_b_full_snapshot_diagnostic_keeps_nmi_line_closed() -> None:
    summary = pd.read_csv(MILESTONE / "table_route_b_full_snapshot_summary.csv").iloc[0]
    assert int(summary["n_common"]) >= 200
    assert float(summary["discordance_rate"]) < 0.40
    assert str(summary["top_model_flip"]).lower() == "false"
    assert str(summary["ordering_flip"]).lower() == "false"
    assert summary["go_no_go"] == "NO_GO_keep_NMI_line_closed"


def test_third_source_attempt_is_undercovered_not_positive_triangulation() -> None:
    triangle = pd.read_csv(MILESTONE / "table_third_source_triangle_summary.csv")
    mp_alex = triangle[triangle["comparison"].eq("MP_vs_Alex")].iloc[0]
    assert int(mp_alex["n_common"]) == 287
    assert float(mp_alex["discordance_rate"]) < 0.20
    assert mp_alex["claim_scope"] == "completed_pairwise_baseline"

    for comparison in ["MP_vs_OQMD", "Alex_vs_OQMD"]:
        row = triangle[triangle["comparison"].eq(comparison)].iloc[0]
        assert int(row["n_common"]) < 200
        assert row["claim_scope"] == "blocked_or_undercovered_third_source"

    closeout = (MILESTONE / "THIRD_SOURCE_AND_DISCORDANCE_DECOMPOSITION_CLOSEOUT.md").read_text(
        encoding="utf-8"
    )
    assert "not a completed third-source measurement" in closeout


def test_discordance_decomposition_localizes_to_near_hull_boundary() -> None:
    near = pd.read_csv(MILESTONE / "table_discordance_near_hull_decomposition.csv")
    either = near[near["band"].eq("either_near_hull_25meV")].iloc[0]
    neither = near[near["band"].eq("neither_near_hull_25meV")].iloc[0]
    assert int(either["discordant_n"]) > 0
    assert float(either["discordance_rate"]) > float(neither["discordance_rate"])
    assert int(neither["discordant_n"]) == 0

    families = pd.read_csv(MILESTONE / "table_discordance_element_family.csv")
    assert {"transition_metal", "alkali", "chalcogen"}.issubset(set(families["element_family"]))


def test_wbm_alex_high_discordance_is_case_analysis_not_baseline() -> None:
    cases = pd.read_csv(MILESTONE / "table_wbm_alex_case_comparison.csv")
    wbm = cases[cases["case"].eq("WBM_vs_alex_existing_probe")].iloc[0]
    route_b = cases[cases["case"].eq("MP_vs_alex_route_b_full_snapshot")].iloc[0]
    assert float(wbm["discordance_rate"]) > float(route_b["discordance_rate"])
    assert wbm["role"] == "case_analysis_high_discordance_source_selection_specific"
    assert route_b["role"] == "full_snapshot_pairwise_baseline"


def test_fig4c_selection_conditioned_mp_alex_bar_is_completed_and_scoped() -> None:
    fig4c = pd.read_csv(MILESTONE / "table_fig4c_selection_conditioned_mp_alex.csv")
    full = fig4c[fig4c["selection_rule"].eq("full_MP_Alex_strict_denominator")].iloc[0]
    selected = fig4c[fig4c["selection_rule"].eq("MP_native_exact_stable_release_ehull_le_0")].iloc[0]
    near = fig4c[fig4c["selection_rule"].eq("MP_native_near_hull_release_ehull_le_25meV")].iloc[0]

    assert int(full["n_selected"]) == 287
    assert int(selected["n_selected"]) == 124
    assert int(selected["mp_selected_but_alex_unstable_n"]) == 21
    assert float(selected["discordance_rate"]) > float(full["discordance_rate"])
    assert float(selected["discordance_rate"]) < 0.25
    assert near["paper_role"] == "selection_boundary_sensitivity"

    bars = pd.read_csv(MILESTONE / "table_fig4_reconciliation_bars.csv")
    assert {"a", "b", "c"}.issubset(set(bars["fig4_panel"]))
    panel_c = bars[bars["fig4_panel"].eq("c")].iloc[0]
    assert panel_c["bar"] == "MP_native_exact_stable_release_conditioned"

    scs = pd.read_csv(MILESTONE / "table_fig4c_scs_portability_check.csv")
    assert int((scs["released"].astype(int) > 0).sum()) == 0
    assert set(scs["claim_scope"]) == {"strict_SCS_portability_check_not_fig4c_bar"}

    closeout = (MILESTONE / "FIG4C_SELECTION_CONDITIONED_MP_ALEX_CLOSEOUT.md").read_text(
        encoding="utf-8"
    )
    assert "not a new PARC guarantee" in closeout
    assert "`0` non-empty seed rows" in closeout


def test_denominator_construction_audit_explains_287_denominator() -> None:
    audit = pd.read_csv(MILESTONE / "table_denominator_construction_audit.csv")
    counts = dict(zip(audit["step"], audit["count"], strict=True))
    assert int(counts["Alexandria v20 entries"]) == 675204
    assert int(counts["Alexandria entries with MP identifiers"]) == 43984
    assert int(counts["Frozen Route B MP-ID candidates attempted"]) == 300
    assert int(counts["MP records successfully queried"]) == 287
    assert int(counts["StructureMatcher strict matches"]) == 287
    assert int(counts["MP/Alex labels available"]) == 287
    assert int(counts["ALIGNN-FF scores available"]) == 287
    assert int(counts["CHGNet scores available"]) == 287
    assert int(counts["MACE-MP scores available"]) == 287
    assert int(counts["OQMD exact matches"]) == 4


def test_representativeness_tables_are_present_and_scoped() -> None:
    stable = pd.read_csv(MILESTONE / "table_representativeness_stable_fraction.csv")
    pops = set(stable["population"])
    assert "Alexandria_v20_all_rows" in pops
    assert "Alexandria_v20_MP_identifier_rows" in pops
    assert "MP_Alex_strict_denominator_MP_labels" in pops
    assert "MP_Alex_strict_denominator_Alex_labels" in pops

    elements = pd.read_csv(MILESTONE / "table_representativeness_element_frequency.csv")
    assert len(elements) > 10
    crystal = pd.read_csv(MILESTONE / "table_representativeness_crystal_system.csv")
    assert crystal["n"].sum() == 287
    ehull = pd.read_csv(MILESTONE / "table_representativeness_ehull_distribution.csv")
    assert {"MP", "Alexandria"}.issubset(set(ehull["source"]))


def test_wbm_alex_probe_has_formal_definition_and_is_case_analysis() -> None:
    definition = pd.read_csv(MILESTONE / "table_wbm_alex_probe_formal_definition.csv")
    assert "selection/matching rule" in set(definition["component"])
    summary = pd.read_csv(MILESTONE / "table_wbm_alex_probe_formal_summary.csv").iloc[0]
    assert int(summary["n_candidate_rows"]) == 701
    assert int(summary["n_exact_structure_match"]) == 270
    assert int(summary["discordant_n"]) == 141
    assert abs(float(summary["discordance_rate"]) - 0.5222222222222223) < 1e-12
    assert summary["claim_scope"] == "formal_case_analysis_not_general_baseline"


def test_uncertainty_threshold_sweep_captures_discordance_with_flag_burden() -> None:
    sweep = pd.read_csv(MILESTONE / "table_uncertainty_threshold_sweep.csv")
    row5 = sweep[sweep["threshold_meV_per_atom"].eq(5)].iloc[0]
    row25 = sweep[sweep["threshold_meV_per_atom"].eq(25)].iloc[0]
    assert int(row5["discordant_captured_n"]) == 31
    assert int(row5["outside_discordant_n"]) == 0
    assert float(row5["flagged_fraction"]) > 0.50
    assert int(row25["discordant_captured_n"]) == 31
    assert int(row25["outside_discordant_n"]) == 0
    assert float(row25["flagged_fraction"]) > float(row5["flagged_fraction"])


def test_uncertainty_filtered_benchmark_metrics_and_ranking_stability_exist() -> None:
    metrics = pd.read_csv(MILESTONE / "table_benchmark_metrics_uncertainty_filtered.csv")
    assert {"ALIGNN-FF", "CHGNet", "MACE-MP"}.issubset(set(metrics["model"]))
    assert {"MP", "Alexandria"}.issubset(set(metrics["label_source"]))
    assert {"none", "0.025"}.issubset(set(metrics["threshold_eV_per_atom"].astype(str)))
    assert {"binary_precision", "binary_recall", "binary_F1", "AUROC_supporting"}.issubset(metrics.columns)

    rank = pd.read_csv(MILESTONE / "table_benchmark_ranking_stability_uncertainty_filtered.csv")
    assert "top_model_changed_vs_unfiltered" in rank.columns
    assert not rank[rank["threshold_eV_per_atom"].astype(str).eq("none")]["top_model_changed_vs_unfiltered"].astype(bool).any()


def test_selection_fraction_curve_and_regression_support_no_amplification() -> None:
    curve = pd.read_csv(MILESTONE / "table_selection_fraction_discordance_curve.csv")
    assert set(curve["selection_fraction"]) == {0.01, 0.05, 0.10, 0.20, 0.50}
    assert set(curve["model"]) == {"ALIGNN-FF", "CHGNet", "MACE-MP"}
    top10 = curve[curve["selection_fraction"].eq(0.10)]
    assert top10["discordance_rate"].max() < 0.30
    assert top10["permutation_p_ge_observed"].min() > 0.10

    logit = pd.read_csv(MILESTONE / "table_logistic_regression_discordance.csv")
    rank = logit[logit["predictor"].eq("rank_percentile")]
    assert rank["standardized_logistic_coef"].abs().max() < 0.25
    perm = pd.read_csv(MILESTONE / "table_model_rank_permutation_tests.csv")
    assert perm["p_abs_ge_observed"].min() > 0.10


def test_scatter_source_and_error_case_tables_exist() -> None:
    scatter = pd.read_csv(MILESTONE / "table_mp_alex_ehull_scatter_source.csv")
    assert len(scatter) == 287
    assert {"both_stable", "both_unstable", "MP_stable_only", "Alex_stable_only"}.issubset(set(scatter["quadrant"]))
    assert {"near_hull_10meV", "near_hull_25meV", "near_hull_50meV"}.issubset(scatter.columns)

    cases = pd.read_csv(MILESTONE / "table_top_discordant_structures_by_delta_ehull.csv")
    assert len(cases) >= 10
    assert cases["abs_delta_ehull"].is_monotonic_decreasing
    assert set(cases["structure_match_rms"]) == {"not_recorded_public_safe_artifact"}


def test_third_source_coverage_closeout_keeps_boundaries() -> None:
    closeout = pd.read_csv(MILESTONE / "table_third_source_coverage_closeout.csv")
    oqmd = closeout[closeout["source"].eq("OQMD public API")].iloc[0]
    assert int(oqmd["strict_matches"]) == 4
    assert oqmd["status"] == "undercovered"
    jarvis = closeout[closeout["source"].eq("JARVIS dft_3d via jarvis-tools")].iloc[0]
    assert jarvis["status"] == "blocked"
    wbm = closeout[closeout["source"].eq("WBM/Matbench")].iloc[0]
    assert wbm["status"] == "case_analysis_only"


def test_selection_conditional_discordance_no_go() -> None:
    top = pd.read_csv(MILESTONE / "table_selection_conditional_top_decile_summary.csv")
    assert set(top["model"]) == {"ALIGNN-FF", "CHGNet", "MACE-MP"}
    assert top["top_decile_discordance"].max() < 0.30
    assert top["top_decile_enrichment"].max() < 2.0

    go = pd.read_csv(MILESTONE / "table_selection_conditional_go_no_go.csv").iloc[0]
    assert go["launch_gate"] == "NO_GO"
    assert int(go["n_models_passing"]) == 0


def test_manifest_exists() -> None:
    assert (MILESTONE / "MANIFEST_SHA256.txt").exists()
    assert (ROOT / "MANIFEST_SHA256.txt").exists()
