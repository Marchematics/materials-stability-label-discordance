from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "evidence_strengthening_v1"


def test_threshold_sensitivity_reproduces_native_anchor() -> None:
    x = pd.read_csv(OUT / "endpoint_sensitivity" / "endpoint_switch_threshold_sensitivity.csv")
    row = x.loc[(x.threshold_meV_per_atom == 0) & (x.endpoint_a == "mp_native") & (x.endpoint_b == "alex_pbe_native")].iloc[0]
    assert int(row.n) == 36_802
    assert int(row.switch_n) == 5_666


def test_cluster_bootstrap_uses_requested_replicates_and_all_schemes() -> None:
    x = pd.read_csv(OUT / "cluster_bootstrap_sensitivity" / "paired_cluster_bootstrap_summary.csv")
    assert set(x.cluster_scheme) == {"chemical_system", "reduced_formula", "prototype_proxy"}
    assert set(x.replicates) == {5_000}
    assert set(x.row_n) == {31_872}
    assert (x.ci_2_5 <= x.ci_97_5).all()


def test_uniform_referee_subset_and_vasp_inputs_are_complete() -> None:
    subset = pd.read_parquet(OUT / "unified_referee_subset_1200" / "unified_referee_subset_1200.parquet")
    jobs = pd.read_csv(OUT / "uniform_vasp_pbeu_1200" / "uniform_vasp_job_manifest.csv")
    assert len(subset) == 1_200
    assert len(jobs) == 1_200
    assert set(jobs.run_state) == {"input_ready"}
    relax_kpoints = (OUT / "uniform_vasp_pbeu_1200" / "jobs" / "USR1200-00001" / "relax" / "KPOINTS").read_text()
    static_kpoints = (OUT / "uniform_vasp_pbeu_1200" / "jobs" / "USR1200-00001" / "static" / "KPOINTS").read_text()
    assert "Gamma" in relax_kpoints and "Gamma" in static_kpoints
    assert relax_kpoints != static_kpoints
    runner = (OUT / "uniform_vasp_pbeu_1200" / "run_relax.sh").read_text()
    assert "export POTCAR_ROOT=" in runner


def test_uniform_vasp_result_collector_records_each_target() -> None:
    results = pd.read_csv(OUT / "uniform_vasp_pbeu_1200" / "uniform_vasp_results.csv")
    assert len(results) == 1_200
    assert set(results.static_state) == {"not_started"}
    assert not results.usable_static_energy.any()


def test_private_paw_inventory_and_stratified_ready_cohort_are_complete() -> None:
    inventory = pd.read_csv(OUT / "private_paw_potential_audit" / "private_paw_pbe_potential_inventory.csv")
    cohort = pd.read_parquet(OUT / "unified_referee_subset_1061_legacy_paw" / "unified_referee_subset_1061_legacy_paw.parquet")
    assert len(inventory) == 77
    assert inventory.selected_titel.str.contains("PAW_PBE").all()
    assert set(inventory.distinct_archive_hash_n) == {1}
    assert len(cohort) == 1_061
    assert cohort.legacy_paw_ready.all()
    assert set(cohort.referee_stratum) == {"phase_pool_sensitive", "persistent", "hidden_common_pool", "source_consistent"}


def test_fixed_subsystem_phase_pool_pilot_has_complete_structures_and_job_inputs() -> None:
    pilot = OUT / "fixed_subsystem_phase_pool_pilot_1274"
    phases = pd.read_parquet(pilot / "fixed_subsystem_phase_pool_manifest.parquet")
    targets = pd.read_parquet(pilot / "fixed_subsystem_phase_pool_target_rows.parquet")
    run = OUT / "uniform_vasp_pbeu_fixed_phase_pool_pilot_1274"
    jobs = pd.read_csv(run / "uniform_vasp_job_manifest.csv")
    hull = pd.read_csv(run / "fixed_subsystem_unified_hull_labels.csv")
    preflight = pd.read_csv(run / "vasp_potcar_preflight_summary.csv")
    assert len(phases) == 1_274 and phases.paw_ready.all()
    assert all((pilot / path).exists() for path in phases.structure_path)
    assert len(targets) == 23
    assert set(targets.referee_stratum) == {"phase_pool_sensitive", "persistent", "hidden_common_pool", "source_consistent"}
    assert len(jobs) == len(phases)
    assert set(hull.hull_status) == {"incomplete"}
    assert set(hull.failure_reason) == {"fixed_phase_pool_calculations_incomplete"}
    assert int(preflight.all_potential_coverage_n.iloc[0]) == 1_274
    assert int(preflight.missing_potential_job_n.iloc[0]) == 0


def test_phase_pool_scope_and_generated_smoke_are_materialized() -> None:
    scope = pd.read_csv(OUT / "full_phase_pool_referee_1200" / "phase_pool_scope_summary.csv")
    assert int(scope.target_chemical_system_n.iloc[0]) == 1_146
    assert int(scope.target_subsystem_n.iloc[0]) == 3_658
    smoke = pd.read_csv(OUT / "generated_candidate_smoke" / "generated_candidate_cohort_summary.csv")
    assert int(smoke.input_structure_n.iloc[0]) == 2
    assert int(smoke.accepted_n.iloc[0]) == 2


def test_full_source_phase_pool_referee_audit_has_explicit_coverage() -> None:
    x = pd.read_csv(OUT / "full_phase_pool_referee_1200" / "referee_full_phase_pool_comparison_summary.csv")
    row = x.iloc[0]
    assert int(row.target_n) == 1_200
    assert int(row.both_source_full_pool_evaluable_n) == 1_145
    assert int(row.mp_full_pool_evaluable_n) == 1_164
    assert int(row.alexandria_full_pool_evaluable_n) == 1_181


def test_source_union_inventory_covers_all_referee_targets() -> None:
    x = pd.read_csv(OUT / "full_phase_pool_referee_1200" / "referee_source_union_inventory_summary.csv")
    row = x.iloc[0]
    assert int(row.referee_target_n) == 1_200
    assert int(row.union_phase_entry_n) == int(row.mp_phase_entry_n) + int(row.alexandria_phase_entry_n)


def test_training_overlap_audit_tracks_all_real_models() -> None:
    x = pd.read_csv(OUT / "model_training_overlap" / "model_training_overlap_audit.csv")
    assert set(x.model) == {"ALIGNN-FF", "CHGNet", "M3GNet", "MACE-MP"}
    assert set(x.M1_row_n) == {31_872}


def test_primary_discovery_outputs_use_fixed_budget_and_paired_5000_bootstrap() -> None:
    topk = pd.read_csv(OUT / "primary_discovery_evidence" / "topk_endpoint_decision_deltas.csv")
    assert set(topk.K) == {100, 300, 500, 1000, 5000, 10000}
    assert topk.stable_candidate_jaccard.between(0, 1).all()
    paired = pd.read_csv(OUT / "primary_discovery_evidence" / "paired_endpoint_differences_cluster_bootstrap_5000.csv")
    assert set(paired.replicates) == {5000}


def test_generated_candidate_vasp_smoke_jobs_are_ready() -> None:
    jobs = pd.read_csv(OUT / "generated_candidate_smoke_vasp_jobs" / "generated_candidate_vasp_job_manifest.csv")
    preflight = pd.read_csv(OUT / "generated_candidate_smoke_vasp_jobs" / "vasp_potcar_preflight_summary.csv")
    assert len(jobs) == 2
    assert set(jobs.job_status) == {"input_ready"}
    assert int(preflight.all_potential_coverage_n.iloc[0]) == 2


def test_generated_candidate_yields_are_limited_to_exact_matches() -> None:
    accounting = pd.read_csv(OUT / "generated_candidate_smoke" / "generated_candidate_cohort_accounting.csv")
    yields = pd.read_csv(OUT / "generated_candidate_smoke" / "generated_candidate_exact_match_label_yields.csv")
    exact_n = int(accounting.loc[accounting.cohort_partition.eq("exact_sourceaware_match"), "n"].iloc[0])
    unmatched_n = int(accounting.loc[accounting.cohort_partition.eq("formula_only_or_unmatched"), "n"].iloc[0])
    assert exact_n == 0 and unmatched_n == 2
    assert set(yields.match_tier) == {"exact_structure"}
    assert set(yields.evaluable_exact_match_n) == {0}


def test_manuscript_evidence_tables_are_regenerated_from_analysis_outputs() -> None:
    p1 = pd.read_csv(OUT / "manuscript_tables" / "table_p1_referee_phase_pool_coverage.csv")
    assert {"source_specific_full_pool_hulls", "source_union_inventory"} <= set(p1.table_section)
    p3 = pd.read_csv(OUT / "manuscript_tables" / "table_p3p6_paired_label_differences_5000.csv")
    assert set(p3.replicates) == {5_000}


def test_slurm_arrays_cover_referee_and_smoke_candidate_jobs() -> None:
    launchers = OUT / "slurm_launchers"
    referee = (launchers / "submit_referee1200_relax.sbatch").read_text()
    smoke = (launchers / "submit_generated-smoke_relax.sbatch").read_text()
    assert "--array=1-1200" in referee
    assert "--array=1-2" in smoke
    assert "#SBATCH --ntasks=14" in referee
    assert "#SBATCH --cpus-per-task=1" in referee
    assert 'srun "$VASP_EXECUTABLE"' in referee
